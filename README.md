# Omarchy Studio

Make Omarchy understand music.

## What is Omarchy Studio?

An optional music-workstation layer for Omarchy, focused on integration, diagnostics and a musician-friendly experience. Simple by default. Powerful when needed. Transparent always.

Omarchy Studio is a community project and is not an official Omarchy component unless/until adopted by the Omarchy project.

## Why?

Musicians should spend their time making music, with clear information about their audio system and deliberate, reversible configuration when needed.

## Project status

Early development / experimental. The first milestone provides **read-only diagnostics**. It does not install applications, change audio settings, or certify a workstation for production use.

## Goals

Reliable system detection, a versioned JSON interface, useful troubleshooting, and native Omarchy shell integration.

## Non-goals

A distribution, DAW, replacement audio server, universal plugin manager, telemetry service, or automatic collection of Linux audio tweaks.

## Features

Bash CLI for version, status and doctor; PipeWire/WirePlumber service detection; ALSA and PipeWire audio inventory; MIDI endpoints; selected default input/output; bounded active driver sampling; conservative realtime observations. The CLI and panel distinguish audio in an idle state from unavailable sampling and label period duration as theoretical, never measured round-trip latency. Doctor separates operational findings from optional capabilities and unimplemented measurements. See [CLI documentation](docs/CLI.md) for exact semantics and limitations.

## Installation

Requires Bash 5+, GNU coreutils and jq. Clone the repository and run `./bin/omarchy-studio --help`. No installation or root privileges are needed. Optional probes use systemd, pacman, PipeWire tools, alsa-utils and procps-ng when available. Missing optional tools produce partial reports.

This Bash implementation uses the `feat/bash-foundation` branch of [carlosferrerdev/omarchy-studio](https://github.com/carlosferrerdev/omarchy-studio/tree/feat/bash-foundation). The default `main` branch preserves an earlier, separate Python implementation. Clone the intended branch explicitly:

```bash
git clone --branch feat/bash-foundation --single-branch https://github.com/carlosferrerdev/omarchy-studio.git
cd omarchy-studio
./bin/omarchy-studio --help
```

The shell plugin runs the CLI from its own checkout; a global command is optional. Its ID is `io.github.carlosferrerdev.omarchy-studio`, and the root manifest supports the official plugin manager. See [shell integration and installation](docs/PLUGIN.md) for installing this branch through a local checkout. Do not add symlinks inside the repository: Omarchy's plugin validator rejects them.

## Usage

```bash
./bin/omarchy-studio version
./bin/omarchy-studio status
./bin/omarchy-studio doctor --verbose
./bin/omarchy-studio status --json
./bin/omarchy-studio doctor --json
```

## Architecture

Small Bash probes → normalized JSON → CLI presentation / QML panel. QML never parses terminal text or owns system policy. See [architecture](docs/ARCHITECTURE.md), [audio model](docs/AUDIO_ARCHITECTURE.md), and [research](docs/RESEARCH.md).

## Development

See [local development and testing](docs/DEVELOPMENT.md). Public text, identifiers and commit messages are in English.

## Roadmap

See [ROADMAP.md](ROADMAP.md) and the [0.1.1 development plan](docs/PLAN-0.1.1.md). Diagnosis comes before configuration.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Small, tested improvements and reproducible hardware observations are welcome.

## Security

See [SECURITY.md](SECURITY.md). No telemetry, privileged background processes or remote code execution paths.

## License

[MIT](LICENSE).
