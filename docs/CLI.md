# CLI and JSON API

`omarchy-studio --help`, `version`, `status`, and `doctor` are implemented. Each command accepts `--json`. `status` and `doctor` accept `--verbose`; `OMARCHY_STUDIO_DEBUG=1` has the same effect. Human output is English/ASCII with no ANSI colors, so `NO_COLOR` is inherently respected. No persistent logs are written. Errors and debug messages go to stderr; JSON stdout contains one document.

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | Report completed, including warnings or unknown checks; version/help succeeded |
| 1 | Internal execution/parsing error |
| 2 | Invalid command or arguments |
| 3 | Required runtime dependency missing |
| 4 | Doctor completed outside a detected Omarchy environment |
| 5 | Doctor completed with an observed service/configuration problem |

`status` returns 0 when collection completes, regardless of report health. `doctor` prioritizes code 5 over 4 when both apply. Machine consumers must read `status` and `checks`, even after exit 0; unknown realtime or measurements never imply readiness. Invocation failures may have no JSON document.

## Schema 1

See [the JSON Schema](../data/report.schema.json). `version` returns `schema_version`, `command` and `version`. Reports add:

- `status`: `ok`, `warning`, `error`, `unknown`, or `unsupported`. Unknown checks aggregate to a warning, never an all-clear.
- `system`: Omarchy package/runtime evidence, kernel, architecture, session environment, live Hyprland probe, user manager state. A package version is not a Git branch.
- `audio`: user service states, package versions, successful PipeWire snapshot reachability, JACK package evidence, clock configuration, and explicitly unavailable measurements.
- `hardware`: separate ALSA/PipeWire source status and normalized device inventory, joined by ALSA card number when available. No USB professionalism inference, serial numbers, raw properties or addresses.
- `midi`: ALSA sequencer endpoints with source/destination event flow, classification (`hardware` only with explicit ALSA card evidence), separate PipeWire MIDI ports and source status. Empty successfully enumerated arrays are not errors; unknown enumeration may include partial results.
- `realtime`: observed FIFO/RR threads of the managed PipeWire process, RTKit service evidence, invoking shell limits and an explicit `performance_verified:false`.
- `tools`: command availability booleans (availability does not prove correct operation).
- `checks`: stable `id`, status, English message and diagnostic hint. Consumers should use IDs/status, not parse messages.

Missing numeric/string observations are null; source states indicate whether empty inventories are known. Clock settings are not active driver rate/quantum. Zero forced settings mean no override and normalize to null. No latency or XRUN values are invented. Service state and graph reachability may disagree, for example with manually started services or a remote PipeWire connection.

Fields may be added within schema 1; consumers must ignore unknown fields and reject unsupported schema versions. Renames, removals and semantic changes require a new schema version. Snapshots are not atomic across subsystems. Probes have a two-second deadline plus at most one second for termination, so offline sessions cannot hang indefinitely; total time can include multiple probe deadlines.

Deferred: CPU/governor recommendations, detailed process limits, journal inspection with redaction, DAW inventory, plugin directory inventory, active driver sampling, routing validation and all configuration commands.
