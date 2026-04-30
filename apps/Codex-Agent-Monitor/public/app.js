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

function whole(value) {
  return Math.round(Number(value || 0));
}

function currency(value) {
  return `$${Number(value).toFixed(2)}`;
}

function formatAge(seconds) {
  if (seconds == null) return 'No heartbeat';
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  return `${Math.round(minutes / 60)}h ago`;
}

function badge(label, tone) {
  return `<span class="badge tone-${tone}">${label}</span>`;
}

function providerTone(provider) {
  if (provider === 'openai') return 'neutral';
  if (provider === 'anthropic') return 'warn';
  if (provider === 'google') return 'good';
  return 'danger';
}

function toneForDiscovery(level) {
  if (level === 'confirmed') return 'good';
  if (level === 'observed') return 'warn';
  return 'danger';
}

function toneForHeartbeat(level) {
  if (level === 'healthy') return 'good';
  if (level === 'delayed') return 'warn';
  return 'danger';
}

function toneForStatus(status) {
  if (status === 'running' || status === 'completed') return 'good';
  if (status === 'idle') return 'neutral';
  return 'danger';
}

function metricCard(label, value, detail, tone) {
  return `
    <article class="metric tone-${tone}">
      <span>${label}</span>
      <strong>${value}</strong>
      <p>${detail}</p>
    </article>
  `;
}

const dashboardState = {
  data: null,
  filters: {
    provider: 'all',
    status: 'all',
    environment: 'all'
  }
};

function progressRail(label, value, suffix, toneClass) {
  const numeric = Math.max(0, Math.min(100, Number(value || 0)));
  return `
    <article class="rail-card ${toneClass}">
      <div class="rail-head">
        <span>${label}</span>
        <strong>${whole(numeric)}${suffix}</strong>
      </div>
      <div class="rail-track"><span style="width:${numeric}%"></span></div>
    </article>
  `;
}

function buildRing(summary) {
  const trustworthy = summary.confirmed_agents + summary.observed_agents;
  const trustPercent = toPercent(trustworthy, summary.total_agents);
  const ring = document.getElementById('fleetRing');
  ring.style.setProperty('--angle', `${Math.max(14, Math.round((trustPercent / 100) * 360))}deg`);
  document.getElementById('ringTotal').textContent = summary.total_agents;
  document.getElementById('ringCaption').textContent = `${trustPercent}% of the fleet is confirmed or observed.`;
  document.getElementById('trustPercent').textContent = `${trustPercent}% trusted`;
}

function renderTopPills(summary, heartbeatSummary, providerSummary) {
  const pills = [
    badge(`${summary.running_agents} running`, 'good'),
    badge(`${heartbeatSummary.stale} stale`, 'danger'),
    badge(`${providerSummary.length} providers`, 'neutral')
  ];
  document.getElementById('topPills').innerHTML = pills.join('');
  document.getElementById('providerCount').textContent = `${providerSummary.length} providers live`;
}

function renderProviderMix(providerSummary) {
  document.getElementById('providerTotal').textContent = `${providerSummary.reduce((sum, item) => sum + item.count, 0)} agents`;
  document.getElementById('providerGrid').innerHTML = providerSummary.map((item) => `
    <article class="provider-card tone-${providerTone(item.provider)}">
      <span>${item.provider}</span>
      <strong>${item.count}</strong>
    </article>
  `).join('');
}

function renderMix(summary) {
  const total = summary.total_agents;
  const segments = [
    { label: 'Confirmed', value: summary.confirmed_agents, className: 'confirmed' },
    { label: 'Observed', value: summary.observed_agents, className: 'observed' },
    { label: 'Suspected', value: summary.suspected_agents, className: 'suspected' }
  ];

  document.getElementById('stackChart').innerHTML = segments.map((segment) => {
    const width = Math.max(8, toPercent(segment.value, total));
    return `<div class="stack-segment ${segment.className}" style="width:${width}%"></div>`;
  }).join('');

  document.getElementById('mixLegend').innerHTML = segments.map((segment) => `
    <div class="legend-row">
      <div class="legend-left">
        <span class="legend-dot ${segment.className}"></span>
        <span>${segment.label}</span>
      </div>
      <strong>${segment.value}</strong>
    </div>
  `).join('');
}

