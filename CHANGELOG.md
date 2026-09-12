# Changelog

## 0.1.1 — Unreleased

- Resolve selected input and output from PipeWire default metadata without exposing internal node names.
- Separate operational findings, optional capabilities and unverified/unimplemented performance measurements.
- Explain check impact and next steps; suspended selected devices are normal idle observations.
- **JSON API change:** schema 2 changes aggregate status semantics. CLI and plugin must be updated together; the Omarchy manifest schema stays at 1.

## 0.1.0 — Foundation

Initial experimental foundation: read-only diagnostics and versioned machine-readable reports. See the roadmap for deferred measurements and configuration features.

The initial shell panel includes a validated manifest under `io.github.carlosferrerdev.omarchy-studio` and consumes the checkout CLI without requiring a global command.
