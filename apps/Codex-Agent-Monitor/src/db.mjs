import { mkdirSync, existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { DatabaseSync } from 'node:sqlite';

const __filename = fileURLToPath(import.meta.url);
const projectRoot = path.resolve(path.dirname(__filename), '..');
const dataDir = path.join(projectRoot, 'data');
const dbPath = path.join(dataDir, 'monitor.db');

function ensureDataDir() {
  if (!existsSync(dataDir)) {
    mkdirSync(dataDir, { recursive: true });
  }
}

export function openDb() {
  ensureDataDir();
  return new DatabaseSync(dbPath);
}

export function initSchema(db) {
  db.exec(`
    PRAGMA foreign_keys = ON;

    CREATE TABLE IF NOT EXISTS hosts (
      id TEXT PRIMARY KEY,
      hostname TEXT NOT NULL,
      environment TEXT NOT NULL,
      platform TEXT NOT NULL,
      owner TEXT NOT NULL,
      last_seen_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS agent_instances (
      id TEXT PRIMARY KEY,
      host_id TEXT NOT NULL,
      provider TEXT NOT NULL,
      agent_family TEXT NOT NULL,
      runtime_type TEXT NOT NULL,
      discovery_level TEXT NOT NULL,
      status TEXT NOT NULL,
      confidence_score REAL NOT NULL,
      user_name TEXT NOT NULL,
      workspace_name TEXT,
      repo_path TEXT,
      current_task TEXT,
      first_seen_at TEXT NOT NULL,
      last_seen_at TEXT NOT NULL,
      FOREIGN KEY (host_id) REFERENCES hosts(id)
    );

    CREATE TABLE IF NOT EXISTS discoveries (
      id TEXT PRIMARY KEY,
      agent_id TEXT NOT NULL,
      source TEXT NOT NULL,
      process_signature TEXT NOT NULL,
      install_signature TEXT,
      confidence_score REAL NOT NULL,
      observed_at TEXT NOT NULL,
      notes TEXT,
      FOREIGN KEY (agent_id) REFERENCES agent_instances(id)
    );

    CREATE TABLE IF NOT EXISTS heartbeats (
      id TEXT PRIMARY KEY,
      agent_id TEXT NOT NULL,
      status TEXT NOT NULL,
      cpu_percent REAL NOT NULL,
      memory_mb REAL NOT NULL,
      tokens_used INTEGER NOT NULL,
      cost_usd REAL NOT NULL,
      recorded_at TEXT NOT NULL,
      FOREIGN KEY (agent_id) REFERENCES agent_instances(id)
    );

    CREATE TABLE IF NOT EXISTS jobs (
      id TEXT PRIMARY KEY,
      agent_id TEXT NOT NULL,
      title TEXT NOT NULL,
      outcome TEXT NOT NULL,
      started_at TEXT NOT NULL,
      ended_at TEXT,
      duration_seconds INTEGER NOT NULL,
      repo_path TEXT,
      model_name TEXT,
      prompt_summary TEXT,
      FOREIGN KEY (agent_id) REFERENCES agent_instances(id)
    );

    CREATE TABLE IF NOT EXISTS workspace_observations (
      id TEXT PRIMARY KEY,
      agent_id TEXT,
      workspace_name TEXT NOT NULL,
      observation_type TEXT NOT NULL,
      correlation_key TEXT NOT NULL,
      observed_at TEXT NOT NULL,
      details TEXT NOT NULL,
      FOREIGN KEY (agent_id) REFERENCES agent_instances(id)
    );

    CREATE TABLE IF NOT EXISTS host_metrics (
      id TEXT PRIMARY KEY,
      host_id TEXT NOT NULL,
      cpu_percent REAL NOT NULL,
      memory_used_mb REAL NOT NULL,
      memory_total_mb REAL NOT NULL,
      disk_used_gb REAL NOT NULL,
      disk_total_gb REAL NOT NULL,
      network_in_kbps REAL NOT NULL,
      network_out_kbps REAL NOT NULL,
      recorded_at TEXT NOT NULL,
      FOREIGN KEY (host_id) REFERENCES hosts(id)
    );

    CREATE TABLE IF NOT EXISTS agent_metrics (
      id TEXT PRIMARY KEY,
      agent_id TEXT NOT NULL,
      cpu_percent REAL NOT NULL,
      memory_mb REAL NOT NULL,
      disk_read_kbps REAL NOT NULL,
      disk_write_kbps REAL NOT NULL,
      uptime_seconds INTEGER NOT NULL,
      restart_count INTEGER NOT NULL,
      recorded_at TEXT NOT NULL,
      FOREIGN KEY (agent_id) REFERENCES agent_instances(id)
    );
  `);
}

export function resetDatabase(db) {
  db.exec(`
    DROP TABLE IF EXISTS agent_metrics;
    DROP TABLE IF EXISTS host_metrics;
    DROP TABLE IF EXISTS workspace_observations;
    DROP TABLE IF EXISTS jobs;
    DROP TABLE IF EXISTS heartbeats;
    DROP TABLE IF EXISTS discoveries;
    DROP TABLE IF EXISTS agent_instances;
    DROP TABLE IF EXISTS hosts;
  `);
}

function toPercent(part, total) {
  if (!total) {
    return 0;
  }
  return Math.round((part / total) * 1000) / 10;
}

function secondsBetween(earlier, later = new Date()) {
  return Math.max(0, Math.round((later.getTime() - new Date(earlier).getTime()) / 1000));
}

function heartbeatStateFromAge(ageSeconds) {
  if (ageSeconds <= 120) return 'healthy';
  if (ageSeconds <= 900) return 'delayed';
  return 'stale';
}

export function getDashboardSnapshot(db) {
  const fleetSummary = db.prepare(`
    SELECT
      COUNT(*) AS total_agents,
      SUM(CASE WHEN discovery_level = 'confirmed' THEN 1 ELSE 0 END) AS confirmed_agents,
      SUM(CASE WHEN discovery_level = 'observed' THEN 1 ELSE 0 END) AS observed_agents,
      SUM(CASE WHEN discovery_level = 'suspected' THEN 1 ELSE 0 END) AS suspected_agents,
      SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) AS running_agents,
      SUM(CASE WHEN status = 'idle' THEN 1 ELSE 0 END) AS idle_agents,
      SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_agents
    FROM agent_instances
  `).get();

  const providerSummary = db.prepare(`
    SELECT provider, COUNT(*) AS count
    FROM agent_instances
    GROUP BY provider
    ORDER BY count DESC, provider ASC
  `).all();

  const activeCost = db.prepare(`
    SELECT ROUND(COALESCE(SUM(cost_usd), 0), 2) AS total_cost
    FROM heartbeats
    WHERE recorded_at >= datetime('now', '-1 day')
  `).get();

  const hostRows = db.prepare(`
    SELECT
      h.id,
      h.hostname,
      h.environment,
      h.platform,
      h.owner,
      h.last_seen_at,
      COUNT(a.id) AS agent_count,
      SUM(CASE WHEN a.status = 'running' THEN 1 ELSE 0 END) AS running_count,
      hm.cpu_percent,
      hm.memory_used_mb,
      hm.memory_total_mb,
      hm.disk_used_gb,
      hm.disk_total_gb,
      hm.network_in_kbps,
      hm.network_out_kbps,
      hm.recorded_at AS metrics_recorded_at
    FROM hosts h
    LEFT JOIN agent_instances a ON a.host_id = h.id
    LEFT JOIN host_metrics hm ON hm.id = (
      SELECT hm2.id FROM host_metrics hm2 WHERE hm2.host_id = h.id ORDER BY hm2.recorded_at DESC LIMIT 1
    )
    GROUP BY h.id
    ORDER BY h.environment, h.hostname
  `).all().map((host) => ({
    ...host,
    memory_percent: toPercent(host.memory_used_mb, host.memory_total_mb),
    disk_percent: toPercent(host.disk_used_gb, host.disk_total_gb)
  }));

  const now = new Date();
  const agents = db.prepare(`
    SELECT
      a.id,
      a.provider,
      a.agent_family,
      a.runtime_type,
      a.discovery_level,
      a.status,
      a.confidence_score,
      a.user_name,
      a.workspace_name,
      a.repo_path,
      a.current_task,
      a.last_seen_at,
      h.hostname,
      h.environment,
      am.cpu_percent AS process_cpu_percent,
      am.memory_mb AS process_memory_mb,
      am.disk_read_kbps,
      am.disk_write_kbps,
      am.uptime_seconds,
      am.restart_count,
      hb.status AS heartbeat_status,
      hb.recorded_at AS heartbeat_recorded_at,
      hb.tokens_used,
      hb.cost_usd
    FROM agent_instances a
    JOIN hosts h ON h.id = a.host_id
    LEFT JOIN agent_metrics am ON am.id = (
      SELECT am2.id FROM agent_metrics am2 WHERE am2.agent_id = a.id ORDER BY am2.recorded_at DESC LIMIT 1
    )
    LEFT JOIN heartbeats hb ON hb.id = (
      SELECT hb2.id FROM heartbeats hb2 WHERE hb2.agent_id = a.id ORDER BY hb2.recorded_at DESC LIMIT 1
    )
    ORDER BY
      CASE a.discovery_level WHEN 'confirmed' THEN 1 WHEN 'observed' THEN 2 ELSE 3 END,
      a.status DESC,
      a.confidence_score DESC
  `).all().map((agent) => {
    const heartbeatAgeSeconds = agent.heartbeat_recorded_at ? secondsBetween(agent.heartbeat_recorded_at, now) : null;
    return {
      ...agent,
      heartbeatAgeSeconds,
      heartbeat_state: heartbeatAgeSeconds === null ? 'stale' : heartbeatStateFromAge(heartbeatAgeSeconds)
    };
  });

  const jobs = db.prepare(`
    SELECT
      j.id,
      j.agent_id,
      j.title,
      j.outcome,
      j.started_at,
      j.ended_at,
      j.duration_seconds,
      j.repo_path,
      j.model_name,
      a.user_name,
      a.provider,
      h.hostname
    FROM jobs j
    JOIN agent_instances a ON a.id = j.agent_id
    JOIN hosts h ON h.id = a.host_id
    ORDER BY j.started_at DESC
    LIMIT 12
  `).all();

  const findings = db.prepare(`
    SELECT
      d.id,
      d.agent_id,
      d.source,
      d.process_signature,
      d.install_signature,
      d.confidence_score,
      d.observed_at,
      d.notes,
      a.provider
    FROM discoveries d
    JOIN agent_instances a ON a.id = d.agent_id
    WHERE a.discovery_level = 'suspected'
    ORDER BY d.confidence_score DESC, d.observed_at DESC
  `).all();

  const resourceSummaryRaw = db.prepare(`
    SELECT
      ROUND(AVG(cpu_percent), 1) AS avg_host_cpu,
      ROUND(MAX(cpu_percent), 1) AS peak_host_cpu,
      ROUND(AVG((memory_used_mb / memory_total_mb) * 100), 1) AS avg_memory_percent,
      ROUND(MAX((disk_used_gb / disk_total_gb) * 100), 1) AS peak_disk_percent,
      ROUND(SUM(network_in_kbps + network_out_kbps), 1) AS total_network_kbps
    FROM host_metrics
    WHERE recorded_at >= datetime('now', '-1 day')
  `).get();

  const heartbeatSummary = agents.reduce((acc, agent) => {
    acc.total += 1;
    acc[agent.heartbeat_state] += 1;
    return acc;
  }, { total: 0, healthy: 0, delayed: 0, stale: 0 });

  const hotHosts = [...hostRows]
    .sort((a, b) => (b.cpu_percent + b.memory_percent + b.disk_percent) - (a.cpu_percent + a.memory_percent + a.disk_percent))
    .slice(0, 3);

  const resourceSummary = {
    avg_host_cpu: resourceSummaryRaw.avg_host_cpu ?? 0,
    peak_host_cpu: resourceSummaryRaw.peak_host_cpu ?? 0,
    avg_memory_percent: resourceSummaryRaw.avg_memory_percent ?? 0,
    peak_disk_percent: resourceSummaryRaw.peak_disk_percent ?? 0,
    total_network_kbps: resourceSummaryRaw.total_network_kbps ?? 0,
    hot_host_count: hotHosts.length
  };

  return {
    generatedAt: new Date().toISOString(),
    fleetSummary: {
      ...fleetSummary,
      total_cost: activeCost.total_cost
    },
    providerSummary,
    heartbeatSummary,
    resourceSummary,
    hosts: hostRows,
    hotHosts,
    agents,
    jobs,
    findings
  };
}

export function getSampleRows(db) {
  return {
    hosts: db.prepare(`SELECT * FROM hosts ORDER BY id`).all(),
    agent_instances: db.prepare(`SELECT * FROM agent_instances ORDER BY id`).all(),
    discoveries: db.prepare(`SELECT * FROM discoveries ORDER BY id`).all(),
    heartbeats: db.prepare(`SELECT * FROM heartbeats ORDER BY id`).all(),
    jobs: db.prepare(`SELECT * FROM jobs ORDER BY id`).all(),
    workspace_observations: db.prepare(`SELECT * FROM workspace_observations ORDER BY id`).all(),
    host_metrics: db.prepare(`SELECT * FROM host_metrics ORDER BY id`).all(),
    agent_metrics: db.prepare(`SELECT * FROM agent_metrics ORDER BY id`).all()
  };
}
