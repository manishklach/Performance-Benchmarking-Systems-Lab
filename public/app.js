function formatTimestamp(value) {
  return new Date(value).toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short'
  });
}

function toPercent(value, total) {
  if (!total) return 0;
  return Math.round((value / total) * 100);
}

function currency(value) {
  return `$${Number(value).toFixed(2)}`;
}

function whole(value) {
  return Math.round(Number(value || 0));
}

function formatAge(seconds) {
  if (seconds == null) return 'No heartbeat';
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  return `${hours}h ago`;
}

function badge(label, tone) {
  return `<span class="badge tone-${tone}">${label}</span>`;
}

function levelTone(level) {
  if (level === 'confirmed') return 'good';
  if (level === 'observed') return 'warn';
  return 'danger';
}

function statusTone(status) {
  if (status === 'running' || status === 'completed') return 'good';
  if (status === 'idle') return 'neutral';
  return 'danger';
}

function heartbeatTone(state) {
  if (state === 'healthy') return 'good';
  if (state === 'delayed') return 'warn';
  return 'danger';
}

function metricCard(label, value, detail, tone, sparkle) {
  return `
    <article class="metric-card tone-${tone}">
      <div class="metric-top">
        <span>${label}</span>
        <i>${sparkle}</i>
      </div>
      <strong>${value}</strong>
      <p>${detail}</p>
    </article>
  `;
}

function meter(label, value, suffix, toneClass) {
  const numeric = Math.max(0, Math.min(100, Number(value || 0)));
  return `
    <div class="resource-meter ${toneClass}">
      <div class="resource-head">
        <span>${label}</span>
        <strong>${whole(numeric)}${suffix}</strong>
      </div>
      <div class="resource-track"><span style="width:${numeric}%"></span></div>
    </div>
  `;
}

function buildRing(summary) {
  const trustworthy = summary.confirmed_agents + summary.observed_agents;
  const trustPercent = toPercent(trustworthy, summary.total_agents);
  const angle = Math.max(12, Math.round((trustPercent / 100) * 360));
  const ring = document.getElementById('fleetRing');
  ring.style.setProperty('--angle', `${angle}deg`);
  document.getElementById('ringTotal').textContent = summary.total_agents;
  document.getElementById('ringCaption').textContent = `${trustPercent}% of agents are confirmed or observed.`;
}

function renderSignals(summary, resources, heartbeatSummary) {
  const signals = [
    ['Running now', summary.running_agents, 'good'],
    ['Healthy heartbeats', heartbeatSummary.healthy, 'good'],
    ['Needs review', summary.suspected_agents, 'danger'],
    ['Peak host CPU', `${whole(resources.peak_host_cpu)}%`, 'warn']
  ];

  document.getElementById('signalBoard').innerHTML = signals.map(([label, value, tone]) => `
    <div class="signal-card tone-${tone}">
      <span>${label}</span>
      <strong>${value}</strong>
    </div>
  `).join('');
}

function renderMix(summary) {
  const total = summary.total_agents;
  const segments = [
    { label: 'Confirmed', value: summary.confirmed_agents, className: 'seg-confirmed' },
    { label: 'Observed', value: summary.observed_agents, className: 'seg-observed' },
    { label: 'Suspected', value: summary.suspected_agents, className: 'seg-suspected' }
  ];

  document.getElementById('stackChart').innerHTML = segments.map((segment) => {
    const width = Math.max(8, toPercent(segment.value, total));
    return `<div class="stack-segment ${segment.className}" style="width:${width}%"></div>`;
  }).join('');

  document.getElementById('mixLegend').innerHTML = segments.map((segment) => `
    <div class="legend-item">
      <span class="legend-dot ${segment.className}"></span>
      <div>
        <strong>${segment.value}</strong>
        <p>${segment.label}</p>
      </div>
    </div>
  `).join('');
}

