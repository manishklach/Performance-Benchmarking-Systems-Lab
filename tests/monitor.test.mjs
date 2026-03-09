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
const trustPercent = Math.round(((data.fleetSummary.confirmed_agents + data.fleetSummary.observed_agents) / total) * 100);
const widths = {
  confirmed: Math.round((data.fleetSummary.confirmed_agents / total) * 100),
  observed: Math.round((data.fleetSummary.observed_agents / total) * 100),
  suspected: Math.round((data.fleetSummary.suspected_agents / total) * 100)
};
const hb = data.heartbeatSummary;
const healthyPct = Math.round((hb.healthy / hb.total) * 100);
const delayedPct = Math.round((hb.delayed / hb.total) * 100);

const svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg width="1440" height="1380" viewBox="0 0 1440 1380" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#FFF0F7" /><stop offset="100%" stop-color="#FFF7EF" /></linearGradient>
    <linearGradient id="bluePink" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#5A6FF0" /><stop offset="100%" stop-color="#FF7CA2" /></linearGradient>
    <linearGradient id="green" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="#13C47D" /><stop offset="100%" stop-color="#55E6A6" /></linearGradient>
    <linearGradient id="orange" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="#FFBE4D" /><stop offset="100%" stop-color="#FF8F5B" /></linearGradient>
    <linearGradient id="rose" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="#FF5C74" /><stop offset="100%" stop-color="#FF7CA2" /></linearGradient>
  </defs>
  <rect width="1440" height="1380" fill="url(#bg)" />
  <circle cx="1240" cy="100" r="170" fill="#FFD9C2" opacity="0.55" />
  <circle cx="150" cy="1220" r="180" fill="#D9D1FF" opacity="0.55" />
  <rect x="24" y="24" width="1392" height="1332" rx="30" fill="rgba(255,255,255,0.72)" stroke="rgba(94,58,126,0.12)" />
  <text x="54" y="74" font-size="18" letter-spacing="2" fill="#C55A6E">CODEX FLEET MONITOR</text>
  <text x="54" y="124" font-size="54" font-weight="700" fill="#2D2140">See the Codex fleet, not just a table.</text>
  <text x="54" y="160" font-size="20" fill="#756D87">Confidence, heartbeat freshness, workload, and resource pressure in one screen.</text>
  <rect x="54" y="200" width="850" height="240" rx="28" fill="rgba(255,255,255,0.86)" stroke="rgba(94,58,126,0.10)" />
  <circle cx="180" cy="320" r="78" fill="none" stroke="rgba(90,111,240,0.12)" stroke-width="24" />
  <circle cx="180" cy="320" r="78" fill="none" stroke="url(#bluePink)" stroke-width="24" stroke-dasharray="${trustPercent * 4.9} 999" stroke-linecap="round" transform="rotate(-90 180 320)" />
  <text x="180" y="330" text-anchor="middle" font-size="40" font-weight="700" fill="#2D2140">${total}</text>
  <text x="290" y="290" font-size="28" font-weight="700" fill="#2D2140">Fleet pulse</text>
  <text x="290" y="326" font-size="18" fill="#756D87">${trustPercent}% confirmed or observed</text>
  <rect x="290" y="350" width="150" height="70" rx="20" fill="#F8F3FF" /><text x="314" y="378" font-size="16" fill="#756D87">Healthy HB</text><text x="314" y="407" font-size="28" font-weight="700" fill="#16B87A">${hb.healthy}</text>
  <rect x="458" y="350" width="150" height="70" rx="20" fill="#FFF1E3" /><text x="482" y="378" font-size="16" fill="#756D87">Peak CPU</text><text x="482" y="407" font-size="28" font-weight="700" fill="#FF9B3D">${Math.round(data.resourceSummary.peak_host_cpu)}%</text>
  <rect x="626" y="350" width="150" height="70" rx="20" fill="#FFF0F4" /><text x="650" y="378" font-size="16" fill="#756D87">Stale HB</text><text x="650" y="407" font-size="28" font-weight="700" fill="#FF5C74">${hb.stale}</text>
  <rect x="930" y="200" width="432" height="240" rx="28" fill="rgba(255,255,255,0.86)" stroke="rgba(94,58,126,0.10)" />
  <text x="960" y="246" font-size="28" font-weight="700" fill="#2D2140">Discovery mix</text>
  <rect x="960" y="286" width="370" height="28" rx="14" fill="#EEF0FF" />
  <rect x="960" y="286" width="${370 * widths.confirmed / 100}" height="28" rx="14" fill="url(#green)" />
  <rect x="${960 + (370 * widths.confirmed / 100)}" y="286" width="${370 * widths.observed / 100}" height="28" fill="url(#orange)" />
  <rect x="${960 + (370 * (widths.confirmed + widths.observed) / 100)}" y="286" width="${370 * widths.suspected / 100}" height="28" rx="14" fill="url(#rose)" />
  <text x="960" y="352" font-size="18" fill="#2D2140">Confirmed: ${data.fleetSummary.confirmed_agents}</text>
  <text x="960" y="386" font-size="18" fill="#2D2140">Observed: ${data.fleetSummary.observed_agents}</text>
  <text x="960" y="420" font-size="18" fill="#2D2140">Suspected: ${data.fleetSummary.suspected_agents}</text>
  <g transform="translate(54,470)"><rect width="310" height="120" rx="24" fill="#F8F3FF" /><text x="24" y="40" font-size="18" fill="#756D87">Confirmed agents</text><text x="24" y="82" font-size="42" font-weight="700" fill="#16B87A">${data.fleetSummary.confirmed_agents}</text></g>
  <g transform="translate(384,470)"><rect width="310" height="120" rx="24" fill="#FFF1E3" /><text x="24" y="40" font-size="18" fill="#756D87">24h spend</text><text x="24" y="82" font-size="42" font-weight="700" fill="#FF9B3D">$${Number(data.fleetSummary.total_cost).toFixed(2)}</text></g>
  <g transform="translate(714,470)"><rect width="310" height="120" rx="24" fill="#FFF0F4" /><text x="24" y="40" font-size="18" fill="#756D87">Delayed HB</text><text x="24" y="82" font-size="42" font-weight="700" fill="#FF5C74">${hb.delayed}</text></g>
  <g transform="translate(1044,470)"><rect width="318" height="120" rx="24" fill="#EEF0FF" /><text x="24" y="40" font-size="18" fill="#756D87">Network flow</text><text x="24" y="82" font-size="34" font-weight="700" fill="#5A6FF0">${Math.round(data.resourceSummary.total_network_kbps)} kbps</text></g>
  <rect x="54" y="622" width="640" height="220" rx="28" fill="rgba(255,255,255,0.86)" stroke="rgba(94,58,126,0.10)" />
  <text x="84" y="666" font-size="30" font-weight="700" fill="#2D2140">Resource overview</text>
  <text x="84" y="714" font-size="18" fill="#756D87">Average host CPU ${data.resourceSummary.avg_host_cpu}%</text>
  <rect x="84" y="728" width="250" height="16" rx="8" fill="#EEF0FF" /><rect x="84" y="728" width="${2.5 * data.resourceSummary.avg_host_cpu}" height="16" rx="8" fill="#5A6FF0" />
  <text x="84" y="786" font-size="18" fill="#756D87">Average memory ${data.resourceSummary.avg_memory_percent}%</text>
  <rect x="84" y="800" width="250" height="16" rx="8" fill="#E6FFF2" /><rect x="84" y="800" width="${2.5 * data.resourceSummary.avg_memory_percent}" height="16" rx="8" fill="#16B87A" />
  <text x="380" y="714" font-size="18" fill="#756D87">Peak disk ${data.resourceSummary.peak_disk_percent}%</text>
  <rect x="380" y="728" width="250" height="16" rx="8" fill="#FFF2DE" /><rect x="380" y="728" width="${2.5 * data.resourceSummary.peak_disk_percent}" height="16" rx="8" fill="#FF9B3D" />
  <text x="380" y="786" font-size="18" fill="#756D87">Hot hosts ${data.resourceSummary.hot_host_count}</text>
  <text x="380" y="825" font-size="34" font-weight="700" fill="#2D2140">${Math.round(data.resourceSummary.total_network_kbps)} kbps</text>
  <rect x="720" y="622" width="642" height="220" rx="28" fill="rgba(255,255,255,0.86)" stroke="rgba(94,58,126,0.10)" />
  <text x="750" y="666" font-size="30" font-weight="700" fill="#2D2140">Heartbeat monitor</text>
  <circle cx="840" cy="742" r="62" fill="none" stroke="#F0F1FF" stroke-width="22" />
  <circle cx="840" cy="742" r="62" fill="none" stroke="#16B87A" stroke-width="22" stroke-dasharray="${healthyPct * 3.9} 999" transform="rotate(-90 840 742)" />
  <circle cx="840" cy="742" r="62" fill="none" stroke="#FF9B3D" stroke-width="22" stroke-dasharray="${delayedPct * 3.9} 999" transform="rotate(${healthyPct * 3.6 - 90} 840 742)" />
  <text x="840" y="750" text-anchor="middle" font-size="34" font-weight="700" fill="#2D2140">${hb.total}</text>
  <text x="960" y="716" font-size="18" fill="#2D2140">Healthy: ${hb.healthy}</text>
  <text x="960" y="752" font-size="18" fill="#2D2140">Delayed: ${hb.delayed}</text>
  <text x="960" y="788" font-size="18" fill="#2D2140">Stale: ${hb.stale}</text>
  <rect x="54" y="874" width="860" height="440" rx="28" fill="rgba(255,255,255,0.86)" stroke="rgba(94,58,126,0.10)" />
  <text x="84" y="918" font-size="30" font-weight="700" fill="#2D2140">Agent cards</text>
  ${data.agents.slice(0,4).map((agent, index) => {
    const x = 84 + (index % 2) * 394;
    const y = 950 + Math.floor(index / 2) * 172;
    const confidence = Math.round(agent.confidence_score * 100);
    const stroke = agent.discovery_level === 'confirmed' ? '#16B87A' : agent.discovery_level === 'observed' ? '#FF9B3D' : '#FF5C74';
    const hbColor = agent.heartbeat_state === 'healthy' ? '#16B87A' : agent.heartbeat_state === 'delayed' ? '#FF9B3D' : '#FF5C74';
    return `<g transform="translate(${x},${y})"><rect width="360" height="144" rx="24" fill="#FFFFFF" stroke="rgba(94,58,126,0.10)" /><rect width="8" height="144" rx="4" fill="${stroke}" /><text x="24" y="28" font-size="12" letter-spacing="1.5" fill="#C55A6E">${agent.codex_type.toUpperCase()}</text><text x="24" y="54" font-size="22" font-weight="700" fill="#2D2140">${agent.id}</text><text x="24" y="78" font-size="14" fill="#756D87">Heartbeat ${agent.heartbeat_state} · ${Math.round((agent.heartbeatAgeSeconds || 0) / 60)}m ago</text><circle cx="320" cy="74" r="8" fill="${hbColor}" /><text x="24" y="100" font-size="14" fill="#756D87">CPU ${Math.round(agent.process_cpu_percent || 0)}% · MEM ${Math.round(agent.process_memory_mb || 0)} MB</text><rect x="24" y="112" width="240" height="10" rx="5" fill="#EEF0FF" /><rect x="24" y="112" width="${2.4 * confidence}" height="10" rx="5" fill="url(#bluePink)" /><text x="278" y="121" font-size="14" fill="#2D2140">${confidence}%</text></g>`;
  }).join('')}
  <rect x="940" y="874" width="422" height="440" rx="28" fill="rgba(255,255,255,0.86)" stroke="rgba(94,58,126,0.10)" />
  <text x="970" y="918" font-size="30" font-weight="700" fill="#2D2140">Hosts and jobs</text>
  ${data.hosts.slice(0,3).map((host, index) => {
    const y = 964 + index * 56;
    return `<text x="970" y="${y}" font-size="18" fill="#2D2140">${host.hostname}</text><text x="970" y="${y + 22}" font-size="14" fill="#756D87">${host.environment} · CPU ${Math.round(host.cpu_percent)}% · ${host.running_count}/${host.agent_count} running</text>`;
  }).join('')}
  ${data.jobs.slice(0,3).map((job, index) => {
    const y = 1142 + index * 44;
    return `<circle cx="980" cy="${y - 6}" r="8" fill="#5A6FF0" /><text x="1000" y="${y}" font-size="18" fill="#2D2140">${job.title}</text><text x="1000" y="${y + 18}" font-size="14" fill="#756D87">${job.hostname} · ${job.outcome} · ${job.duration_seconds}s</text>`;
  }).join('')}
</svg>`;

writeFileSync(outputPath, svg);
console.log(outputPath);
