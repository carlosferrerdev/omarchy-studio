const assert = require('node:assert/strict');
const { readReport, rows, quantity } = require('../plugin/Model.js');
const report = {
  schema_version: 1, command: 'status', status: 'warning', checks: [],
  audio: { pipewire: { reachable: true }, wireplumber: { state: 'active' }, clock_settings: { rate_hz: 48000, quantum_frames: 128 } },
  hardware: { devices: [{ name: 'Studio "A"' }] }, midi: { status: 'ok', ports: [] }
};
assert.equal(readReport(JSON.stringify(report)).status, 'warning');
assert.equal(rows(report)[0].value, 'Studio "A"');
assert.equal(rows(report)[3].value, '48000 Hz / 128 frames');
assert.equal(rows(report)[4].value, 'None observed (ok)');
assert.equal(quantity(null, 'Hz'), 'Unknown');
assert.equal(quantity(0, 'Hz'), 'Unknown');
assert.equal(quantity(NaN, 'Hz'), 'Unknown');
assert.throws(() => readReport('{broken'));
assert.throws(() => readReport(JSON.stringify({ ...report, schema_version: 2 })));
assert.throws(() => readReport(JSON.stringify({ ...report, hardware: null })));
assert.throws(() => readReport(JSON.stringify({ ...report, command: 'version' })));
assert.throws(() => readReport(JSON.stringify({ ...report, hardware: { devices: [null] } })));
assert.throws(() => readReport(JSON.stringify({ ...report, midi: { ports: [null] } })));
assert.throws(() => readReport(JSON.stringify({ ...report, checks: [null] })));
assert.equal(rows(null).length, 0);
console.log('ok - plugin reads schema 1, handles unknown values and rejects invalid reports');
