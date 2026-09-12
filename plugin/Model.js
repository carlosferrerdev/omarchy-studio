function readReport(text) {
  var report = JSON.parse(text)
  if (!report || report.schema_version !== 2 ||
      ["status", "doctor"].indexOf(report.command) < 0 ||
      ["ok", "warning", "error", "unknown", "unsupported"].indexOf(report.status) < 0 ||
      !report.audio || !report.audio.pipewire || !report.audio.wireplumber ||
      !report.audio.clock_settings || !report.hardware || !Array.isArray(report.hardware.devices) ||
      !report.midi || !Array.isArray(report.midi.ports) || !Array.isArray(report.checks)) {
    throw new Error("Unsupported or incomplete diagnostic report")
  }
  if (!report.hardware.devices.every(function(device) { return device && typeof device.name === "string" }) ||
      !report.midi.ports.every(function(port) { return port && typeof port.kind === "string" && typeof port.client_name === "string" && typeof port.name === "string" }) ||
      !report.checks.every(function(check) { return check && typeof check.status === "string" && typeof check.message === "string" && typeof check.hint === "string" })) {
    throw new Error("Malformed diagnostic entries")
  }
  return report
}

function label(value) {
  return typeof value === "string" ? value.replace(/[\x00-\x1f\x7f]/g, " ") : "Unknown"
}

function quantity(value, unit) {
  return typeof value === "number" && isFinite(value) && value > 0 ? String(value) + " " + unit : "Unknown"
}

function rows(report) {
  if (!report) return []
  var ports = report.midi.ports.filter(function(port) { return port.kind !== "virtual" })
  return [
    { title: "Audio devices", value: report.hardware.devices.length ? report.hardware.devices.map(function(device) { return label(device.name) }).join("\n") : "None observed" },
    { title: "PipeWire", value: report.audio.pipewire.reachable ? "Graph reachable" : "Unknown" },
    { title: "WirePlumber", value: label(report.audio.wireplumber.state) },
    { title: "Clock settings", value: quantity(report.audio.clock_settings.rate_hz, "Hz") + " / " + quantity(report.audio.clock_settings.quantum_frames, "frames") },
    { title: "MIDI endpoints", value: ports.length ? ports.map(function(port) { return label(port.client_name) + ": " + label(port.name) }).join("\n") : "None observed (" + label(report.midi.status) + ")" }
  ]
}

if (typeof module !== "undefined") module.exports = { readReport: readReport, rows: rows, quantity: quantity }
