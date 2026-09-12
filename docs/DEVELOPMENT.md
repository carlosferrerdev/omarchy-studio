# Development

Target: packaged Omarchy 4.0.3-1 and its current Quickshell plugin contract. The core can return partial diagnostic reports outside Omarchy; this is graceful failure behavior, not cross-distribution support.

Run directly from the checkout. `./scripts/check` runs Bash syntax checks, ShellCheck, shfmt, fixture tests and JSON validation. Development tools: ShellCheck, shfmt, Node (schema and UI model tests); no Bats dependency. Unit tests simulate commands and files. Live/system and hardware checks are opt-in and never alter audio settings. Do not run configuration tests against a real workstation in CI.

The plugin manifest is validated using `omarchy plugin validate .` on Omarchy. QML integration uses the installed `qs.Ui` and `qs.Commons` modules. Standalone qmllint may require the shell's import root and report missing upstream type metadata; runtime tests are a separate acceptance step. Do not restart or reconfigure a production shell just to run unit tests.

The repository does not configure PATH, shell rc files or global installation. A user may create an external symlink to `bin/omarchy-studio` in `~/.local/bin` after checking the destination does not exist and that directory is already on PATH. Do not create symlinks inside this plugin checkout.
