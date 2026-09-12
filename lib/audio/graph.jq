# pw-top 1.6 batch layout. Keep names private: use them only to correlate snapshots.
def graph_unavailable($reason):
  {status:"unavailable",reason:$reason,source:"unavailable",scope:"audio_drivers",
   rate_hz:null,quantum_frames:null,drivers:[]};
def top_rows($text):
  "S   ID  QUANT   RATE    WAIT    BUSY   W/Q   B/Q  ERR FORMAT           NAME" as $header
  | ($text | split("\n") | map(select(length > 0) | if . == $header + " " then $header else . end)) as $lines
  | if ($lines | map(select(. == $header)) | length) != 2 or $lines[0] != $header
    then error("incomplete sample") else $lines end
  | (reduce .[] as $line ([]; if $line == $header then [] else . + [$line] end))
  | map((capture("^(?<state>[ECSIRtT!]) +(?<id>[0-9]+) +(?<quantum>[0-9]+) +(?<rate>[0-9]+) +\\S+ +\\S+ +\\S+ +\\S+ +[0-9]+ (?<format>.{16}) (?<marker> [+=] )?(?<name>.+)$") // error("invalid row"))
    | .id |= tonumber | .quantum |= tonumber | .rate |= tonumber)
  | if length == 0 or (map(.id) | unique | length) != length then error("invalid inventory") else . end;
def audio_node:
  (.info.props["media.class"] // "") | test("^(Audio/|Stream/(Input|Output)/Audio$)");
def running: .state == "R" or .state == "t" or .state == "T";
def sampled_graph($dump; $rows):
  [$dump[] | select(.type == "PipeWire:Interface:Node")] as $nodes
  | [$rows[] | . as $row
    | [$nodes[] | select(.id == $row.id)] as $matches
    | if ($matches | length) != 1 then error("snapshot mismatch") else $matches[0] end
    | if (.info.props["node.name"] | type) != "string" or .info.props["node.name"] != $row.name
      then error("snapshot mismatch") else $row + {audio:audio_node} end] as $matched
  | if any($nodes[] | select(audio_node); .id as $id | all($matched[]; .id != $id))
    then error("snapshot mismatch") else $matched end
  # A dummy/virtual driver can schedule audio followers. Never use follower clocks.
  | reduce .[] as $row ([];
      if $row.marker == null then . + [{driver:$row,members:[$row]}]
      elif length == 0 then error("orphan follower") else .[-1].members += [$row] end)
  | map(select(any(.members[]; .audio))) as $groups
  | if ($groups | length) == 0 then graph_unavailable("no_audio_nodes")
    elif any($groups[].members[]; .state == "C" or .state == "E" or .state == "!")
      then graph_unavailable("incomplete_sample")
    elif any($groups[]; any(.members[]; running) and ((.driver | running) | not))
      then graph_unavailable("incomplete_sample")
    else [$groups[].driver | select(running)] as $active
    | if any($active[]; .rate <= 0 or .quantum <= 0) then graph_unavailable("incomplete_sample")
      else {status:(if ($active|length) > 0 then "observed" else "idle" end),
        reason:(if ($active|length) > 0 then "sampled" else "no_running_audio_driver" end),
        source:"pw-top batch",scope:"audio_drivers",
        rate_hz:(if ($active|length) == 1 then $active[0].rate else null end),
        quantum_frames:(if ($active|length) == 1 then $active[0].quantum else null end),
        drivers:[$active[] | {node_id:.id,rate_hz:.rate,quantum_frames:.quantum,
          theoretical_period_ms:(1000 * .quantum / .rate)}]} end end;
def audio_graph($dump; $text; $available):
  if $available | not then graph_unavailable("probe_unavailable")
  else (try top_rows($text) catch null) as $rows
    | if $rows == null then graph_unavailable("malformed_output")
      else try sampled_graph($dump; $rows) catch graph_unavailable("snapshot_mismatch") end end;
