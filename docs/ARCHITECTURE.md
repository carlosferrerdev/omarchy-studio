# Architecture

`bin/omarchy-studio` owns routing and exit codes. `lib/core/` owns bounded execution, report assembly and rendering. `lib/system/`, `lib/audio/`, `lib/hardware/` and `lib/midi/` collect narrow observations. `data/` contains the JSON schema. `plugin/` is a thin Omarchy popup consuming the same API. Tests use synthetic fixtures, never a required physical interface.

Bash is the system glue; jq is the only additional required runtime for reports. This avoids fragile hand-built JSON and a second application runtime. Modules expose explicit functions, not executable configuration. No `eval`, downloaded code, persistent daemon, or automatic filesystem scans.

The CLI is located relative to its resolved executable, so it can run from a checkout or an external symlink. QML uses a relative URL to that checkout's executable and an argument array. No global installation is required.

Future configuration will use versioned declarative data, per-file ownership records, conflict detection, backups and exact restoration. XDG roots are `${XDG_CONFIG_HOME:-$HOME/.config}/omarchy-studio`, `${XDG_STATE_HOME:-$HOME/.local/state}/omarchy-studio`, `${XDG_CACHE_HOME:-$HOME/.cache}/omarchy-studio`, and `${XDG_DATA_HOME:-$HOME/.local/share}/omarchy-studio`. The read-only milestone creates none of these directories.

Technical profiles and application/persona bundles are separate concepts. Studio Mode must restore captured state, including Omarchy idle/notification state through supported APIs. These are design constraints, not implemented commands.
