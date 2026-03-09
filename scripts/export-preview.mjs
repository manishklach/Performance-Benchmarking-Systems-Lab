import { writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { getDashboardSnapshot, openDb, initSchema } from '../src/db.mjs';

const __filename = fileURLToPath(import.meta.url);
const projectRoot = path.resolve(path.dirname(__filename), '..');
const outputPath = path.join(projectRoot, 'data', 'dashboard-preview.svg');
const db = openDb();
initSchema(db);
const data = getDashboardSnapshot(db);

const total = data.fleetSummary.total_agents;
const trusted = data.fleetSummary.confirmed_agents + data.fleetSummary.observed_agents;
const trustPercent = Math.round((trusted / total) * 100);
const hb = data.heartbeatSummary;
const healthyPct = hb.total ? Math.round((hb.healthy / hb.total) * 100) : 0;
const delayedPct = hb.total ? Math.round((hb.delayed / hb.total) * 100) : 0;
const suspectedPct = Math.round((data.fleetSummary.suspected_agents / total) * 100);
const observedPct = Math.round((data.fleetSummary.observed_agents / total) * 100);
const confirmedPct = 100 - suspectedPct - observedPct;

function agentBlock(agent, x, y) {
  const confidence = Math.round(agent.confidence_score * 100);
  const hbColor = agent.heartbeat_state === 'healthy' ? '#18bb7d' : agent.heartbeat_state === 'delayed' ? '#ff9c3f' : '#ff5f7b';
  const stripe = agent.discovery_level === 'confirmed' ? '#18bb7d' : agent.discovery_level === 'observed' ? '#ff9c3f' : '#ff5f7b';
  const memWidth = Math.min(100, Math.round((agent.process_memory_mb || 0) / 10));
  return `
    <g transform="translate(${x},${y})">
      <rect width="460" height="220" rx="26" fill="rgba(255,255,255,0.96)" stroke="rgba(87,54,140,0.12)"/>
      <rect width="9" height="220" rx="4" fill="${stripe}"/>
      <text x="26" y="34" font-size="13" letter-spacing="2" fill="#c75f74">${agent.agent_family.toUpperCase()}</text>
      <text x="26" y="66" font-size="28" font-weight="700" fill="#281d3f">${agent.id}</text>
      <rect x="26" y="84" width="125" height="28" rx="14" fill="rgba(255,255,255,0.84)" stroke="${hbColor}"/>
      <text x="46" y="103" font-size="13" fill="${hbColor}">${agent.provider}</text>
      <circle cx="412" cy="98" r="9" fill="${hbColor}"/>
      <text x="26" y="136" font-size="15" fill="#7b738d">${agent.current_task}</text>
      <text x="26" y="160" font-size="14" fill="#7b738d">Heartbeat ${Math.round((agent.heartbeatAgeSeconds || 0) / 60)}m ago</text>
      <text x="26" y="184" font-size="13" fill="#7b738d">CPU ${Math.round(agent.process_cpu_percent || 0)}%  MEM ${Math.round(agent.process_memory_mb || 0)} MB  IO ${Math.round(agent.disk_read_kbps || 0)}r/${Math.round(agent.disk_write_kbps || 0)}w</text>
      <rect x="26" y="194" width="300" height="10" rx="5" fill="#ecebff"/>
      <rect x="26" y="194" width="${confidence * 3}" height="10" rx="5" fill="url(#purple)"/>
      <rect x="338" y="194" width="90" height="10" rx="5" fill="#e7fff3"/>
      <rect x="338" y="194" width="${Math.min(90, memWidth * 0.9)}" height="10" rx="5" fill="#18bb7d"/>
    </g>`;
}

const providerRows = data.providerSummary.map((item, index) => `
  <text x="420" y="${498 + index * 28}" font-size="18" fill="#281d3f">${item.provider}: ${item.count}</text>
`).join('');

const hostRows = data.hosts.map((host, index) => `
  <text x="1124" y="${1000 + index * 74}" font-size="20" fill="#281d3f">${host.hostname}</text>
  <text x="1124" y="${1022 + index * 74}" font-size="14" fill="#7b738d">${host.environment} · CPU ${Math.round(host.cpu_percent)}% · MEM ${Math.round(host.memory_percent)}% · DISK ${Math.round(host.disk_percent)}%</text>
`).join('');

const jobRows = data.jobs.slice(0, 3).map((job, index) => `
  <circle cx="1142" cy="${1344 + index * 70}" r="9" fill="#6d55ff"/>
  <text x="1164" y="${1350 + index * 70}" font-size="19" fill="#281d3f">${job.title}</text>
  <text x="1164" y="${1372 + index * 70}" font-size="14" fill="#7b738d">${job.provider} · ${job.hostname} · ${job.duration_seconds}s</text>
`).join('');

const svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg width="1600" height="1600" viewBox="0 0 1600 1600" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#fff3f7"/><stop offset="100%" stop-color="#fff8ef"/></linearGradient>
    <linearGradient id="purple" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="#6d55ff"/><stop offset="100%" stop-color="#ff7ca4"/></linearGradient>
    <linearGradient id="orange" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="#ffb94b"/><stop offset="100%" stop-color="#ff8e63"/></linearGradient>
    <linearGradient id="green" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="#12c27d"/><stop offset="100%" stop-color="#69e7aa"/></linearGradient>
    <linearGradient id="pink" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="#ff6079"/><stop offset="100%" stop-color="#ff7aa8"/></linearGradient>
  </defs>
  <rect width="1600" height="1600" fill="url(#bg)"/>
  <circle cx="1420" cy="80" r="220" fill="#ffd9c7" opacity="0.6"/>
  <circle cx="120" cy="1470" r="210" fill="#ddd4ff" opacity="0.5"/>
  <rect x="24" y="24" width="1552" height="1552" rx="34" fill="rgba(255,255,255,0.70)" stroke="rgba(87,54,140,0.12)"/>
  <text x="60" y="76" font-size="18" letter-spacing="3" fill="#c75f74">UNIVERSAL AGENT COMMAND</text>
  <text x="60" y="134" font-size="58" font-weight="700" fill="#281d3f">Run the agent fleet like an operations room.</text>
  <text x="60" y="176" font-size="21" fill="#7b738d">Codex, Claude, Gemini, and OpenClaw in one provider-neutral monitoring board.</text>

  <rect x="60" y="220" width="1010" height="420" rx="32" fill="rgba(255,255,255,0.84)" stroke="rgba(87,54,140,0.12)"/>
  <text x="90" y="266" font-size="18" letter-spacing="2" fill="#c75f74">CONTROL ROOM</text>
  <text x="90" y="306" font-size="34" font-weight="700" fill="#281d3f">Fleet pulse</text>
  <circle cx="250" cy="445" r="132" fill="none" stroke="#e9e7ff" stroke-width="28"/>
  <circle cx="250" cy="445" r="132" fill="none" stroke="url(#purple)" stroke-width="28" stroke-dasharray="${trustPercent * 8.3} 999" stroke-linecap="round" transform="rotate(-90 250 445)"/>
  <text x="250" y="454" text-anchor="middle" font-size="72" font-weight="700" fill="#281d3f">${total}</text>
  <text x="250" y="486" text-anchor="middle" font-size="16" letter-spacing="2" fill="#7b738d">AGENTS</text>
  <text x="420" y="356" font-size="24" font-weight="700" fill="#281d3f">Discovery confidence</text>
  <text x="860" y="356" font-size="20" fill="#7b738d">${trustPercent}% trusted</text>
  <rect x="420" y="382" width="560" height="36" rx="18" fill="#ecebff"/>
  <rect x="420" y="382" width="${5.6 * confirmedPct}" height="36" rx="18" fill="url(#green)"/>
  <rect x="${420 + 5.6 * confirmedPct}" y="382" width="${5.6 * observedPct}" height="36" fill="url(#orange)"/>
  <rect x="${420 + 5.6 * (confirmedPct + observedPct)}" y="382" width="${5.6 * suspectedPct}" height="36" rx="18" fill="url(#pink)"/>
  <text x="420" y="458" font-size="18" fill="#281d3f">Provider mix</text>
  ${providerRows}

  <rect x="1098" y="220" width="442" height="420" rx="32" fill="rgba(255,255,255,0.84)" stroke="rgba(87,54,140,0.12)"/>
  <text x="1132" y="266" font-size="18" letter-spacing="2" fill="#c75f74">TELEMETRY</text>
  <text x="1132" y="306" font-size="34" font-weight="700" fill="#281d3f">Pressure radar</text>
  <circle cx="1260" cy="446" r="106" fill="none" stroke="#ecebff" stroke-width="24"/>
  <circle cx="1260" cy="446" r="106" fill="none" stroke="#18bb7d" stroke-width="24" stroke-dasharray="${healthyPct * 6.6} 999" transform="rotate(-90 1260 446)"/>
  <circle cx="1260" cy="446" r="106" fill="none" stroke="#ff9c3f" stroke-width="24" stroke-dasharray="${delayedPct * 6.6} 999" transform="rotate(${healthyPct * 3.6 - 90} 1260 446)"/>
  <text x="1260" y="454" text-anchor="middle" font-size="52" font-weight="700" fill="#281d3f">${hb.total}</text>
  <text x="1260" y="486" text-anchor="middle" font-size="16" fill="#7b738d">heartbeat set</text>
  <text x="1380" y="392" font-size="18" fill="#281d3f">Healthy ${hb.healthy}</text>
  <text x="1380" y="432" font-size="18" fill="#281d3f">Delayed ${hb.delayed}</text>
  <text x="1380" y="472" font-size="18" fill="#281d3f">Stale ${hb.stale}</text>
  <text x="1132" y="556" font-size="18" fill="#7b738d">Average CPU ${data.resourceSummary.avg_host_cpu}%</text>
  <rect x="1132" y="570" width="340" height="16" rx="8" fill="#ecebff"/><rect x="1132" y="570" width="${3.4 * data.resourceSummary.avg_host_cpu}" height="16" rx="8" fill="#6d55ff"/>
  <text x="1132" y="614" font-size="18" fill="#7b738d">Average memory ${data.resourceSummary.avg_memory_percent}%</text>
  <rect x="1132" y="628" width="340" height="16" rx="8" fill="#e8fff4"/><rect x="1132" y="628" width="${3.4 * data.resourceSummary.avg_memory_percent}" height="16" rx="8" fill="#18bb7d"/>

  <rect x="60" y="674" width="360" height="140" rx="28" fill="#f3f1ff"/><text x="88" y="718" font-size="18" fill="#7b738d">Confirmed agents</text><text x="88" y="774" font-size="52" font-weight="700" fill="#18bb7d">${data.fleetSummary.confirmed_agents}</text>
  <rect x="438" y="674" width="360" height="140" rx="28" fill="#fff1e2"/><text x="466" y="718" font-size="18" fill="#7b738d">24h spend</text><text x="466" y="774" font-size="52" font-weight="700" fill="#ff9c3f">$${Number(data.fleetSummary.total_cost).toFixed(2)}</text>
  <rect x="816" y="674" width="360" height="140" rx="28" fill="#fff0f4"/><text x="844" y="718" font-size="18" fill="#7b738d">Stale HB</text><text x="844" y="774" font-size="52" font-weight="700" fill="#ff5f7b">${hb.stale}</text>
  <rect x="1194" y="674" width="346" height="140" rx="28" fill="#eef0ff"/><text x="1222" y="718" font-size="18" fill="#7b738d">Network flow</text><text x="1222" y="774" font-size="44" font-weight="700" fill="#5d72f2">${Math.round(data.resourceSummary.total_network_kbps)} kbps</text>

  <rect x="60" y="850" width="1000" height="680" rx="32" fill="rgba(255,255,255,0.86)" stroke="rgba(87,54,140,0.12)"/>
  <text x="94" y="898" font-size="18" letter-spacing="2" fill="#c75f74">PROCESSES</text>
  <text x="94" y="938" font-size="34" font-weight="700" fill="#281d3f">Agent telemetry</text>
  ${agentBlock(data.agents[0], 94, 972)}
  ${agentBlock(data.agents[1], 560, 972)}
  ${agentBlock(data.agents[2], 94, 1210)}
  ${agentBlock(data.agents[3], 560, 1210)}

  <rect x="1090" y="850" width="450" height="330" rx="32" fill="rgba(255,255,255,0.86)" stroke="rgba(87,54,140,0.12)"/>
  <text x="1124" y="898" font-size="18" letter-spacing="2" fill="#c75f74">HOTSPOTS</text>
  <text x="1124" y="938" font-size="34" font-weight="700" fill="#281d3f">Host pressure</text>
  ${hostRows}

  <rect x="1090" y="1200" width="450" height="330" rx="32" fill="rgba(255,255,255,0.86)" stroke="rgba(87,54,140,0.12)"/>
  <text x="1124" y="1248" font-size="18" letter-spacing="2" fill="#c75f74">EXECUTION</text>
  <text x="1124" y="1288" font-size="34" font-weight="700" fill="#281d3f">Recent jobs</text>
  ${jobRows}
</svg>`;

writeFileSync(outputPath, svg);
console.log(outputPath);
