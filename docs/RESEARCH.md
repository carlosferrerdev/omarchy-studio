# Research baseline

Researched on 2026-09-12, before implementation. No system configuration was changed.

## Omarchy

The inspected installation is the packaged **Omarchy 4.0.3-1**, at `$OMARCHY_PATH` (`/usr/share/omarchy` on packaged installations). It is not a Git checkout; there is no installed branch to report. GitHub's current default branch is **quattro**, inspected at `31bd80daa4613ffdee995ac27467fce5a2990806`. Do not confuse the older `master` branch with the current default. The installed contract is the compatibility target; upstream is moving.

Sources: [repository](https://github.com/basecamp/omarchy), [current AGENTS.md](https://github.com/basecamp/omarchy/blob/31bd80daa4613ffdee995ac27467fce5a2990806/AGENTS.md), [shell development](https://github.com/basecamp/omarchy/blob/quattro/agents/skills/shell-dev.md), [shell architecture](https://github.com/basecamp/omarchy/blob/quattro/docs/omarchy-shell.md), [shell plugins manual](https://github.com/basecamp/omarchy/blob/quattro/manual/32-shell-plugins.md), [first-party plugins](https://github.com/basecamp/omarchy/blob/quattro/shell/plugins/README.md), [testing](https://github.com/basecamp/omarchy/blob/quattro/docs/testing.md).

The installed `shell/README.md`, `shell/services/PluginRegistry.qml`, `bin/omarchy`, `bin/omarchy-version`, `bin/omarchy-plugin-validate`, `shell/Ui/` and audio/tailscale plugins were inspected. Omarchy dispatches command metadata to Bash executables, uses two-space indentation and `#!/bin/bash`. We retain a separate CLI rather than change its router. We use raw command detection deliberately: this diagnostic must survive missing Omarchy dependencies and incomplete sessions.

Plugins are repositories with a root `manifest.json`, `schemaVersion: 1`, namespaced ID, kinds and safe relative entry points. `omarchy.*` is reserved. No symlinks are allowed inside the plugin tree. The official installer clones and validates; it does not run install hooks. Third-party QML receives scoped host facades, not unrestricted service access. First-party audio uses a **bar-widget containing a popup panel**, not a separate `panel` kind; the initial Studio UI follows that composition. A resident service is unnecessary.

Quickshell 0.3.1 is installed. [Process documentation](https://quickshell.org/docs/v0.3.0/types/Quickshell.Io/Process/) specifies argument arrays and collected stdout. Local QML uses `qs.Ui` and `qs.Commons` for theme, typography, spacing and popup lifecycle. Upstream tests use Bash fixtures and Node for pure JavaScript; we choose those over adding Bats.

## Audio

Observed packages: PipeWire/Pulse/JACK 1.6.8, WirePlumber 0.5.17, alsa-utils 1.2.16. PipeWire, pipewire-pulse and WirePlumber user services are active. Kernel 7.2.3-arch1-3, x86_64, Wayland/Hyprland. `wpctl`, `pw-cli`, `pw-dump`, `pw-top`, `pw-metadata`, `pw-link`, `pactl`, `aplay`, `arecord`, `aconnect`, `lsusb`, and `udevadm` are available. This is a development observation, not a supported-version promise or a hardware certification.

- [PipeWire configuration](https://docs.pipewire.org/page_man_pipewire_conf_5.html): future changes belong in user drop-ins, never package files.
- [PipeWire metadata](https://docs.pipewire.org/page_man_pw-metadata_1.html): settings metadata describes clock configuration. It must not be advertised as an active driver's measured quantum.
- [pw-top](https://docs.pipewire.org/page_man_pw-top_1.html): driver quantum/rate and error statistics are observable, but followers have different semantics. Active graph measurement and XRUN counters are deferred until a reproducible sampler is tested. Unknown values remain null.
- [Realtime module](https://docs.pipewire.org/page_module_rt.html): direct scheduling permissions, the realtime portal and RTKit are distinct paths. RTKit absence alone is not failure. Inspect process threads; shell limits are only the invoking shell's limits.
- [WirePlumber ALSA](https://pipewire.pages.freedesktop.org/wireplumber/daemon/configuration/alsa.html): ALSA devices and the sequencer bridge are separate monitors. PipeWire `Audio/Device` objects provide structured hardware evidence; a USB camera is not an audio interface.
- [ALSA sequencer](https://www.alsa-project.org/alsa-doc/alsa-lib/seq.html) and [PipeWire MIDI](https://docs.pipewire.org/page_midi.html): enumerate ports, retain source/destination capabilities, distinguish virtual/system clients from hardware. Do not assume every kernel client is a physical controller. Development documentation may describe MIDI 1.7 behavior beyond installed 1.6.8.
- [PipeWire JACK](https://docs.pipewire.org/page_man_pipewire-jack_conf_5.html): JACK compatibility is library support, not proof a JACK application works or a standalone JACK server is running.
- [ArchWiki Professional audio](https://wiki.archlinux.org/title/Professional_audio), [PipeWire](https://wiki.archlinux.org/title/PipeWire), [realtime process management](https://wiki.archlinux.org/title/Realtime_process_management): reviewed indexed content; full-page retrieval encountered an anti-bot challenge. No automatic tuning is derived from inaccessible passages. Start with PipeWire and the ordinary kernel; measure before recommending changes.

## Decisions and uncertainties

Use Bash 5, GNU coreutils (bounded probes), and jq for correct JSON parsing/escaping. ShellCheck and shfmt are development dependencies only. Human output is plain English/ASCII and never requires color. Probes are read-only requests but may connect to sockets or wake an existing audio session; no streams, routes or settings are created intentionally. No raw dumps, journals, serial numbers or personal paths are persisted. Friendly endpoint labels can be user-defined; review reports before sharing.

Systemd service state and a successful PipeWire snapshot are separate observations. Missing tools, failed probes, malformed data and empty hardware inventories remain distinguishable. No readiness claim certifies low-latency or live-performance suitability. Realtime, active driver sampling, UMP details, routing validation, hardware capabilities and journal redaction require further work. Profiles, privilege escalation and rollback are future design work; no configuration commands ship in this milestone.