function renderStats(summary, resources, heartbeatSummary) {
  const cards = [
    metricCard('Confirmed agents', summary.confirmed_agents, 'Known Codex signatures and launcher evidence.', 'good', '●'),
    metricCard('24h spend', currency(summary.total_cost), 'Recent token and runtime cost across the fleet.', 'warn', '$'),
    metricCard('Stale heartbeats', heartbeatSummary.stale, 'Agents that have not checked in within the stale window.', 'danger', '♥'),
    metricCard('Network flow', `${whole(resources.total_network_kbps)} kbps`, 'Aggregate inbound and outbound host throughput.', 'neutral', '↗')
  ];
  document.getElementById('stats').innerHTML = cards.join('');
}

function renderResourceSummary(resources) {
  document.getElementById('resourceSummary').innerHTML = [
    meter('Average host CPU', resources.avg_host_cpu, '%', 'cpu'),
    meter('Average memory', resources.avg_memory_percent, '%', 'memory'),
    meter('Peak disk usage', resources.peak_disk_percent, '%', 'disk'),
    `
      <article class="network-card">
        <span>Total network throughput</span>
        <strong>${whole(resources.total_network_kbps)} kbps</strong>
        <p>${resources.hot_host_count} hosts currently in the pressure review set.</p>
      </article>
    `
  ].join('');
}

function renderHeartbeatSummary(heartbeatSummary) {
  const total = heartbeatSummary.total || 1;
  document.getElementById('heartbeatSummary').innerHTML = `
    <div class="heartbeat-ring" style="--healthy:${toPercent(heartbeatSummary.healthy, total)}; --delayed:${toPercent(heartbeatSummary.delayed, total)}; --stale:${toPercent(heartbeatSummary.stale, total)};">
      <span>${heartbeatSummary.total}</span>
    </div>
    <div class="heartbeat-legend">
      <div>${badge('healthy', 'good')}<strong>${heartbeatSummary.healthy}</strong></div>
      <div>${badge('delayed', 'warn')}<strong>${heartbeatSummary.delayed}</strong></div>
      <div>${badge('stale', 'danger')}<strong>${heartbeatSummary.stale}</strong></div>
    </div>
  `;
}

function renderAgents(agents) {
  document.getElementById('agentsGrid').innerHTML = agents.map((agent) => {
    const confidence = Math.round(agent.confidence_score * 100);
    return `
      <article class="agent-card ${agent.discovery_level}">
        <div class="agent-top">
          <div>
            <p class="micro">${agent.codex_type}</p>
            <h3>${agent.id}</h3>
          </div>
          ${badge(agent.status, statusTone(agent.status))}
        </div>
        <div class="agent-badges">
          ${badge(agent.discovery_level, levelTone(agent.discovery_level))}
          ${badge(agent.environment, 'neutral')}
          ${badge(agent.heartbeat_state, heartbeatTone(agent.heartbeat_state))}
        </div>
        <p class="agent-task">${agent.current_task || 'No active task'}</p>
        <div class="heartbeat-inline">
          <span>Last heartbeat</span>
          <strong>${formatAge(agent.heartbeatAgeSeconds)}</strong>
          <em>${agent.heartbeat_recorded_at ? formatTimestamp(agent.heartbeat_recorded_at) : 'No signal'}</em>
        </div>
        <div class="confidence-block">
          <div class="confidence-meta">
            <span>Confidence</span>
            <strong>${confidence}%</strong>
          </div>
          <div class="confidence-bar"><span style="width:${confidence}%"></span></div>
        </div>
        <div class="agent-resources">
          ${meter('CPU', agent.process_cpu_percent || 0, '%', 'cpu')}
          ${meter('Memory', Math.min(100, (agent.process_memory_mb || 0) / 10), '%', 'memory')}
          <div class="mini-io">
            <span>Disk I/O</span>
            <strong>${whole(agent.disk_read_kbps)}r / ${whole(agent.disk_write_kbps)}w kbps</strong>
          </div>
        </div>
        <dl class="agent-meta">
          <div><dt>Host</dt><dd>${agent.hostname}</dd></div>
          <div><dt>User</dt><dd>${agent.user_name}</dd></div>
          <div><dt>Uptime</dt><dd>${whole(agent.uptime_seconds / 60)} min</dd></div>
          <div><dt>Restarts</dt><dd>${agent.restart_count}</dd></div>
        </dl>
      </article>
    `;
  }).join('');
}

