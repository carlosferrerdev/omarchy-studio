#!/bin/bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
fixture=$root/tests/fixtures/healthy-report.json
assess() { jq -f "$root/lib/core/checks.jq"; }
check() {
  jq -e "$2" <<<"$1" >/dev/null || {
    printf 'not ok - %s\n' "$3" >&2
    exit 1
  }
  printf 'ok - %s\n' "$3"
}
report=$(assess <"$fixture")
check "$report" '.status == "ok" and .status_scope == "operational"' 'missing optional JACK/MIDI and unimplemented measurements do not manufacture warnings'
check "$report" '[.checks[]|select(.evidence == "not_implemented")]|length == 1' 'unimplemented collectors are explicitly labeled'
check "$report" '[.checks[]|select(.id == "performance.realtime")][0].evidence == "unavailable"' 'missing scheduling evidence is unavailable, not unimplemented'
check "$(jq '.realtime.pipewire_realtime_thread_observed = false' "$fixture" | assess)" '.status == "ok" and ([.checks[]|select(.id == "performance.realtime")][0].evidence == "observed")' 'observed ordinary threads do not become a scheduling configuration error'
check "$(jq '.audio.wireplumber.state = "inactive"' "$fixture" | assess)" '.status == "error"' 'inactive WirePlumber remains an operational error'
check "$(jq '.audio.pipewire |= {reachable:false,state:"inactive"}' "$fixture" | assess)" '.status == "error"' 'unreachable inactive PipeWire remains an operational error'
check "$(jq '.audio.pipewire |= {reachable:false,state:"unknown"}' "$fixture" | assess)" '.status == "unknown"' 'unknown essential probes prevent an all-clear'
check "$(jq '.system.user_manager = "unknown"' "$fixture" | assess)" '.status == "unknown"' 'missing user-session evidence prevents an all-clear'
check "$(jq '.audio.pulse.state = "inactive"' "$fixture" | assess)" '.status == "warning"' 'missing desktop audio compatibility remains a real warning'
check "$(jq '.audio.defaults.output.status = "not_selected"' "$fixture" | assess)" '.status == "warning"' 'a missing default output deserves attention'
check "$(jq '.audio.defaults.output.state = "error"' "$fixture" | assess)" '.status == "error"' 'selected output in error is not available'
check "$(jq '.audio.defaults.input = {status:"selected",state:"error"}' "$fixture" | assess)" '.status == "error"' 'a selected input in error remains visible'
check "$(jq '.audio.defaults.output = {status:"unavailable",reason:"node_not_found"}' "$fixture" | assess)" '.status == "unknown"' 'a stale selected output is not silently healthy'
check "$(jq '.system.omarchy.detected = false' "$fixture" | assess)" '.status == "unsupported"' 'unsupported environments remain explicit'
check "$(jq '.system.omarchy.detected = false | .audio.wireplumber.state = "failed"' "$fixture" | assess)" '.status == "error"' 'observed failure retains precedence over unsupported environment'
check "$report" 'all(.checks[]; (.impact|length)>0 and (.hint|length)>0)' 'checks explain impact and next steps'
for graph_status in observed idle unavailable; do
  check "$(jq --arg state "$graph_status" '.audio.graph.status = $state' "$fixture" | assess)" '.status == "ok"' 'sampling availability does not change operational health'
done
check "$(jq '.audio.graph.status = "observed"' "$fixture" | assess)" 'any(.checks[]; .id == "audio.graph" and .status == "ok" and .evidence == "observed")' 'driver observations are distinct from unimplemented latency measurements'
