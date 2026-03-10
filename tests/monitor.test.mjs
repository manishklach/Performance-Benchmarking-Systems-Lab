import test from 'node:test';
import assert from 'node:assert/strict';
import { once } from 'node:events';
import { openDb, getSampleRows } from '../src/db.mjs';
import { startServer } from '../src/server.mjs';
import '../scripts/seed.mjs';

test('seeded sample database contains multi-provider agent data', () => {
  const rows = getSampleRows(openDb());
  assert.equal(rows.hosts.length, 3);
  assert.equal(rows.agent_instances.length, 4);
  assert.equal(rows.jobs.length, 4);
  assert.equal(rows.host_metrics.length, 3);
  assert.equal(rows.agent_metrics.length, 4);
  assert.equal(rows.heartbeats.length, 4);
  assert.equal(rows.agent_instances.some((row) => row.provider === 'anthropic'), true);
  assert.equal(rows.agent_instances.some((row) => row.provider === 'google'), true);
  assert.equal(rows.agent_instances.some((row) => row.provider === 'openclaw'), true);
  assert.equal(rows.agent_instances.every((row) => typeof row.runtime_type === 'string'), true);
});

test('dashboard api returns provider-neutral fleet summary', async () => {
  const server = await startServer({ port: 0 });
  const address = server.address();
  const response = await fetch(`http://127.0.0.1:${address.port}/api/dashboard`);
  const payload = await response.json();

  assert.equal(response.status, 200);
  assert.equal(payload.fleetSummary.total_agents, 4);
  assert.equal(payload.providerSummary.length, 4);
  assert.equal(payload.hotHosts.length, 3);
  assert.equal(payload.resourceSummary.peak_host_cpu, 67.4);
  assert.equal(payload.heartbeatSummary.total, 4);
  assert.equal(payload.agents[0].provider, 'openai');
  assert.equal(typeof payload.agents[0].agent_family, 'string');
  assert.equal(typeof payload.agents[0].runtime_type, 'string');

  server.close();
  await once(server, 'close');
});
