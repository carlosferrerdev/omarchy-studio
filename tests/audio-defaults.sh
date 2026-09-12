#!/bin/bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
fixture=$root/tests/fixtures/defaults.json
collect() { jq -L "$root/lib/audio" 'include "defaults"; default_devices(.; true)'; }
check() {
  jq -e "$2" <<<"$1" >/dev/null || {
    printf 'not ok - %s\n' "$3" >&2
    exit 1
  }
  printf 'ok - %s\n' "$3"
}
result=$(collect <"$fixture")
check "$result" '.output.name == "Studio Output" and .input.name == "Studio Input" and .output.node_id == 20' 'resolve current defaults, including JSON-encoded values, without using remembered preferences'
check "$result" '.output.status == "selected" and .output.state == "suspended" and .input.state == "idle"' 'selected nodes do not have to be running'
[[ $result != *PRIVATE-SERIAL* ]] || exit 1
check "$(jq 'map(select(.id != 20))' "$fixture" | collect)" '.output.reason == "node_not_found" and .output.name == null' 'disconnected selected node is unavailable'
check "$(jq 'map(select(.id != 1))' "$fixture" | collect)" '.output.reason == "metadata_unavailable"' 'missing metadata is not a known empty selection'
check "$(jq '(.[] | select(.id == 1).metadata) = []' "$fixture" | collect)" '.output.status == "not_selected" and .input.status == "not_selected"' 'empty metadata explicitly means no selected defaults'
check "$(jq '. + [.[] | select(.id == 20) | .id = 25]' "$fixture" | collect)" '.output.reason == "ambiguous_node"' 'duplicate node names never resolve arbitrarily'
check "$(jq '(.[] | select(.id == 1).metadata) += [.[] | select(.id == 1).metadata[0]]' "$fixture" | collect)" '.output.reason == "ambiguous_default"' 'duplicate metadata keys remain unknown'
for value in 'null' 'false' '7' '[]' '{}' '"broken JSON"' '{"name":5}'; do
  check "$(jq --argjson value "$value" '(.[] | select(.id == 1).metadata[0].value) = $value' "$fixture" | collect)" '.output.reason == "malformed_default"' 'malformed default value does not crash or invent a device'
done
check "$(jq '(.[] | select(.id == 20).info.props["node.virtual"]) = true' "$fixture" | collect)" '.output.kind == "virtual"' 'virtual output is not presented as a physical interface'
check "$(jq '(.[] | select(.id == 21).info.props["device.class"]) = "monitor"' "$fixture" | collect)" '.input.kind == "monitor"' 'an explicit monitor source is distinguished from a microphone'
check "$(jq '(.[] | select(.id == 20).info.props["media.class"]) = "Video/Source"' "$fixture" | collect)" '.output.reason == "node_not_found"' 'default names only resolve to compatible audio nodes'
check "$(jq '(.[] | select(.id == 20).info.props) |= del(.["node.description"])' "$fixture" | collect)" '.output.name == "Selected output"' 'internal node names are not leaked as label fallbacks'
check "$(jq -L "$root/lib/audio" 'include "defaults"; default_devices(.; false)' "$fixture")" '.output.reason == "probe_unavailable" and .input.status == "unavailable"' 'failed snapshots retain unknown defaults'
