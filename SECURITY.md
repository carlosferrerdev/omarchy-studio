# Security

This experimental project currently provides local read-only diagnostics. It never requests root, modifies audio configuration, starts recording, downloads code at runtime or sends telemetry. Omarchy shell plugins run with the user's privileges inside a shared process; review plugin code before enabling it.

Reports allowlist useful fields and omit serial numbers, raw dumps and personal paths. Friendly device and MIDI labels may be user-assigned; review output before sharing it. Verbose logging reports probe names and failure categories, not raw command output.

Do not post credentials or sensitive diagnostics in public issues. Until a private reporting channel is configured on the published repository, report a non-sensitive request for private contact to the maintainer. Only the current development version receives fixes; no production support guarantee is made.
