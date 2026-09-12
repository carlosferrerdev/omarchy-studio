#!/bin/bash
# aconnect calls readable/source ports "input"; retain event-flow terminology.
studio_midi_parse() {
  local direction=$1
  jq -Rs --arg direction "$direction" '
    reduce (split("\n")[]) as $line ({client:null,ports:[]};
      if ($line | test("^client [0-9]+:")) then
        .client = (try ($line | capture("^client (?<id>[0-9]+): '\''(?<name>.*)'\'' \\[(?<details>.*)\\]$")) catch null)
      elif .client != null and ($line | test("^\\s+[0-9]+ '\''")) then
        (try ($line | capture("^\\s+(?<port>[0-9]+) '\''(?<name>.*)'\''\\s*$")) catch null) as $port
        | if $port == null then . else
          .ports += [{client:(.client.id|tonumber),port:($port.port|tonumber),
            client_name:.client.name,name:($port.name|sub("\\s+$";"")),
            kind:(if .client.id == "0" or (.client.id == "14" and .client.name == "Midi Through") then "virtual"
                  elif (.client.details|test("(^|,)card=[0-9]+(,|$)")) then "hardware" else "unknown" end),
            directions:[$direction]}] end
      else . end) | .ports'
}

studio_midi() {
  local direction output parsed ports='[]' state=ok pipewire_ports='[]'
  for direction in source destination; do
    local flag=-i
    if [[ $direction == "destination" ]]; then flag=-o; fi
    if output=$(studio_run aconnect "$flag") && { [[ -z $output ]] || [[ $output == client\ * ]]; } \
      && parsed=$(studio_midi_parse "$direction" <<<"$output" 2>/dev/null); then
      ports=$(jq -n --argjson old "$ports" --argjson new "$parsed" '$old + $new')
    else
      state=unknown
    fi
  done
  if [[ $STUDIO_PW_REACHABLE == "true" ]]; then
    pipewire_ports=$(jq '[.[] | select(.type == "PipeWire:Interface:Port") | . as $port | .info.props
      | select(.["format.dsp"]? | type == "string" and test("midi";"i"))
      | {id:$port.id,name:(.["port.name"] // "Unknown MIDI port"),
         direction:(if .["port.direction"] == "out" then "source" elif .["port.direction"] == "in" then "destination" else "unknown" end)}]' \
      <<<"$STUDIO_PW_DUMP" 2>/dev/null) || pipewire_ports='[]'
  fi
  jq -n --arg status "$state" --argjson ports "$ports" --argjson pw "$pipewire_ports" --argjson reachable "$STUDIO_PW_REACHABLE" '
    {status:$status,source:"aconnect",ports:($ports | group_by([.client,.port]) | map(.[0] + {directions:(map(.directions[])|unique)})),
     pipewire_status:(if $reachable then "ok" else "unknown" end),pipewire_ports:$pw,routing_verified:false}'
}
