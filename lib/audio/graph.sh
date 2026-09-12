#!/bin/bash
studio_audio_graph() {
  local output='' available=false
  # Two finite iterations discard the initial unpopulated view. A timeout is failure,
  # even if stdout contains a partial sample. No streams or monitoring daemon are created.
  if [[ $STUDIO_PW_REACHABLE == true ]] && output=$(studio_run pw-top -b -n 2); then
    available=true
  fi
  # Both potentially large private snapshots travel over stdin, never argv or disk.
  {
    printf '%s\n' "$STUDIO_PW_DUMP"
    jq -Rs . <<<"$output"
  } |
    jq -s -L "$STUDIO_ROOT/lib/audio" --argjson available "$available" \
      'include "graph"; audio_graph(.[0]; .[1]; $available)'
}
