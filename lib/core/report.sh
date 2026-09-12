#!/bin/bash
# Collectors are introduced independently; unavailable evidence stays explicit.
studio_report() {
  if [[ $2 == "true" ]]; then
    jq -n --arg command "$1" --arg version "$STUDIO_VERSION" \
      '{schema_version:1, command:$command, version:$version, status:"unknown", checks:[]}'
  else
    printf 'Omarchy Studio\n\nStatus: UNKNOWN\nDiagnostic collectors are not available yet.\n'
  fi
}
