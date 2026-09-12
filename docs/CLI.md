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

## Schema 2

See [the JSON Schema](../data/report.schema.json). `version` returns `schema_version`, `command` and `version`. Reports add:

- `status`: `ok`, `warning`, `error`, `unknown`, or `unsupported`. Only checks with `category: "health"` affect this operational result. Precedence is error, unsupported, warning, unknown, ok. An unknown essential observation prevents an all-clear. Missing optional capabilities and unimplemented performance collectors do not manufacture warnings.
- `status_scope`: always `operational`. An ok result means the basic observations passed; it does not certify playback, recording, application routing or low-latency performance.
- `system`: Omarchy package/runtime evidence, kernel, architecture, session environment, live Hyprland probe, user manager state. A package version is not a Git branch.
- `audio`: user service states, package versions, successful PipeWire snapshot reachability, JACK package evidence, clock configuration, selected session defaults, bounded driver sampling, and explicitly unavailable latency/XRUN measurements.
- `hardware`: separate ALSA/PipeWire source status and normalized device inventory, joined by ALSA card number when available. No USB professionalism inference, serial numbers, raw properties or addresses.
- `midi`: ALSA sequencer endpoints with source/destination event flow, classification (`hardware` only with explicit ALSA card evidence), separate PipeWire MIDI ports and source status. Empty successfully enumerated arrays are not errors; unknown enumeration may include partial results.
- `realtime`: observed FIFO/RR threads of the managed PipeWire process, RTKit service evidence, invoking shell limits and an explicit `performance_verified:false`.
- `tools`: command availability booleans (availability does not prove correct operation).
- `checks`: stable `id`, `status`, `category` (`health`, `optional`, `performance`), `evidence` (`observed`, `unavailable`, `not_implemented`), English `message`, `impact` and diagnostic `hint`. Evidence describes the observation source, not a success verdict. Consumers should use IDs and structured fields, not parse messages.

`audio.defaults` resolves the session's default input/output using `default.audio.source` / `default.audio.sink` metadata and compatible nodes in the same snapshot. It never substitutes the remembered `default.configured.*` preference. Each endpoint has `status` (`selected`, `not_selected`, `unavailable`), a machine-readable `reason`, friendly `name`, ephemeral `node_id`, observed node `state`, `kind` (`device`, `virtual`, `monitor`, `unknown`) and optional `device_id`. A device association is not a certification of physical hardware. Internal node names can contain serial numbers and are not exported. Suspended selected nodes are normal while idle. No default input is an informational result; an explicitly selected input in error remains an operational problem. A DAW may bypass these defaults or use a previously assigned route.

### Migration from schema 1

Version 0.1.1 emits schema 2 for all JSON commands, including `version`. Schema 1 mixed optional capabilities and unimplemented measurements into aggregate health, making warnings unavoidable. Changing that meaning requires a schema version change. Consumers must now inspect operational status and optional/performance checks separately. The bundled QML reader accepts schema 2 and rejects older/unknown schemas. Update CLI and plugin together. The Omarchy plugin manifest is a separate contract and remains at `schemaVersion: 1`.

Missing numeric/string observations are null; source states indicate whether empty inventories are known. Clock settings are not active driver rate/quantum. Zero forced settings mean no override and normalize to null. No latency or XRUN values are invented. Service state and graph reachability may disagree, for example with manually started services or a remote PipeWire connection.

Fields may be added within schema 2; consumers must ignore unknown fields and reject unsupported schema versions. Renames, removals and semantic changes require a new schema version. Snapshots are not atomic across subsystems. Probes have a two-second deadline plus at most one second for termination, so offline sessions cannot hang indefinitely; total time can include multiple probe deadlines.

### Audio driver sample (additive schema 2 extension)

`audio.graph` retains `rate_hz`, `quantum_frames` and `source`. Added fields are `status` (`observed`, `idle`, `unavailable`), `reason`, `scope: "audio_drivers"` and `drivers`. Older schema 2 reports without these fields mean sampling unavailable. Source is `pw-top batch` for completed observed/idle samples and `unavailable` otherwise.

Each active driver exposes its ephemeral `node_id`, positive `rate_hz`, positive `quantum_frames` and `theoretical_period_ms` (`1000 * quantum_frames / rate_hz`). This period is not measured round-trip latency, hardware sample rate or an application latency guarantee. Summary rate/quantum are null unless exactly one active audio driver is observed; consumers must use the array for multiple graphs. Idle/unavailable samples have an empty driver array and null summaries. Clock configuration remains under `audio.clock_settings` and is never substituted for a missing measurement.

Reasons: `sampled`, `no_running_audio_driver`, `probe_unavailable`, `no_audio_nodes`, `incomplete_sample`, `malformed_output`, `snapshot_mismatch`. Reason text describes this sample, not a permanent hardware capability. `audio.graph` is a performance check and does not change aggregate operational health. `audio.measurement` continues to describe unimplemented XRUN and round-trip measurements.

Deferred: CPU/governor recommendations, detailed process limits, journal inspection with redaction, DAW inventory, plugin directory inventory, continuous graph monitoring, routing validation and all configuration commands.
