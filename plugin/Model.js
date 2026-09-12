function validEndpoint(endpoint) {
  if (!endpoint || ["selected", "not_selected", "unavailable"].indexOf(endpoint.status) < 0) return false
  return endpoint.status !== "selected" || (typeof endpoint.name === "string" && typeof endpoint.state === "string")
}

function positiveInteger(value) {
  return typeof value === "number" && isFinite(value) && value > 0 && Math.floor(value) === value
}

function validGraph(graph) {
  // Schema 2 reports from 0.1.1 have no sampler fields.
  if (!graph || graph.status === undefined) return true
  if (["observed", "idle", "unavailable"].indexOf(graph.status) < 0 ||
      graph.scope !== "audio_drivers" || !Array.isArray(graph.drivers)) return false
  return (graph.status === "observed" ? graph.drivers.length > 0 : graph.drivers.length === 0) &&
    graph.drivers.every(function(driver) {
      return driver && typeof driver.node_id === "number" && isFinite(driver.node_id) && driver.node_id >= 0 && Math.floor(driver.node_id) === driver.node_id &&
        positiveInteger(driver.rate_hz) && positiveInteger(driver.quantum_frames) &&
        typeof driver.theoretical_period_ms === "number" && isFinite(driver.theoretical_period_ms) && driver.theoretical_period_ms > 0
    })
}

function readReport(text) {
  var report = JSON.parse(text)
  if (!report || report.schema_version !== 2 || report.status_scope !== "operational" ||
      ["status", "doctor"].indexOf(report.command) < 0 ||
      ["ok", "warning", "error", "unknown", "unsupported"].indexOf(report.status) < 0 ||
      !report.audio || !report.audio.pipewire || !report.audio.wireplumber ||
      !report.audio.clock_settings || !report.audio.defaults || report.audio.defaults.scope !== "session_defaults" ||
      !validEndpoint(report.audio.defaults.output) || !validEndpoint(report.audio.defaults.input) || !validGraph(report.audio.graph) ||
      !report.hardware || !Array.isArray(report.hardware.devices) ||
      !report.midi || !Array.isArray(report.midi.ports) || !Array.isArray(report.checks)) {
    throw new Error("Unsupported or incomplete diagnostic report")
  }
  if (!report.hardware.devices.every(function(device) { return device && typeof device.name === "string" }) ||
      !report.midi.ports.every(function(port) { return port && typeof port.kind === "string" && typeof port.client_name === "string" && typeof port.name === "string" }) ||
      !report.checks.every(function(check) {
        return check && ["health", "optional", "performance"].indexOf(check.category) >= 0 &&
          ["observed", "unavailable", "not_implemented"].indexOf(check.evidence) >= 0 &&
          typeof check.status === "string" && typeof check.message === "string" &&
          typeof check.impact === "string" && typeof check.hint === "string"
      })) {
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

function summary(report) {
  if (!report) return "Unknown"
  var messages = { ok: "Audio services available", warning: "Needs attention", error: "Audio problem detected", unknown: "Diagnosis incomplete", unsupported: "Unsupported environment" }
  return messages[report.status] || "Unknown"
}

function endpointText(endpoint) {
  if (endpoint.status === "not_selected") return "None selected"
  if (endpoint.status !== "selected") return "Unknown - refresh to inspect again"
  var suffix = endpoint.kind === "virtual" ? " (virtual)" : endpoint.kind === "monitor" ? " (monitor source)" : ""
  if (endpoint.state === "error") suffix += " - device error"
  return label(endpoint.name) + suffix
}

function graphText(graph) {
  if (!graph || graph.status === undefined || graph.status === "unavailable") return "Sampling unavailable"
  if (graph.status === "idle") return "No running audio driver observed"
  return graph.drivers.map(function(driver) {
    return "Driver " + driver.node_id + ": " + quantity(driver.rate_hz, "Hz") + " / " + quantity(driver.quantum_frames, "frames") +
      "\nTheoretical period: " + driver.theoretical_period_ms.toFixed(2) + " ms"
  }).join("\n")
}

function rows(report) {
  if (!report) return []
  var ports = report.midi.ports.filter(function(port) { return port.kind !== "virtual" })
  var result = [
    { title: "Default output", value: endpointText(report.audio.defaults.output) },
    { title: "Default input", value: endpointText(report.audio.defaults.input) },
    { title: "Audio services", value: "PipeWire " + (report.audio.pipewire.reachable ? "reachable" : "unknown") + " / WirePlumber " + label(report.audio.wireplumber.state) },
    { title: "Audio driver sample", value: graphText(report.audio.graph) },
    { title: "Clock settings", value: quantity(report.audio.clock_settings.rate_hz, "Hz") + " / " + quantity(report.audio.clock_settings.quantum_frames, "frames") },
    { title: "MIDI endpoints", value: ports.length ? ports.map(function(port) { return label(port.client_name) + ": " + label(port.name) }).join("\n") : report.midi.status === "ok" ? "None observed" : "Enumeration unavailable" }
  ]
  if (report.command === "doctor") result.push({ title: "Audio device inventory", value: report.hardware.devices.length ? report.hardware.devices.map(function(device) { return label(device.name) }).join("\n") : "None observed" })
  return result
}

function findings(report) {
  if (!report || report.command !== "doctor") return []
  var order = { health: 0, optional: 1, performance: 2 }
  return report.checks.filter(function(check) { return check.status !== "ok" }).sort(function(a, b) { return order[a.category] - order[b.category] })
}

function findingText(check) {
  var heading = check.evidence === "not_implemented" ? "Not measured" :
    check.category === "performance" ? "Not verified" :
    check.category === "optional" ? "Optional capability" : "Needs attention"
  return heading + ": " + label(check.message) + "\n" + label(check.impact) + "\n" + label(check.hint)
}

if (typeof module !== "undefined") module.exports = { readReport: readReport, rows: rows, quantity: quantity, summary: summary, endpointText: endpointText, findings: findings, findingText: findingText, graphText: graphText }
