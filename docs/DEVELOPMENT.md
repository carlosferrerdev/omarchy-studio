# Development

Target: packaged Omarchy 4.0.3-1 and its current Quickshell plugin contract. The core can return partial diagnostic reports outside Omarchy; this is graceful failure behavior, not cross-distribution support.

Run directly from the checkout. `./scripts/check` runs Bash syntax checks, ShellCheck, shfmt, fixture tests and JSON validation. Development tools: ShellCheck, shfmt, Node (UI model tests), Python with `jsonschema` (standards-compliant schema validation only); no Bats dependency. Python is not an application runtime. On Arch, development dependencies are `shellcheck shfmt nodejs python-jsonschema`. Unit tests simulate commands and files. Live/system and hardware checks are opt-in and never alter audio settings. Do not run configuration tests against a real workstation in CI.

Validate the root manifest using `omarchy plugin validate .` on Omarchy. The check runner requires the manifest, checks its identity and CLI version consistency, and invokes the official validator when Omarchy is available. See [plugin status and opt-in QML test](PLUGIN.md). QML integration uses the installed `qs.Ui` and `qs.Commons` modules. Standalone qmllint may require the shell's import root and report missing upstream type metadata; runtime tests are a separate acceptance step. Do not restart or reconfigure a production shell just to run unit tests.

The repository does not configure PATH, shell rc files or global installation. A user may create an external symlink to `bin/omarchy-studio` in `~/.local/bin` after checking the destination does not exist and that directory is already on PATH. Do not create symlinks inside this plugin checkout.

The next manual acceptance gate is [musical session validation](HARDWARE_VALIDATION.md).
`tests/hardware-smoke --live` checks one real diagnostic report against explicit
graph/hardware expectations. It never starts a workload. CI only exercises its
wrapper and predicates through `tests/session-validation.sh` with a synthetic CLI;
the real session runner is not invoked by `scripts/check`.
