#!/bin/bash
set -euo pipefail
STUDIO_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
# shellcheck source=../lib/audio/graph.sh
source "$STUDIO_ROOT/lib/audio/graph.sh"
fixture=$STUDIO_ROOT/tests/fixtures
STUDIO_PW_DUMP=$(<"$fixture/graph-nodes.json")
STUDIO_PW_REACHABLE=true
sample=$(<"$fixture/pw-top-active.txt")
probe_code=0
studio_run() {
  [[ $* == 'pw-top -b -n 2' ]] || exit 1
  printf '%s\n' "$sample"
  return "$probe_code"
}
check() {
  jq -e "$2" <<<"$1" >/dev/null || {
    printf 'not ok - %s\n' "$3" >&2
    exit 1
  }
  printf 'ok - %s\n' "$3"
}
report=$(studio_audio_graph)
check "$report" '.status == "observed" and .rate_hz == 48000 and .quantum_frames == 128 and (.drivers|length) == 1' 'last batch snapshot uses the active driver, not follower requests or video clocks'
check "$report" '.drivers[0].node_id == 20 and (.drivers[0].theoretical_period_ms - 2.6666666666666665 | fabs) < 0.00001' 'period duration is explicitly theoretical'
[[ $report != *PRIVATE* && $report != *errors* ]] || exit 1
original=$sample
sample=${original// + / = }
check "$(studio_audio_graph)" '.quantum_frames == 128' 'asynchronous followers do not become drivers'
sample=${original// + /}
check "$(studio_audio_graph)" '.rate_hz == null and .quantum_frames == null and (.drivers|length) == 2' 'independent drivers retain distinct clocks without a fictitious global rate'
sample=${original//R   20    128  48000/S   20    128  48000}
check "$(studio_audio_graph)" '.status == "unavailable"' 'a running follower under a suspended driver is an incomplete sample'
sample=${original//R   20    128  48000/R   20      0      0}
check "$(studio_audio_graph)" '.reason == "incomplete_sample" and .drivers == []' 'running state with no profiler clock remains unavailable'
for state in T t; do
  sample=${original//R   20/$state   20}
  check "$(studio_audio_graph)" '.status == "observed"' 'running transport states retain driver observations'
done
sample=$(<"$fixture/pw-top-idle.txt")
check "$(studio_audio_graph)" '.status == "idle" and .rate_hz == null and .drivers == []' 'idle and suspended audio never export stale clock values'
for state in C E '!'; do
  sample=${original//R   20/$state   20}
  check "$(studio_audio_graph)" '.status == "unavailable"' 'transitional and error states do not imply idle audio'
done
for sample in '' 'unexpected output' "${original%?????}"; do
  check "$(studio_audio_graph)" '.status == "unavailable"' 'missing, malformed and truncated samples never produce an all-clear'
done
sample=$original
probe_code=124
check "$(studio_audio_graph)" '.reason == "probe_unavailable"' 'even complete-looking stdout is discarded after timeout'
probe_code=127
check "$(studio_audio_graph)" '.reason == "probe_unavailable"' 'missing pw-top is optional'
probe_code=0
STUDIO_PW_REACHABLE=false
studio_run() { exit 99; }
check "$(studio_audio_graph)" '.reason == "probe_unavailable"' 'unreachable PipeWire skips the profiler probe entirely'
STUDIO_PW_REACHABLE=true
studio_run() { printf '%s\n' "$sample"; }
STUDIO_PW_DUMP=$(jq '(.[]|select(.id==20).info.props["node.name"])="replacement"' "$fixture/graph-nodes.json")
check "$(studio_audio_graph)" '.reason == "snapshot_mismatch"' 'reused IDs with changed names are rejected'
STUDIO_PW_DUMP=$(jq 'map(select(.id!=20))' "$fixture/graph-nodes.json")
check "$(studio_audio_graph)" '.reason == "snapshot_mismatch"' 'hotplug snapshot disagreement is unknown'
STUDIO_PW_DUMP=$(jq '(.[]|select(.id==20).info.props["media.class"])="Support/Node"' "$fixture/graph-nodes.json")
check "$(studio_audio_graph)" '.drivers[0].node_id == 20 and .rate_hz == 48000' 'a support driver can schedule an audio follower'
STUDIO_PW_DUMP=$(jq 'map(.info.props["media.class"]="Video/Source")' "$fixture/graph-nodes.json")
check "$(studio_audio_graph)" '.reason == "no_audio_nodes"' 'video-only inventory does not imply idle audio'
STUDIO_PW_DUMP=$(jq '. + [{id:999,type:"Other",padding:("x"*140000)}]' "$fixture/graph-nodes.json")
check "$(studio_audio_graph)" '.rate_hz == 48000' 'large private snapshots are streamed, not passed in argv'
