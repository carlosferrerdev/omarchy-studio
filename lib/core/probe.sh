#!/bin/bash
studio_has() { command -v "$1" >/dev/null 2>&1; }

studio_debug() {
  if [[ ${verbose:-0} == "1" ]]; then printf 'debug: %s\n' "$*" >&2; fi
}

# Never print external stderr or full argv: it may contain personal information.
studio_run() {
  local result
  if ! studio_has "$1"; then
    studio_debug "$1 unavailable"
    return 127
  fi
  if timeout --signal=TERM --kill-after=1s 2s "$@" 2>/dev/null; then
    return 0
  else
    result=$?
    studio_debug "$1 probe failed (exit $result)"
    return "$result"
  fi
}

studio_package() {
  local output
  if ! studio_has pacman; then
    printf 'null\n'
    return
  fi
  if output=$(studio_run pacman -Q "$1"); then
    jq -Rn --arg package "$1" --arg output "$output" \
      '$output | split(" ") | if length == 2 and .[0] == $package and (.[1] | test("^[^\\s]+$")) then .[1] else null end'
  else
    printf 'null\n'
  fi
}

studio_service() {
  local output=''
  local -a scope=(--user)
  if [[ ${2:-user} == "system" ]]; then scope=(); fi
  if output=$(studio_run systemctl "${scope[@]}" show "$1" --property=LoadState,ActiveState,SubState,MainPID); then
    jq -Rn --arg output "$output" '
      ($output | split("\n") | map(select(test("^[A-Za-z]+=")) | capture("^(?<key>[^=]+)=(?<value>.*)$")) | from_entries) as $p
      | {state: (if (["active","inactive","failed","activating","deactivating","reloading"] | index($p.ActiveState)) != null then $p.ActiveState else "unknown" end),
         load_state: ($p.LoadState // "unknown"),
         main_pid: ((try ($p.MainPID | tonumber | select(. > 0 and floor == .)) catch null) // null)}
      | .main_pid //= null'
  else
    printf '{"state":"unknown","load_state":"unknown","main_pid":null}\n'
  fi
}
