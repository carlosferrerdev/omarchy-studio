const assert = require('node:assert/strict');
const { readReport, rows, quantity, summary, endpointText, findings, findingText, graphText } = require('../plugin/Model.js');
const output = { status: 'selected', name: 'Studio "A"', state: 'suspended', kind: 'device' };
const report = {
  schema_version: 2, command: 'status', status: 'ok', status_scope: 'operational', checks: [],
  audio: {
    pipewire: { reachable: true }, wireplumber: { state: 'active' },
    clock_settings: { rate_hz: 48000, quantum_frames: 128 },
    defaults: { scope: 'session_defaults', output, input: { status: 'not_selected' } }
  },
  hardware: { devices: [{ name: 'Studio "A"' }] }, midi: { status: 'ok', ports: [] }
};
assert.equal(readReport(JSON.stringify(report)).status, 'ok');
assert.equal(rows(report)[0].title, 'Default output');
assert.equal(rows(report)[0].value, 'Studio "A"');
assert.equal(rows(report)[1].value, 'None selected');
assert.equal(rows(report)[3].value, 'Sampling unavailable');
assert.equal(rows(report)[4].value, '48000 Hz / 128 frames');
assert.equal(rows(report)[5].value, 'None observed');
assert.equal(summary(report), 'Audio services available');
assert.equal(summary({ ...report, status: 'unknown' }), 'Diagnosis incomplete');
assert.equal(endpointText({ ...output, kind: 'virtual' }), 'Studio "A" (virtual)');
assert.equal(endpointText({ ...output, kind: 'monitor' }), 'Studio "A" (monitor source)');
assert.equal(endpointText({ status: 'unavailable' }), 'Unknown - refresh to inspect again');
assert.ok(endpointText({ ...output, state: 'error' }).includes('device error'));
assert.equal(quantity(null, 'Hz'), 'Unknown');
assert.equal(quantity(0, 'Hz'), 'Unknown');
assert.equal(quantity(NaN, 'Hz'), 'Unknown');
assert.throws(() => readReport('{broken'));
for (const schema_version of [1, 99]) assert.throws(() => readReport(JSON.stringify({ ...report, schema_version })));
for (const override of [
  { status_scope: 'everything' }, { hardware: null }, { command: 'version' },
  { hardware: { devices: [null] } }, { midi: { ports: [null] } }, { checks: [null] },
  { audio: { ...report.audio, defaults: null } },
  { audio: { ...report.audio, defaults: { ...report.audio.defaults, input: { status: 'selected', name: null } } } }
]) assert.throws(() => readReport(JSON.stringify({ ...report, ...override })));
const baseCheck = { id: 'test', status: 'unknown', evidence: 'unavailable', message: 'Observation missing', impact: 'Impact', hint: 'Next step' };
const measurement = { ...baseCheck, category: 'performance', evidence: 'not_implemented' };
const failure = { ...baseCheck, category: 'health', status: 'error', evidence: 'observed' };
const doctor = { ...report, command: 'doctor', checks: [measurement, failure] };
readReport(JSON.stringify(doctor));
assert.equal(findings(doctor)[0], failure);
assert.ok(findingText(measurement).startsWith('Not measured:'));
assert.ok(findingText(failure).startsWith('Needs attention:'));
assert.deepEqual(findings(report), []);
assert.equal(rows(doctor).at(-1).title, 'Audio device inventory');
assert.equal(doctor.checks[0], measurement, 'sorting must not mutate the report');
assert.equal(rows(null).length, 0);
console.log('ok - plugin displays operational health and selected defaults, rejects invalid schemas, and prioritizes actual findings');
const driver = { node_id: 20, rate_hz: 48000, quantum_frames: 128, theoretical_period_ms: 128 / 48 };
const graph = { status: 'observed', scope: 'audio_drivers', drivers: [driver] };
assert.ok(graphText(graph).includes('48000 Hz / 128 frames\nTheoretical period: 2.67 ms'));
assert.equal(graphText({ status: 'idle' }), 'No running audio driver observed');
assert.equal(graphText({ status: 'unavailable' }), 'Sampling unavailable');
assert.ok(graphText({ ...graph, drivers: [driver, { ...driver, node_id: 21, rate_hz: 44100 }] }).includes('Driver 21: 44100 Hz'));
readReport(JSON.stringify({ ...report, audio: { ...report.audio, graph } }));
for (const badGraph of [
  { ...graph, drivers: [] }, { ...graph, drivers: [null] }, { ...graph, status: 'idle' },
  { ...graph, scope: 'all_nodes' }, { ...graph, drivers: [{ ...driver, rate_hz: 0 }] },
  { ...graph, drivers: [{ ...driver, theoretical_period_ms: null }] }
]) assert.throws(() => readReport(JSON.stringify({ ...report, audio: { ...report.audio, graph: badGraph } })));
console.log('ok - plugin distinguishes idle, unavailable and independent active driver samples');
