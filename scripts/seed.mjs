import { initSchema, openDb, resetDatabase } from '../src/db.mjs';

const db = openDb();
resetDatabase(db);
initSchema(db);

const hosts = [
  ['host-laptop-01', 'design-laptop-01', 'endpoint', 'windows-11', 'manish', '2026-03-09T17:58:00Z'],
  ['host-server-01', 'build-server-01', 'server', 'ubuntu-24.04', 'platform-team', '2026-03-09T17:59:00Z'],
  ['host-k8s-01', 'k8s-node-a', 'cloud', 'kubernetes', 'sre', '2026-03-09T17:57:00Z']
];

const agents = [
  ['agent-cli-01', 'host-laptop-01', 'cli', 'confirmed', 'running', 0.98, 'manish', 'codex-enterprise', 'C:\\Users\\ManishKL\\Downloads\\Codex-Agent-Monitor', 'Generate dashboard and seed data', '2026-03-09T17:20:00Z', '2026-03-09T17:58:00Z'],
  ['agent-app-02', 'host-server-01', 'app', 'observed', 'idle', 0.82, 'ops-bot', 'codex-enterprise', '/srv/codex-worker', 'Awaiting queued review task', '2026-03-09T16:00:00Z', '2026-03-09T17:55:00Z'],
  ['agent-sdk-03', 'host-k8s-01', 'sdk', 'suspected', 'running', 0.63, 'deploy-bot', 'codex-enterprise', '/workspace/triage-agent', 'Correlate workspace events with pod scan', '2026-03-09T17:10:00Z', '2026-03-09T17:57:00Z'],
  ['agent-cli-04', 'host-server-01', 'cli', 'suspected', 'failed', 0.57, 'release-bot', 'codex-enterprise', '/srv/release-agent', 'Retry after missing heartbeat', '2026-03-09T15:45:00Z', '2026-03-09T17:12:00Z']
];

const discoveries = [
  ['disc-01', 'agent-cli-01', 'endpoint-collector', 'codex exec --profile enterprise', 'OpenAI Codex CLI 1.3.2', 0.98, '2026-03-09T17:58:00Z', 'Known binary and active workspace session'],
  ['disc-02', 'agent-app-02', 'workspace-observation', 'codex app session correlation', 'Workspace admin analytics', 0.82, '2026-03-09T17:55:00Z', 'Observed through workspace telemetry without local install proof'],
  ['disc-03', 'agent-sdk-03', 'k8s-scanner', 'node dist/worker.js --agent codex-triage', 'container label app=codex-triage', 0.63, '2026-03-09T17:57:00Z', 'Pod label matched but launcher wrapper not enforced'],
  ['disc-04', 'agent-cli-04', 'server-scan', 'node node_modules/@openai/codex/bin.js exec', null, 0.57, '2026-03-09T17:12:00Z', 'Process signature matched but no workspace event correlation yet']
];

const heartbeats = [
  ['hb-01', 'agent-cli-01', 'running', 18.4, 612, 18240, 7.23, '2026-03-09T17:58:00Z'],
  ['hb-02', 'agent-app-02', 'idle', 3.2, 420, 8240, 2.11, '2026-03-09T17:55:00Z'],
  ['hb-03', 'agent-sdk-03', 'running', 26.9, 734, 21450, 8.44, '2026-03-09T17:57:00Z'],
  ['hb-04', 'agent-cli-04', 'failed', 0.4, 0, 13320, 5.02, '2026-03-09T17:12:00Z']
];

const jobs = [
  ['job-01', 'agent-cli-01', 'Build Codex fleet monitor MVP', 'completed', '2026-03-09T17:20:00Z', '2026-03-09T17:51:00Z', 1860, 'C:\\Users\\ManishKL\\Downloads\\Codex-Agent-Monitor', 'gpt-5-codex', 'Create a monitor with dashboard, sample DB, and tests'],
  ['job-02', 'agent-sdk-03', 'Correlate endpoint and workspace signals', 'running', '2026-03-09T17:32:00Z', null, 1500, '/workspace/triage-agent', 'gpt-5-codex', 'Promote suspected agents when signals match'],
  ['job-03', 'agent-app-02', 'Review stale heartbeats', 'completed', '2026-03-09T16:42:00Z', '2026-03-09T16:57:00Z', 900, '/srv/codex-worker', 'gpt-5-mini', 'Find stale agents and queue alerts'],
  ['job-04', 'agent-cli-04', 'Release notes verification', 'failed', '2026-03-09T16:05:00Z', '2026-03-09T16:23:00Z', 1080, '/srv/release-agent', 'gpt-5-codex', 'Retry failed release draft after workspace timeout']
];