function renderSignals(summary, resources, heartbeatSummary) {
  const signals = [
    ['Healthy heartbeats', heartbeatSummary.healthy, 'good'],
    ['Peak host CPU', `${whole(resources.peak_host_cpu)}%`, 'warn'],
    ['Peak disk', `${whole(resources.peak_disk_percent)}%`, 'warn'],
    ['24h spend', currency(summary.total_cost), 'neutral'],
    ['Delayed heartbeats', heartbeatSummary.delayed, 'warn'],
    ['Stale heartbeats', heartbeatSummary.stale, 'danger']
  ];

  document.getElementById('signalBoard').innerHTML = signals.map(([label, value, tone]) => `
    <article class="signal-card tone-${tone}">
      <span>${label}</span>
      <strong>${value}</strong>
    </article>
  `).join('');
}

function renderMetrics(summary, resources, heartbeatSummary, providerSummary) {
  const largestProvider = providerSummary[0] || { provider: 'n/a', count: 0 };
  const cards = [
    metricCard('Confirmed agents', summary.confirmed_agents, 'Verified evidence on-host or via managed launcher flow.', 'good'),
    metricCard('Resource pressure', `${whole(resources.avg_host_cpu)}%`, 'Average fleet CPU with memory and disk pressure tracked below.', 'neutral'),
    metricCard('Largest provider', `${largestProvider.provider}`, `${largestProvider.count} monitored agents in the current sample.`, providerTone(largestProvider.provider)),
    metricCard('Heartbeat risk', heartbeatSummary.stale, 'Agents outside the stale threshold and needing operator attention.', 'danger')
  ];
  document.getElementById('stats').innerHTML = cards.join('');
}

function populateSelect(id, values, allLabel) {
  const select = document.getElementById(id);
  const current = select.value || 'all';
  select.innerHTML = [
    `<option value="all">${allLabel}</option>`,
    ...values.map((value) => `<option value="${value}">${value}</option>`)
  ].join('');
  select.value = values.includes(current) ? current : 'all';
}

function syncFilterOptions(agents) {
  populateSelect('providerFilter', [...new Set(agents.map((agent) => agent.provider))].sort(), 'All providers');
  populateSelect('statusFilter', [...new Set(agents.map((agent) => agent.status))].sort(), 'All statuses');
  populateSelect('environmentFilter', [...new Set(agents.map((agent) => agent.environment))].sort(), 'All environments');
}

function getFilteredAgents(agents) {
  return agents.filter((agent) => {
    if (dashboardState.filters.provider !== 'all' && agent.provider !== dashboardState.filters.provider) return false;
    if (dashboardState.filters.status !== 'all' && agent.status !== dashboardState.filters.status) return false;
    if (dashboardState.filters.environment !== 'all' && agent.environment !== dashboardState.filters.environment) return false;
    return true;
  });
}

function renderFilterSummary(total, visible) {
  const activeFilters = Object.entries(dashboardState.filters)
    .filter(([, value]) => value !== 'all')
    .map(([key, value]) => `${key}: ${value}`);

  const detail = activeFilters.length ? activeFilters.join(' | ') : 'all agents';
  document.getElementById('filterSummary').textContent = `Showing ${visible} of ${total} agents | ${detail}`;
}

