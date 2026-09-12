#!/bin/bash
studio_system() {
  local version='null' detected=false source=unavailable manager=unknown kernel='' architecture='' compositor=unknown
  local omarchy_path=${OMARCHY_PATH:-/usr/share/omarchy}
  version=$(studio_package omarchy-dev)
  if [[ $version == "null" ]]; then version=$(studio_package omarchy); fi
  if [[ $version != "null" ]]; then
    detected=true; source=pacman
  elif [[ -f "$omarchy_path/bin/omarchy" && -f "$omarchy_path/shell/shell.qml" ]]; then
    detected=true; source=runtime_files
  fi
  kernel=$(studio_run uname -r || true)
  architecture=$(studio_run uname -m || true)
  manager=$(studio_run systemctl --user is-system-running || true)
  case "$manager" in running | degraded | starting | maintenance | stopping | offline) ;; *) manager=unknown ;; esac
  if [[ -n ${HYPRLAND_INSTANCE_SIGNATURE:-} ]] && studio_run hyprctl -j version | jq -e 'type == "object" and (.version | type == "string")' >/dev/null 2>&1; then
    compositor=Hyprland
  fi
  jq -n --argjson detected "$detected" --argjson version "$version" --arg source "$source" \
    --arg kernel "$kernel" --arg arch "$architecture" --arg session "${XDG_SESSION_TYPE:-unknown}" \
    --arg compositor "$compositor" --arg manager "$manager" '
    {omarchy:{detected:$detected,version:$version,source:$source},kernel:($kernel|select(length>0)) // null,
     architecture:($arch|select(length>0)) // null,session:$session,compositor:$compositor,user_manager:$manager}'
}

studio_realtime() {
  local pid=$1 threads='' observed=null rtkit limits_rt limits_mem
  rtkit=$(studio_service rtkit-daemon.service system)
  limits_rt=$(ulimit -r)
  limits_mem=$(ulimit -l)
  if [[ $pid =~ ^[1-9][0-9]*$ ]] && threads=$(studio_run ps -L -p "$pid" -o cls=,rtprio=); then
    observed=$(jq -Rn --arg text "$threads" '
      [$text | split("\n")[] | select(test("^\\s*(TS|FF|RR|B|IDL|DLN|ISO)\\s+(-|[0-9]+)\\s*$"))]
      | if length == 0 then null else any(.[]; test("^\\s*(FF|RR)\\s+[1-9][0-9]*\\s*$")) end')
  fi
  jq -n --argjson observed "$observed" --argjson rtkit "$rtkit" --arg rt "$limits_rt" --arg mem "$limits_mem" '
    {pipewire_realtime_thread_observed:$observed,source:"ps -L scheduling class snapshot",rtkit:$rtkit,
     invoking_shell_limits:{rtprio:$rt,memlock_kib:$mem},performance_verified:false}'
}
