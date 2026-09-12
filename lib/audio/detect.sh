#!/bin/bash
# shellcheck source=graph.sh
source "$STUDIO_ROOT/lib/audio/graph.sh"
# Keep a single private in-memory snapshot; never expose or persist raw props.
studio_audio_snapshot() {
  STUDIO_PW_DUMP='[]'
  STUDIO_PW_REACHABLE=false
  local output
  if output=$(studio_run pw-dump) && jq -e '
    type == "array" and all(.[]; type == "object" and (.type | type == "string")
      and (.id | type == "number" and . >= 0 and floor == .)
      and (.info == null or (.info | type == "object"))
      and (.info.props == null or (.info.props | type == "object"))
      and (.props == null or (.props | type == "object"))
      and (.metadata == null or (.metadata | type == "array" and all(.[]; type == "object" and (.key | type == "string") and (.subject | type == "number")))))
    and any(.[]; .type == "PipeWire:Interface:Core")' <<<"$output" >/dev/null 2>&1; then
    STUDIO_PW_DUMP=$output
    STUDIO_PW_REACHABLE=true
  else
    studio_debug 'PipeWire snapshot unavailable or malformed'
  fi
}

studio_audio() {
  local pipewire wireplumber pulse pw_version wp_version jack_version graph
  pipewire=$(studio_service pipewire.service)
  wireplumber=$(studio_service wireplumber.service)
  pulse=$(studio_service pipewire-pulse.service)
  pw_version=$(studio_package pipewire)
  wp_version=$(studio_package wireplumber)
  jack_version=$(studio_package pipewire-jack)
  graph=$(studio_audio_graph)
  jq -L "$STUDIO_ROOT/lib/audio" --argjson pw "$pipewire" --argjson wp "$wireplumber" --argjson pulse "$pulse" \
    --argjson pw_version "$pw_version" --argjson wp_version "$wp_version" --argjson jack_version "$jack_version" \
    --argjson reachable "$STUDIO_PW_REACHABLE" --argjson graph "$graph" '
    include "defaults";
    def positive: (try tonumber catch null) | if type == "number" and . > 0 and floor == . then . else null end;
    . as $dump | ([$dump[] | select(.type == "PipeWire:Interface:Metadata" and .props["metadata.name"] == "settings")
      | .metadata[]? | select(.subject == 0) | {key:.key,value:.value}] | from_entries) as $settings
    | {pipewire:($pw + {package_version:$pw_version,reachable:$reachable}),
       wireplumber:($wp + {package_version:$wp_version}),pulse:$pulse,
       jack:{package_version:$jack_version,compatibility:(if $jack_version != null then "installed" else "unknown" end),runtime_verified:false},
       clock_settings:{source:"pw-dump settings metadata",rate_hz:($settings["clock.rate"]|positive),
         quantum_frames:($settings["clock.quantum"]|positive),forced_rate_hz:($settings["clock.force-rate"]|positive),
         forced_quantum_frames:($settings["clock.force-quantum"]|positive)},
       defaults:default_devices($dump; $reachable),
       graph:$graph,
       latency:{measured_round_trip_ms:null},xruns:{count:null,status:"unavailable"}}' <<<"$STUDIO_PW_DUMP"
}