function renderHosts(hosts) {
  document.getElementById('hostCards').innerHTML = hosts.map((host) => {
    const utilization = host.agent_count ? Math.round((host.running_count / host.agent_count) * 100) : 0;
    return `
      <article class="host-card ${host.environment}">
        <div class="host-head">
          <div>
            <h3>${host.hostname}</h3>
            <p>${host.platform}</p>
          </div>
          ${badge(host.environment, 'neutral')}
        </div>
        <div class="host-inline-stats">
          <div><strong>${host.agent_count}</strong><span>agents</span></div>
          <div><strong>${host.running_count}</strong><span>running</span></div>
        </div>
        <div class="mini-meter"><span style="width:${utilization}%"></span></div>
        <div class="host-resource-grid">
          ${meter('CPU', host.cpu_percent, '%', 'cpu')}
          ${meter('Memory', host.memory_percent, '%', 'memory')}
          ${meter('Disk', host.disk_percent, '%', 'disk')}
        </div>
        <p class="muted">Network ${whole(host.network_in_kbps)} in / ${whole(host.network_out_kbps)} out kbps</p>
        <p class="muted">Last seen ${formatTimestamp(host.last_seen_at)}</p>
      </article>
    `;
  }).join('');
}

function renderJobs(jobs) {
  document.getElementById('jobsList').innerHTML = jobs.map((job) => `
    <article class="job-card ${job.outcome}">
      <div class="job-line"></div>
      <div class="job-body">
        <div class="job-head">
          <div>
            <h3>${job.title}</h3>
            <p>${job.hostname} · ${job.user_name}</p>
          </div>
          ${badge(job.outcome, statusTone(job.outcome))}
        </div>
        <div class="job-meta-row">
          <span>${job.model_name}</span>
          <span>${job.duration_seconds}s</span>
          <span>${formatTimestamp(job.started_at)}</span>
        </div>
      </div>
    </article>
  `).join('');
}

function renderFindings(findings) {
  document.getElementById('findingsList').innerHTML = findings.map((finding) => `
    <article class="finding-card">
      <div class="finding-head">
        <h3>${finding.agent_id}</h3>
        ${badge(`${Math.round(finding.confidence_score * 100)}%`, 'danger')}
      </div>
      <p>${finding.source}</p>
      <p class="muted">${finding.process_signature}</p>
      <p class="muted">${finding.notes || 'No notes'}</p>
    </article>
  `).join('') || '<p class="muted">No suspected findings.</p>';
}

async function loadDashboard() {
  const response = await fetch('/api/dashboard');
  const data = await response.json();

  document.getElementById('generatedAt').textContent = formatTimestamp(data.generatedAt);
  buildRing(data.fleetSummary);
  renderSignals(data.fleetSummary, data.resourceSummary, data.heartbeatSummary);
  renderMix(data.fleetSummary);
  renderStats(data.fleetSummary, data.resourceSummary, data.heartbeatSummary);
  renderResourceSummary(data.resourceSummary);
  renderHeartbeatSummary(data.heartbeatSummary);
  renderAgents(data.agents);
  renderHosts(data.hosts);
  renderJobs(data.jobs);
  renderFindings(data.findings);
}

loadDashboard().catch((error) => {
  document.body.innerHTML = `<main class="shell"><section class="panel-surface"><h1>Dashboard failed to load</h1><p>${error.message}</p></section></main>`;
});
