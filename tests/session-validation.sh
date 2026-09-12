#!/bin/bash
# Exercise the live-test wrapper with a synthetic CLI; never contact host audio.
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
scratch=$(mktemp -d)
trap 'rm -rf -- "$scratch"' EXIT
project=$scratch/project\ with\ spaces
mkdir -p "$project/bin" "$project/tests"
cp "$root/tests/hardware-smoke" "$root/tests/session-checks.jq" "$project/tests/"
export SESSION_TEST_REPORT=$scratch/report SESSION_TEST_MARKER=$scratch/invoked SESSION_TEST_EXIT=0
cat >"$project/bin/omarchy-studio" <<'STUB'
#!/bin/bash
[[ $* == 'doctor --json' ]] || exit 99
printf 'invoked\n' >>"$SESSION_TEST_MARKER"
cat "$SESSION_TEST_REPORT"
exit "$SESSION_TEST_EXIT"
STUB
chmod +x "$project/bin/omarchy-studio"
base=$(jq '. + {schema_version:2,command:"doctor",status:"ok",status_scope:"operational"}
  | .audio.graph = {status:"observed",drivers:[{node_id:20,rate_hz:48000,quantum_frames:128}]}
  | .hardware.devices = [{name:"PRIVATE-DEVICE",transport:"usb"}]
  | .midi = {status:"ok",ports:[{kind:"hardware",directions:["source"],name:"PRIVATE-CONTROLLER"}]}' \
  "$root/tests/fixtures/healthy-report.json")
printf '%s\n' "$base" >"$SESSION_TEST_REPORT"
run_case() {
  local expected=$1 description=$2 code=0 output
  shift 2
  output=$("$project/tests/hardware-smoke" "$@" 2>&1) || code=$?
  if [[ $code != "$expected" || $output == *PRIVATE* ]]; then
    printf 'not ok - %s (exit %s)\n' "$description" "$code" >&2
    exit 1
  fi
  printf 'ok - %s\n' "$description"
}
run_case 0 'help does not inspect the session' --help
run_case 2 'live inspection requires explicit opt-in'
run_case 2 'invalid expectations are rejected before probing' --live --expect-graph broken
run_case 2 'missing expectation argument is rejected' --live --expect-graph
run_case 2 'unknown options are rejected' --live --unknown
[[ ! -e $SESSION_TEST_MARKER ]]
run_case 0 'active graph with USB audio and a hardware MIDI source meets observations' --live --expect-graph active --require-usb-audio --require-midi-source
run_case 4 'an active graph does not satisfy the requested idle condition' --live --expect-graph idle
jq '.audio.graph = {status:"idle",drivers:[]}' <<<"$base" >"$SESSION_TEST_REPORT"
run_case 0 'idle is valid when requested' --live --expect-graph idle
run_case 4 'idle during an expected workload is inconclusive' --live --expect-graph active
jq '.audio.graph = {status:"unavailable",drivers:[]}' <<<"$base" >"$SESSION_TEST_REPORT"
run_case 4 'missing profiler evidence is inconclusive even without a specific expectation' --live
jq '.hardware.devices = [] | .midi.ports = [{kind:"virtual",directions:["source"]}]' <<<"$base" >"$SESSION_TEST_REPORT"
run_case 4 'virtual MIDI and missing USB audio do not satisfy hardware requirements' --live --require-usb-audio --require-midi-source
jq '.midi.status = "unknown"' <<<"$base" >"$SESSION_TEST_REPORT"
run_case 4 'partial MIDI enumeration does not confirm a controller' --live --require-midi-source
jq '.status = "error"' <<<"$base" >"$SESSION_TEST_REPORT"
SESSION_TEST_EXIT=5
run_case 1 'observed operational errors fail the session test' --live
SESSION_TEST_EXIT=4
jq '.status = "unsupported"' <<<"$base" >"$SESSION_TEST_REPORT"
run_case 4 'unsupported environments are inconclusive' --live
SESSION_TEST_EXIT=0
run_case 1 'inconsistent exit status is rejected' --live
for invalid in 'null' '{}' '{broken'; do
  printf '%s\n' "$invalid" >"$SESSION_TEST_REPORT"
  run_case 1 'invalid reports cannot pass or expose raw output' --live
done
jq '.audio.graph.drivers = []' <<<"$base" >"$SESSION_TEST_REPORT"
run_case 1 'active state without driver evidence is rejected' --live
printf '%s\n%s\n' "$base" "$base" >"$SESSION_TEST_REPORT"
run_case 1 'multiple reports are rejected instead of presenting contradictory results' --live
printf '%s\n' "$base" >"$SESSION_TEST_REPORT"
SESSION_TEST_EXIT=3
run_case 3 'missing CLI dependencies retain a distinct result' --live
SESSION_TEST_EXIT=1
run_case 1 'unexpected CLI failures are explicit' --live
SESSION_TEST_EXIT=124
run_case 4 'timed-out reports are discarded even with valid stdout' --live
SESSION_TEST_EXIT=137
run_case 4 'forced termination is inconclusive' --live
