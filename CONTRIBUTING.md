# Contributing

Keep changes small and focused on current Omarchy. Research the installed contract and current official sources before changing integration behavior. Add fixture tests for probe failures and parser changes; do not require personal hardware in CI.

Use Bash 5, two spaces, quoted expansions, arrays for commands, `#!/bin/bash`, and no `eval`. Public documentation, comments, CLI text, branches and commit messages must be English. Use atomic Conventional Commits, for example `fix(audio): handle an unavailable user session`.

Run `./scripts/check` before submitting. Review the diff and staged files for secrets and personal dumps. Do not submit unredacted logs, serial numbers, project paths, audio or plugin licenses. See [development](docs/DEVELOPMENT.md) and [security](SECURITY.md).