const observations = [
  ['obs-01', 'agent-app-02', 'codex-enterprise', 'workspace-session', 'session:ops-bot:1755', '2026-03-09T17:55:00Z', '{"source":"workspace-admin","event":"session_seen"}'],
  ['obs-02', 'agent-sdk-03', 'codex-enterprise', 'compliance-log', 'pod:k8s-node-a:1757', '2026-03-09T17:57:00Z', '{"source":"compliance-api","event":"job_started"}'],
  ['obs-03', null, 'codex-enterprise', 'workspace-session', 'session:unknown:1748', '2026-03-09T17:48:00Z', '{"source":"workspace-admin","event":"uncorrelated_session"}']
];

const hostMetrics = [
  ['hm-01', 'host-laptop-01', 42.1, 11240, 16384, 312, 512, 820, 260, '2026-03-09T17:58:00Z'],
  ['hm-02', 'host-server-01', 67.4, 24576, 32768, 740, 1024, 1840, 960, '2026-03-09T17:59:00Z'],
  ['hm-03', 'host-k8s-01', 58.7, 13720, 24576, 188, 400, 1260, 1120, '2026-03-09T17:57:00Z']
];

const agentMetrics = [
  ['am-01', 'agent-cli-01', 18.4, 612, 90, 46, 2280, 0, '2026-03-09T17:58:00Z'],
  ['am-02', 'agent-app-02', 6.2, 420, 24, 18, 6900, 1, '2026-03-09T17:55:00Z'],
  ['am-03', 'agent-sdk-03', 26.9, 734, 140, 112, 2820, 0, '2026-03-09T17:57:00Z'],
  ['am-04', 'agent-cli-04', 2.1, 188, 8, 5, 1020, 3, '2026-03-09T17:12:00Z']
];

const insertMany = (sql, rows) => {
  const statement = db.prepare(sql);
  db.exec('BEGIN');
  try {
    for (const row of rows) {
      statement.run(...row);
    }
    db.exec('COMMIT');
  } catch (error) {
    db.exec('ROLLBACK');
    throw error;
  }
};

insertMany('INSERT INTO hosts (id, hostname, environment, platform, owner, last_seen_at) VALUES (?, ?, ?, ?, ?, ?)', hosts);
insertMany(`INSERT INTO agent_instances (id, host_id, codex_type, discovery_level, status, confidence_score, user_name, workspace_name, repo_path, current_task, first_seen_at, last_seen_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`, agents);
insertMany(`INSERT INTO discoveries (id, agent_id, source, process_signature, install_signature, confidence_score, observed_at, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)`, discoveries);
insertMany(`INSERT INTO heartbeats (id, agent_id, status, cpu_percent, memory_mb, tokens_used, cost_usd, recorded_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)`, heartbeats);
insertMany(`INSERT INTO jobs (id, agent_id, title, outcome, started_at, ended_at, duration_seconds, repo_path, model_name, prompt_summary) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`, jobs);
insertMany(`INSERT INTO workspace_observations (id, agent_id, workspace_name, observation_type, correlation_key, observed_at, details) VALUES (?, ?, ?, ?, ?, ?, ?)`, observations);
insertMany(`INSERT INTO host_metrics (id, host_id, cpu_percent, memory_used_mb, memory_total_mb, disk_used_gb, disk_total_gb, network_in_kbps, network_out_kbps, recorded_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`, hostMetrics);
insertMany(`INSERT INTO agent_metrics (id, agent_id, cpu_percent, memory_mb, disk_read_kbps, disk_write_kbps, uptime_seconds, restart_count, recorded_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`, agentMetrics);

console.log(`Seeded ${hosts.length} hosts, ${agents.length} agents, ${hostMetrics.length} host metrics, and ${agentMetrics.length} agent metrics into data/monitor.db`);
