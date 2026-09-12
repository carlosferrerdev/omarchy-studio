#!/bin/bash
studio_alsa_cards() {
  jq -Rs '
    [split("\n")[] | capture("^\\s*(?<index>[0-9]+) \\[(?<id>[^]]+)\\]\\s*:\\s*(?<driver>.*?) - (?<name>.*)$")
     | {alsa_card:(.index|tonumber),name:.name,vendor:null,model:null,transport:null,pipewire_device:null,source:"proc_asound"}]'
}

studio_hardware() {
  local cards_file=${1:-/proc/asound/cards} alsa='[]' alsa_state=unknown devices='[]' pw_state=unknown
  if [[ -r $cards_file ]]; then
    if alsa=$(studio_alsa_cards <"$cards_file"); then
      if [[ $alsa != '[]' ]] || [[ $(<"$cards_file") == *"no soundcards"* ]]; then alsa_state=ok; fi
    fi
  fi
  if [[ $STUDIO_PW_REACHABLE == "true" ]] && devices=$(jq '
    def text: if type == "string" then gsub("[\\u0000-\\u001f\\u007f]"; "") else null end;
    [.[] | select(.type == "PipeWire:Interface:Device") | . as $device | .info.props
     | select(.["media.class"] == "Audio/Device")
     | {name:((.["device.description"]|text) // (.["device.product.name"]|text) // "Unknown audio device"),
        vendor:(.["device.vendor.name"]|text),model:(.["device.product.name"]|text),transport:(.["device.bus"]|text),
        alsa_card:((try (.["api.alsa.card"]|tonumber) catch null) // null),
        pipewire_device:$device.id,source:"pw-dump"}]' <<<"$STUDIO_PW_DUMP" 2>/dev/null); then
    pw_state=ok
  else
    devices='[]'
  fi
  jq -n --argjson alsa "$alsa" --argjson devices "$devices" --arg alsa_state "$alsa_state" --arg pw_state "$pw_state" '
    {alsa:{status:$alsa_state,cards:$alsa},pipewire_status:$pw_state,
     devices:($devices + [$alsa[] | . as $card | select(all($devices[]; .alsa_card != $card.alsa_card))])}'
}
