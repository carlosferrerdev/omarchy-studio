def value: if . == null or . == "unknown" then "Unknown" else tostring end;
def safe: gsub("[\u0000-\u001f\u007f]"; " ");
def endpoint: if .status == "selected" then "\(.name | safe) [\(.state)]" elif .status == "not_selected" then "None selected" else "Unknown" end;
def check_label: if .evidence == "not_implemented" then "not measured" elif .category == "performance" and .status == "unknown" then "not verified" else .status end;
def check_lines: "  [\(check_label)] \(.message)", (if .status != "ok" then "    Impact: \(.impact)", "    \(.hint)" else empty end);
"Omarchy Studio" + (if .command == "doctor" then " Doctor" else "" end), "",
"System",
"  Omarchy       \(.system.omarchy.version | value)",
"  Kernel        \(.system.kernel | value)",
"  Session       \(.system.session | value)",
"  Compositor    \(.system.compositor | value)", "",
"Audio",
"  PipeWire      \(.audio.pipewire.state) (graph \(if .audio.pipewire.reachable then "reachable" else "unknown" end))",
"  WirePlumber   \(.audio.wireplumber.state)",
"  JACK          \(.audio.jack.compatibility); runtime unverified", "",
"Selected session defaults",
"  Output        \(.audio.defaults.output | endpoint)",
"  Input         \(.audio.defaults.input | endpoint)",
"  Applications may use different routes.", "",
"Audio devices",
(if (.hardware.devices|length) == 0 then "  None observed (see doctor for source availability)" else .hardware.devices[] | "  \(.name | safe) [\(.transport | value)]" end), "",
"Clock settings (not active driver measurements)",
"  Rate          \(.audio.clock_settings.rate_hz | value) Hz",
"  Quantum       \(.audio.clock_settings.quantum_frames | value) frames",
"",
"Audio driver sample",
(if .audio.graph.status == "observed" then .audio.graph.drivers[] |
  "  Driver \(.node_id)     \(.rate_hz) Hz / \(.quantum_frames) frames",
  "    Theoretical period: \((.theoretical_period_ms * 100 | round) / 100) ms (not round-trip latency)"
 elif .audio.graph.status == "idle" then "  No running audio driver observed"
 else "  Unavailable (\(.audio.graph.reason))" end),
"  Round-trip    Not measured",
"  XRUN monitor  Not implemented", "",
"MIDI",
(if ([.midi.ports[] | select(.kind != "virtual")]|length) == 0 then "  No non-system endpoints observed (\(.midi.status))"
 else .midi.ports[] | select(.kind != "virtual") | "  \(.client_name | safe): \(.name | safe) [\(.directions | join(", "))]" end), "",
(if .command == "doctor" then
  "Operational checks", (.checks[] | select(.category == "health") | check_lines), "",
  "Optional capabilities", (.checks[] | select(.category == "optional") | check_lines), "",
  "Performance observations", (.checks[] | select(.category == "performance") | check_lines), ""
 else empty end),
"Operational status: \(.status | ascii_upcase)",
"Playback, recording and low-latency performance have not been tested."
