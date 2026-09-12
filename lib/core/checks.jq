def check($id; $status; $message; $hint): {id:$id,status:$status,message:$message,hint:$hint};
. as $r | .checks = [
  check("system.omarchy"; (if .system.omarchy.detected then "ok" else "unsupported" end);
    (if .system.omarchy.detected then "Omarchy detected" else "Omarchy could not be detected" end); "Target: current Omarchy. Other environments receive partial reports."),
  check("system.user_manager"; (if .system.user_manager == "running" then "ok" else "warning" end);
    ("User session: " + .system.user_manager); "Check: systemctl --user status"),
  check("audio.pipewire"; (if .audio.pipewire.reachable then "ok" elif .audio.pipewire.state == "inactive" or .audio.pipewire.state == "failed" then "error" else "unknown" end);
    (if .audio.pipewire.reachable then "PipeWire graph is reachable" else "PipeWire graph could not be inspected" end);
    "Check: systemctl --user status pipewire; pw-dump. Check that PipeWire tools are installed and the user session is available."),
  check("audio.wireplumber"; (if .audio.wireplumber.state == "active" then "ok" elif .audio.wireplumber.state == "unknown" then "unknown" else "error" end);
    ("WirePlumber service: " + .audio.wireplumber.state); "Check: systemctl --user status wireplumber"),
  check("audio.pulse"; (if .audio.pulse.state == "active" then "ok" else "warning" end);
    ("PipeWire Pulse service: " + .audio.pulse.state); "Check: systemctl --user status pipewire-pulse"),
  check("audio.jack"; (if .audio.jack.package_version != null then "ok" else "unknown" end);
    (if .audio.jack.package_version != null then "PipeWire JACK package installed; runtime not tested" else "PipeWire JACK package not confirmed" end);
    "Check: pacman -Q pipewire-jack. No standalone JACK server is required by Studio."),
  check("hardware.audio"; (if (.hardware.devices|length) > 0 then "ok" elif .hardware.alsa.status == "ok" or .hardware.pipewire_status == "ok" then "warning" else "unknown" end);
    ((.hardware.devices|length|tostring) + " audio devices observed"); "Check: aplay -l; arecord -l; wpctl status. No professional capabilities are inferred."),
  check("midi.endpoints"; .midi.status;
    (if .midi.status == "ok" then (([.midi.ports[]|select(.kind != "virtual")]|length|tostring) + " non-system ALSA MIDI endpoints observed") else "MIDI enumeration incomplete" end);
    "Check: aconnect -i; aconnect -o. Empty inventory is normal without a controller."),
  check("performance.realtime"; (if .realtime.pipewire_realtime_thread_observed == true then "ok" else "unknown" end);
    (if .realtime.pipewire_realtime_thread_observed == true then "A PipeWire FIFO/RR thread was observed" else "PipeWire realtime scheduling could not be verified" end);
    "An idle graph may have no realtime thread. Inspect during a representative audio workload; RTKit and shell limits alone do not prove scheduling."),
  check("audio.measurement"; "unknown"; "Active driver rate, quantum, XRUNs and round-trip latency are not measured";
    "Clock settings are configuration only. Inspect active drivers with pw-top; real round-trip latency requires an appropriate loopback measurement.")
] | .status = (if any(.checks[]; .status == "error") then "error"
  elif any(.checks[]; .status == "unsupported") then "unsupported"
  elif any(.checks[]; .status == "warning" or .status == "unknown") then "warning" else "ok" end)
