# Shell integration prototype

The UI prototype uses the installed Omarchy `qs.Ui.Panel`, `WidgetButton`, `KeyboardPanel` and shared theme tokens. Like the first-party audio plugin, it is a bar widget with a popup, so it needs only the `bar-widget` kind. `plugin/BarWidget.qml` is the intended entry point; `plugin/Panel.qml` contains presentation and `plugin/Model.js` handles the JSON view model.

The widget executes `../bin/omarchy-studio status --json` relative to its own source URL, using an argument array. It refreshes on opening or explicit user action, runs doctor through the same JSON API, reports failures, rejects unsupported schema versions and bounds a request with a watchdog. There is no service, polling loop, terminal-text parser, global command dependency or privileged action.

## Publication prerequisite

**A root manifest is intentionally pending confirmation of the repository's GitHub owner.** The initial directory had no Git remote, and no authenticated GitHub identity was available. A Git author name or a local Linux username is insufficient evidence of repository ownership. Do not publish a fabricated `io.github.*` identity or use `omarchy.*`.

Once the owner is confirmed, add a root `manifest.json` with `schemaVersion: 1`, the verified community ID, name `Omarchy Studio`, version `0.1.0`, actual author, `kinds: ["bar-widget"]`, `entryPoints.barWidget: "plugin/BarWidget.qml"`, and `barWidget` metadata (`displayName`, `category: "Audio"`, `allowMultiple: false`, `defaultSection: "right"`). Validate with `omarchy plugin validate .` before distribution. The current checkout is a functional CLI and UI prototype, **not yet an installable Omarchy plugin**.

After publication, installation uses `omarchy plugin add <actual-repository-url>`. This checkout has not been published, installed or enabled in the user's shell. The plugin manager does not install CLI dependencies; document and verify them before enabling the widget.

## Validation

`node tests/plugin-model.cjs` tests schema rejection and presentation data. `./tests/qml-smoke` is an opt-in integration test requiring the installed Omarchy shell and a reachable Wayland session. It creates a temporary Quickshell test context, keeps the popup closed, executes the actual CLI and verifies JSON consumption. It does not replace/restart the desktop shell or change shell configuration. Temporary test files are removed; Quickshell may write its normal runtime logs.

Use the **Qt 6** qmllint (`/usr/lib/qt6/bin/qmllint` on this Arch baseline); the unqualified `qmllint` executable belongs to Qt 5 here. Provide an import root containing `qs` linked to `$OMARCHY_PATH/shell` outside the plugin checkout. Qt 6 lint returns success with upstream metadata warnings for `Style.font` and `QProcess::ExitStatus`; the actual QML execution test covers those bindings. A visible popup review under the real host, including light/dark themes and bar orientations, remains an acceptance step after the manifest is finalized.