function renderRadar(heartbeatSummary) {
  const total = heartbeatSummary.total || 1;
  const healthy = toPercent(heartbeatSummary.healthy, total);
  const delayed = toPercent(heartbeatSummary.delayed, total);
  const stale = 100 - healthy - delayed;

  document.getElementById('heartbeatRadar').innerHTML = `
    <div class="heartbeat-orbit" style="--healthy:${healthy}; --delayed:${delayed}; --stale:${stale};">
      <div class="heartbeat-core">
        <strong>${heartbeatSummary.total}</strong>
        <span>agents</span>
      </div>
    </div>
    <div class="orbit-legend">
      <div>${badge('healthy', 'good')}<strong>${heartbeatSummary.healthy}</strong></div>
      <div>${badge('delayed', 'warn')}<strong>${heartbeatSummary.delayed}</strong></div>
      <div>${badge('stale', 'danger')}<strong>${heartbeatSummary.stale}</strong></div>
    </div>
  `;
}

function renderResourceSummary(resources) {
  document.getElementById('resourceSummary').innerHTML = [
    progressRail('Average CPU', resources.avg_host_cpu, '%', 'cpu'),
    progressRail('Average memory', resources.avg_memory_percent, '%', 'memory'),
    progressRail('Peak disk', resources.peak_disk_percent, '%', 'disk'),
    `
      <article class="network-spotlight">
        <span>Hot host set</span>
        <strong>${resources.hot_host_count}</strong>
        <p>${whole(resources.total_network_kbps)} kbps of total observed network throughput.</p>
      </article>
    `
  ].join('');
}

function renderAgents(agents) {
  if (!agents.length) {
    document.getElementById('agentsGrid').innerHTML = '<p class="empty">No agents match the active filters.</p>';
    return;
  }

  document.getElementById('agentsGrid').innerHTML = agents.map((agent) => {
    const confidence = Math.round(agent.confidence_score * 100);
    const memoryPercent = Math.min(100, (agent.process_memory_mb || 0) / 10);
    return `
      <article class="agent-card ${agent.discovery_level}">
        <div class="agent-top">
          <div>
            <p class="micro">${agent.agent_family}</p>
            <h3>${agent.id}</h3>
          </div>
          ${badge(agent.status, toneForStatus(agent.status))}
        </div>

        <div class="agent-ribbon">
          ${badge(agent.provider, providerTone(agent.provider))}
          ${badge(agent.discovery_level, toneForDiscovery(agent.discovery_level))}
          ${badge(agent.heartbeat_state, toneForHeartbeat(agent.heartbeat_state))}
          ${badge(agent.environment, 'neutral')}
        </div>

        <p class="agent-task">${agent.current_task || 'No active task'}</p>

        <div class="heartbeat-chip ${agent.heartbeat_state}">
          <span>Last heartbeat</span>
          <strong>${formatAge(agent.heartbeatAgeSeconds)}</strong>
          <em>${agent.heartbeat_recorded_at ? formatTimestamp(agent.heartbeat_recorded_at) : 'No heartbeat recorded'}</em>
        </div>

        <div class="micro-grid">
          ${progressRail('Confidence', confidence, '%', 'confidence')}
          ${progressRail('CPU', agent.process_cpu_percent || 0, '%', 'cpu')}
          ${progressRail('Memory', memoryPercent, '%', 'memory')}
          <article class="io-card">
            <span>Disk I/O</span>
            <strong>${whole(agent.disk_read_kbps)}r / ${whole(agent.disk_write_kbps)}w</strong>
            <p>kbps</p>
          </article>
        </div>

        <dl class="agent-meta">
          <div><dt>Host</dt><dd>${agent.hostname}</dd></div>
          <div><dt>User</dt><dd>${agent.user_name}</dd></div>
          <div><dt>Runtime</dt><dd>${agent.runtime_type}</dd></div>
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
      <article class="host-card">
        <div class="host-top">
          <div>
            <h3>${host.hostname}</h3>
            <p>${host.environment} · ${host.platform}</p>
          </div>
          ${badge(`${host.running_count}/${host.agent_count} running`, 'neutral')}
        </div>
        <div class="host-progress">
          ${progressRail('Fleet utilization', utilization, '%', 'confidence')}
          ${progressRail('CPU', host.cpu_percent, '%', 'cpu')}
          ${progressRail('Memory', host.memory_percent, '%', 'memory')}
          ${progressRail('Disk', host.disk_percent, '%', 'disk')}
        </div>
        <p class="host-foot">Net ${whole(host.network_in_kbps)} in / ${whole(host.network_out_kbps)} out kbps</p>
      </article>
    `;
  }).join('');
}

