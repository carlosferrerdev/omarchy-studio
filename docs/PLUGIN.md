# Shell integration prototype

The UI prototype uses the installed Omarchy `qs.Ui.Panel`, `WidgetButton`, `KeyboardPanel` and shared theme tokens. Like the first-party audio plugin, it is a bar widget with a popup, so it needs only the `bar-widget` kind. `plugin/BarWidget.qml` is the intended entry point; `plugin/Panel.qml` contains presentation and `plugin/Model.js` handles the JSON view model.

The widget consumes CLI JSON schema 2; the manifest uses Omarchy schema 1. The widget executes `../bin/omarchy-studio status --json` relative to its own source URL, using an argument array. It refreshes on opening or explicit user action, runs doctor through the same JSON API, reports failures, rejects unsupported schema versions and bounds a request with a watchdog. There is no service, polling loop, terminal-text parser, global command dependency or privileged action.

## Identity and installation

The maintainer confirmed the personal GitHub account [carlosferrerdev](https://github.com/carlosferrerdev), and the public GitHub API verified that login. The plugin ID is **`io.github.carlosferrerdev.omarchy-studio`**, outside the reserved `omarchy.*` namespace.

The root `manifest.json` declares schema 1, version `0.1.1`, the bar widget entry point, and placement on the right. It passes the installed Omarchy manifest validator. Run `omarchy plugin validate .` before distribution.

After publication, installation uses `omarchy plugin add <actual-repository-url>`, followed by `omarchy plugin enable io.github.carlosferrerdev.omarchy-studio` after review. The repository URL is not assumed from the plugin ID. Publication is separate from local installation. A committed local checkout can also be installed with `omarchy plugin add /absolute/path/to/checkout --enable`; its installed copy follows that local Git origin. The plugin manager does not install CLI dependencies; document and verify them before enabling the widget.

## Validation

`node tests/plugin-model.cjs` tests schema rejection and presentation data. `./tests/qml-smoke` is an opt-in integration test requiring the installed Omarchy shell and a reachable Wayland session. It creates a temporary Quickshell test context, keeps the popup closed, executes the actual CLI and verifies JSON consumption. It does not replace/restart the desktop shell or change shell configuration. Temporary test files are removed; Quickshell may write its normal runtime logs.

Use the **Qt 6** qmllint (`/usr/lib/qt6/bin/qmllint` on this Arch baseline); the unqualified `qmllint` executable belongs to Qt 5 here. Provide an import root containing `qs` linked to `$OMARCHY_PATH/shell` outside the plugin checkout. Qt 6 lint returns success with upstream metadata warnings for `Style.font` and `QProcess::ExitStatus`; the actual QML execution test covers those bindings. The 0.1.1 status panel and Doctor action have been reviewed under the real host on the current theme. Comprehensive light/dark and bar-orientation coverage remains pending.

## Updating from 0.1.0

Update the installed checkout through `omarchy plugin update io.github.carlosferrerdev.omarchy-studio`. This updates CLI and QML together to schema 2. On the tested Omarchy release, a rescan retained old QML components during this upgrade; if the popup rejects the new report despite the CLI working, run `omarchy restart shell` to reload it. Studio does not restart the shell automatically. The plugin uses its installed checkout, so editing the source repository alone does not update the running CLI.
