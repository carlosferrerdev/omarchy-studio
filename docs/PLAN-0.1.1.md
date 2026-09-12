# 0.1.1: useful operational diagnostics

## First increment

1. Resolve the selected default input and output from the existing read-only PipeWire snapshot. Match `default.audio.sink` / `default.audio.source` metadata to compatible nodes by their internal names, but expose only friendly labels and ephemeral IDs. Never substitute a remembered `default.configured.*` preference for the current default. Missing metadata, a missing node, no selection, and a suspended selected node are different observations.
2. Separate operational health, optional capabilities and performance observations. Unimplemented measurements must not manufacture a warning about the user's configuration. Unknown essential observations still prevent an all-clear. Healthy means the basic audio observations passed, never that a recording or performance is certified.
3. Publish schema 2 because the aggregate status semantics change. Update the CLI, JSON schema, QML reader and tests together; reject older schemas explicitly. Keep the Omarchy manifest at its own schema version 1.
4. Present default input/output before the full hardware inventory. Give actual findings an impact and a next step; show absent measurements as not measured. Retain manual refresh and no resident polling.

## Acceptance for this increment

- Synthetic tests cover defaults distinct from remembered preferences, malformed/string-encoded metadata, disconnected or ambiguous nodes, virtual devices, and idle/suspended nodes.
- Operational failures remain visible and preserve doctor exit codes. Missing optional tools and unimplemented measurements do not change operational health.
- Human and QML output never imply that default routing proves a DAW's route or that a microphone was tested.
- All lint, schema and fixture checks pass; the installed plugin is updated through Omarchy and visually reviewed on the current theme.
- No audio settings, streams or routes are changed by the feature.

## Validation record

The first increment is implemented in 0.1.1. Fixture suites cover selected defaults and operational aggregation alongside the existing CLI tests. Bash syntax, ShellCheck, shfmt, JSON Schema 2 validation, UI model tests and isolated Quickshell execution pass. The installed plugin was updated through Omarchy and its default-device panel and Doctor action were reviewed on the current desktop theme. No playback/capture stream or audio setting was changed.

During the schema transition, the running shell retained old QML components after a plugin rescan. An explicit `omarchy restart shell` loaded the updated reader and panel. This is an observed deployment limitation, not a reason to add automatic shell restarts to diagnostics. Full theme/orientation coverage and physical recording validation are still pending.

## Following increments

Active driver sampling is implemented in 0.1.2: a bounded sampler preserves multiple independent drivers and idle behavior. Synthetic fixtures cover active clocks and failure cases; passive live observation confirms idle handling. The CLI and QML distinguish these observations from clock settings. Never label `pw-top` ERR as a pure hardware XRUN counter; its documented semantics include errors. Round-trip latency remains unmeasured without an explicit measurement method.

Validation on 2026-09-12: all foundation checks, 23 sampler assertions, schema validation of active/idle reports, operational-health regression checks and UI model checks pass. The isolated Quickshell test consumes the real CLI, and Qt 6 lint completes with the previously documented upstream metadata warnings. The official plugin validator accepts 0.1.2. The installed status panel and Doctor action were reviewed after the official shell restart loaded the new components. No audio configuration or streams were changed. Active sampling under a sustained musical workload remains the next hardware validation task.

Then validate a musical workflow with available physical hardware: playback, user-authorized recording, interface reconnection, and MIDI source/destination enumeration. Hardware tests remain opt-in. Do not start recording, install a DAW or disconnect devices automatically. Convert observed failures into redacted synthetic fixtures.

Only after these observations are reliable should configuration work begin with a reviewable `setup --dry-run` plan and rollback design.

## Sources

[WirePlumber default-node policy](https://pipewire.pages.freedesktop.org/wireplumber/scripting/existing_scripts/default_nodes.html), [wpctl](https://pipewire.pages.freedesktop.org/wireplumber/man/wpctl.html), [PipeWire metadata](https://docs.pipewire.org/page_man_pw-metadata_1.html), and [pw-top](https://docs.pipewire.org/page_man_pw-top_1.html), consulted against installed PipeWire 1.6.8 / WirePlumber 0.5.17. The live snapshot confirms default metadata values decoded as objects; fixtures also cover JSON-encoded strings. The implementation adds no probes beyond the existing snapshot for default-device selection.