function renderFindings(findings) {
  document.getElementById('findingsList').innerHTML = findings.map((finding) => `
    <article class="finding-card">
      <div class="finding-top">
        <div>
          <h3>${finding.agent_id}</h3>
          <p>${finding.provider}</p>
        </div>
        ${badge(`${Math.round(finding.confidence_score * 100)}%`, 'danger')}
      </div>
      <span>${finding.source}</span>
      <small>${finding.process_signature}</small>
    </article>
  `).join('') || '<p class="empty">No suspected findings.</p>';
}

function renderJobs(jobs) {
  document.getElementById('jobsList').innerHTML = jobs.map((job) => `
    <article class="job-card">
      <div class="job-line"></div>
      <div class="job-body">
        <div class="job-top">
          <div>
            <h3>${job.title}</h3>
            <p>${job.provider} · ${job.hostname} · ${job.user_name}</p>
          </div>
          ${badge(job.outcome, toneForStatus(job.outcome))}
        </div>
        <div class="job-meta">
          <span>${job.model_name}</span>
          <span>${job.duration_seconds}s</span>
          <span>${formatTimestamp(job.started_at)}</span>
        </div>
      </div>
    </article>
  `).join('');
}

function renderHotHosts(hosts) {
  document.getElementById('hotHosts').innerHTML = hosts.map((host, index) => `
    <article class="hot-host-card">
      <div class="hot-rank">${index + 1}</div>
      <div class="hot-main">
        <div class="hot-top">
          <h3>${host.hostname}</h3>
          ${badge(`${whole(host.cpu_percent)}% CPU`, host.cpu_percent >= 65 ? 'danger' : 'warn')}
        </div>
        <div class="hot-bars">
          ${progressRail('Memory', host.memory_percent, '%', 'memory')}
          ${progressRail('Disk', host.disk_percent, '%', 'disk')}
        </div>
      </div>
    </article>
  `).join('');
}

function renderDashboard() {
  const data = dashboardState.data;
  const filteredAgents = getFilteredAgents(data.agents);

  document.getElementById('generatedAt').textContent = formatTimestamp(data.generatedAt);
  buildRing(data.fleetSummary);
  renderTopPills(data.fleetSummary, data.heartbeatSummary, data.providerSummary);
  renderProviderMix(data.providerSummary);
  renderMix(data.fleetSummary);
  renderSignals(data.fleetSummary, data.resourceSummary, data.heartbeatSummary);
  renderMetrics(data.fleetSummary, data.resourceSummary, data.heartbeatSummary, data.providerSummary);
  renderRadar(data.heartbeatSummary);
  renderResourceSummary(data.resourceSummary);
  renderAgents(filteredAgents);
  renderFilterSummary(data.agents.length, filteredAgents.length);
  renderHosts(data.hosts);
  renderFindings(data.findings);
  renderJobs(data.jobs);
  renderHotHosts(data.hotHosts);
}

function attachFilters() {
  [
    ['providerFilter', 'provider'],
    ['statusFilter', 'status'],
    ['environmentFilter', 'environment']
  ].forEach(([id, key]) => {
    document.getElementById(id).addEventListener('change', (event) => {
      dashboardState.filters[key] = event.target.value;
      renderDashboard();
    });
  });
}

async function loadDashboard() {
  const response = await fetch('/api/dashboard');
  dashboardState.data = await response.json();
  syncFilterOptions(dashboardState.data.agents);
  renderDashboard();
}

attachFilters();
loadDashboard().catch((error) => {
  document.body.innerHTML = `<main class="shell"><section class="panel"><h1>Dashboard failed to load</h1><p>${error.message}</p></section></main>`;
});
