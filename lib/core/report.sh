#!/bin/bash
# shellcheck source=probe.sh
source "$STUDIO_ROOT/lib/core/probe.sh"
# shellcheck source=../system/detect.sh
source "$STUDIO_ROOT/lib/system/detect.sh"
# shellcheck source=../audio/detect.sh
source "$STUDIO_ROOT/lib/audio/detect.sh"
# shellcheck source=../hardware/detect.sh
source "$STUDIO_ROOT/lib/hardware/detect.sh"
# shellcheck source=../midi/detect.sh
source "$STUDIO_ROOT/lib/midi/detect.sh"

studio_report() {
  local report system audio hardware midi realtime pid tool tools='{}'
  system=$(studio_system)
  studio_audio_snapshot
  audio=$(studio_audio)
  hardware=$(studio_hardware)
  midi=$(studio_midi)
  pid=$(jq -r '.pipewire.main_pid // empty' <<<"$audio")
  realtime=$(studio_realtime "$pid")
  for tool in wpctl pw-cli pw-dump pw-top pw-metadata pw-link pactl aplay arecord aconnect lsusb udevadm ps systemctl pacman; do
    local available=false
    if studio_has "$tool"; then available=true; fi
    tools=$(jq --arg name "$tool" --argjson available "$available" '. + {($name):$available}' <<<"$tools")
  done
  report=$(jq -n --arg command "$1" --arg version "$STUDIO_VERSION" --argjson system "$system" \
    --argjson audio "$audio" --argjson hardware "$hardware" --argjson midi "$midi" \
    --argjson realtime "$realtime" --argjson tools "$tools" '
    {schema_version:2,command:$command,version:$version,status:"unknown",system:$system,audio:$audio,
     hardware:$hardware,midi:$midi,realtime:$realtime,tools:$tools,checks:[]}' |
    jq -f "$STUDIO_ROOT/lib/core/checks.jq")
  if [[ $2 == "true" ]]; then
    printf '%s\n' "$report"
  else
    jq -r -f "$STUDIO_ROOT/lib/core/render.jq" <<<"$report"
  fi
  # Status describes successful collection; doctor additionally signals findings.
  if [[ $1 == "doctor" ]]; then
    case "$(jq -r '.status' <<<"$report")" in
      error) return 5 ;;
      unsupported) return 4 ;;
    esac
  fi
}
