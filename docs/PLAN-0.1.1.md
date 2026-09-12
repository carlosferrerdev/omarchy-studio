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

## Following increments

Active driver sampling comes next: research and test a bounded sampler of driver rate/quantum, preserving multiple independent drivers and idle behavior. Never label `pw-top` ERR as a pure hardware XRUN counter; its documented semantics include errors. Keep round-trip latency unmeasured without an explicit measurement method.

Then validate a musical workflow with available physical hardware: playback, user-authorized recording, interface reconnection, and MIDI source/destination enumeration. Hardware tests remain opt-in. Do not start recording, install a DAW or disconnect devices automatically. Convert observed failures into redacted synthetic fixtures.

Only after these observations are reliable should configuration work begin with a reviewable `setup --dry-run` plan and rollback design.

## Sources

[WirePlumber default-node policy](https://pipewire.pages.freedesktop.org/wireplumber/scripting/existing_scripts/default_nodes.html), [wpctl](https://pipewire.pages.freedesktop.org/wireplumber/man/wpctl.html), [PipeWire metadata](https://docs.pipewire.org/page_man_pw-metadata_1.html), and [pw-top](https://docs.pipewire.org/page_man_pw-top_1.html), consulted against installed PipeWire 1.6.8 / WirePlumber 0.5.17. The live snapshot confirms default metadata values decoded as objects; fixtures also cover JSON-encoded strings. The implementation adds no probes beyond the existing snapshot for default-device selection.
