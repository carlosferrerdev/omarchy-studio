# Changelog

## 0.1.2 — Unreleased

- Add an opt-in live session observation runner and a manual hardware validation guide; CI uses a synthetic CLI only.
- Sample active audio driver rate/quantum with a bounded, read-only PipeWire profiler query.
- Preserve multiple independent drivers; distinguish idle audio from unavailable sampling.
- Show observations in the CLI and shell panel with explicitly theoretical period duration.
- Add optional schema 2 graph fields, conservative snapshot correlation and synthetic sampler coverage.
- Keep XRUN counts and round-trip latency unmeasured. No audio streams, routes or configuration are changed.

## 0.1.1 — Unreleased

- Resolve selected input and output from PipeWire default metadata without exposing internal node names.
- Separate operational findings, optional capabilities and unverified/unimplemented performance measurements.
- Show default input/output first in the panel and keep Refresh/Doctor actions near the summary.
- Explain check impact and next steps; suspended selected devices are normal idle observations.
- **JSON API change:** schema 2 changes aggregate status semantics. CLI and plugin must be updated together; the Omarchy manifest schema stays at 1.

## 0.1.0 — Foundation

Initial experimental foundation: read-only diagnostics and versioned machine-readable reports. See the roadmap for deferred measurements and configuration features.

The initial shell panel includes a validated manifest under `io.github.carlosferrerdev.omarchy-studio` and consumes the checkout CLI without requiring a global command.
