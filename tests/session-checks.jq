# Validate the fields this observational test consumes, independently of host hardware.
def valid_report:
  type == "object" and .schema_version == 2 and .command == "doctor"
  and .status_scope == "operational"
  and (.status as $s | ["ok","warning","unknown","unsupported","error"] | index($s) != null)
  and (.audio.graph.status as $s | ["observed","idle","unavailable"] | index($s) != null)
  and (.audio.graph.drivers | type == "array" and all(.[]; type == "object"
    and (.node_id | type == "number" and . >= 0 and floor == .)
    and (.rate_hz | type == "number" and . > 0 and floor == .)
    and (.quantum_frames | type == "number" and . > 0 and floor == .)))
  and (if .audio.graph.status == "observed" then (.audio.graph.drivers|length) > 0 else .audio.graph.drivers == [] end)
  and (.hardware.devices | type == "array" and all(.[]; type == "object"))
  and (.midi.status as $s | ["ok","unknown"] | index($s) != null)
  and (.midi.ports | type == "array" and all(.[]; type == "object" and (.directions | type == "array")));
def observation($id; $result; $message): {id:$id,result:$result,message:$message};
if length == 1 then .[0] else error("expected one report") end
| if valid_report | not then error("invalid report") else . end
| if ($exit_code == 5) != (.status == "error") or ($exit_code == 4) != (.status == "unsupported")
  then error("inconsistent exit status") else . end
| {checks:[
    observation("operational";
      (if .status == "ok" then "pass" elif .status == "error" then "fail" else "inconclusive" end);
      (if .status == "ok" then "Operational checks passed."
       elif .status == "error" then "An operational problem was observed. Inspect the checkout CLI doctor."
       else "Operational checks are incomplete or need attention. Inspect the checkout CLI doctor." end)),
    observation("graph";
      (if .audio.graph.status == "unavailable" then "inconclusive"
       elif $expected_graph == "any" or ($expected_graph == "active" and .audio.graph.status == "observed")
         or ($expected_graph == "idle" and .audio.graph.status == "idle") then "pass" else "inconclusive" end);
      (if .audio.graph.status == "unavailable" then "Driver sample unavailable; refresh during the intended workload."
       elif .audio.graph.status == "idle" then "No running audio driver observed (expected: \($expected_graph))."
       else "\(.audio.graph.drivers|length) active audio driver(s) observed (expected: \($expected_graph))." end)),
    (if $require_usb then observation("usb_audio";
      (if any(.hardware.devices[]; .transport == "usb") then "pass" else "inconclusive" end);
      (if any(.hardware.devices[]; .transport == "usb") then "USB audio device enumerated; application routing is unverified."
       else "Required USB audio device not observed. Connect the intended interface and refresh." end)) else empty end),
    (if $require_midi then observation("midi_source";
      (if .midi.status == "ok" and any(.midi.ports[]; .kind == "hardware" and (.directions | index("source") != null))
       then "pass" else "inconclusive" end);
      (if .midi.status == "ok" and any(.midi.ports[]; .kind == "hardware" and (.directions | index("source") != null))
       then "Hardware MIDI source enumerated; event delivery is unverified."
       else "Required hardware MIDI source not confirmed. Check the controller and ALSA enumeration." end)) else empty end)
  ]}
| .result = (if any(.checks[]; .result == "fail") then "fail"
  elif any(.checks[]; .result == "inconclusive") then "inconclusive" else "pass" end)
