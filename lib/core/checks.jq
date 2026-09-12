def check($category; $id; $status; $message; $impact; $hint):
  {category:$category,id:$id,status:$status,
   evidence:(if $status == "unknown" then "unavailable" else "observed" end),
   message:$message,impact:$impact,hint:$hint};
def service_status($state; $inactive):
  if $state == "active" then "ok" elif $state == "unknown" then "unknown"
  elif $state == "inactive" or $state == "failed" then $inactive else "warning" end;
def endpoint_status:
  if .status == "not_selected" then "warning"
  elif .status != "selected" then "unknown"
  elif .state == "error" then "error"
  elif .state == "creating" then "warning"
  elif .state == "unknown" then "unknown" else "ok" end;
. as $report | .checks = [
  check("health"; "system.omarchy"; (if .system.omarchy.detected then "ok" else "unsupported" end);
    (if .system.omarchy.detected then "Omarchy detected" else "Omarchy could not be detected" end);
    "Integration is supported on the current Omarchy release."; "Other environments receive partial reports."),
  check("health"; "system.user_manager";
    (if .system.user_manager == "running" then "ok" elif .system.user_manager == "unknown" then "unknown" else "warning" end);
    ("User session: " + .system.user_manager); "User services may be unavailable or still starting.";
    "Check: systemctl --user status"),
  check("health"; "audio.pipewire";
    (if .audio.pipewire.reachable then "ok" elif .audio.pipewire.state == "inactive" or .audio.pipewire.state == "failed" then "error" else "unknown" end);
    (if .audio.pipewire.reachable then "PipeWire graph is reachable" else "PipeWire graph could not be inspected" end);
    "Applications need a reachable audio server to use PipeWire.";
    "Check: systemctl --user status pipewire; pw-dump. Verify PipeWire tools and the user session."),
  check("health"; "audio.wireplumber"; service_status(.audio.wireplumber.state; "error");
    ("WirePlumber service: " + .audio.wireplumber.state);
    "Automatic device selection and routing may not work when the session manager is unavailable.";
    "Check: systemctl --user status wireplumber"),
  check("health"; "audio.pulse"; service_status(.audio.pulse.state; "warning");
    ("PipeWire Pulse service: " + .audio.pulse.state);
    "Applications using PulseAudio compatibility may have no audio.";
    "Check: systemctl --user status pipewire-pulse"),
  check("health"; "audio.default_output"; (.audio.defaults.output | endpoint_status);
    (if .audio.defaults.output.status == "selected" then "Default output selected" elif .audio.defaults.output.status == "not_selected" then "No default output selected" else "Default output could not be resolved" end);
    "New automatically connected playback streams use this default; existing applications may use another route.";
    "Check the output selection in the Omarchy audio panel or run wpctl status. A suspended node can be a normal idle device."),
  check("health"; "audio.default_input";
    (if .audio.defaults.input.status == "not_selected" then "ok" else (.audio.defaults.input | endpoint_status) end);
    (if .audio.defaults.input.status == "selected" then "Default input selected" elif .audio.defaults.input.status == "not_selected" then "No default input selected" else "Default input could not be resolved" end);
    "Recording needs an appropriate input, but playback does not. Selecting an input does not prove capture works.";
    "Check the input selection in the Omarchy audio panel and your DAW. No microphone test was performed."),
  check("optional"; "audio.jack"; (if .audio.jack.package_version != null then "ok" else "unknown" end);
    (if .audio.jack.package_version != null then "PipeWire JACK package installed; runtime not tested" else "PipeWire JACK package not confirmed" end);
    "Only applications using the JACK API need this compatibility layer.";
    "Check: pacman -Q pipewire-jack. No standalone JACK server is required by Studio."),
  check("optional"; "hardware.audio";
    (if (.hardware.devices|length) > 0 or .hardware.alsa.status == "ok" or .hardware.pipewire_status == "ok" then "ok" else "unknown" end);
    ((.hardware.devices|length|tostring) + " audio devices observed");
    "Device inventory does not establish professional capabilities or actual application routing.";
    "Check: aplay -l; arecord -l; wpctl status."),
  check("optional"; "midi.endpoints"; .midi.status;
    (if .midi.status == "ok" then (([.midi.ports[]|select(.kind != "virtual")]|length|tostring) + " non-system ALSA MIDI endpoints observed") else "MIDI enumeration incomplete" end);
    "MIDI is optional for audio playback and recording.";
    "Check: aconnect -i; aconnect -o. Empty inventory is normal without a controller."),
  (check("performance"; "performance.realtime";
    (if .realtime.pipewire_realtime_thread_observed == true then "ok" else "unknown" end);
    (if .realtime.pipewire_realtime_thread_observed == true then "A PipeWire FIFO/RR thread was observed" else "PipeWire realtime scheduling is not verified" end);
    "This snapshot does not establish low-latency reliability.";
    "Inspect during a representative audio workload. An idle graph may have no realtime thread; RTKit and shell limits alone are insufficient.")
    | .evidence = (if $report.realtime.pipewire_realtime_thread_observed != null then "observed" else "unavailable" end)),
  check("performance"; "audio.graph";
    (if .audio.graph.status == "observed" or .audio.graph.status == "idle" then "ok" else "unknown" end);
    (if .audio.graph.status == "observed" then "Active audio driver clocks observed"
     elif .audio.graph.status == "idle" then "No running audio driver observed in this sample"
     else "Active audio driver clocks could not be sampled" end);
    "Driver periods describe graph scheduling, not hardware round-trip latency or recording reliability.";
    "Refresh during your own audio workload. If unavailable, check pw-top -b -n 2 and PipeWire profiler availability; no stream is started by Studio."),
  (check("performance"; "audio.measurement"; "unknown";
    "XRUNs and round-trip latency: not measured";
    "These collectors are not implemented yet; this is not a detected configuration problem.";
    "The pw-top ERR column combines XRUNs and errors; round-trip latency needs an appropriate loopback measurement.")
    | .evidence = "not_implemented")
]
| .status_scope = "operational"
| [.checks[] | select(.category == "health")] as $health
| .status = (if any($health[]; .status == "error") then "error"
  elif any($health[]; .status == "unsupported") then "unsupported"
  elif any($health[]; .status == "warning") then "warning"
  elif any($health[]; .status == "unknown") then "unknown" else "ok" end)
