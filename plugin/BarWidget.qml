import QtQuick
import Quickshell.Io
import qs.Commons
import qs.Ui as Ui
import "Model.js" as Model

Ui.Panel {
  id: root
  manageIpc: false
  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  property var report: null
  property string failure: ""
  property string requestedCommand: "status"
  property bool timedOut: false
  readonly property bool busy: watchdog.running || probe.running
  readonly property string executable: decodeURIComponent(Qt.resolvedUrl("../bin/omarchy-studio").toString().replace(/^file:\/\//, ""))

  function refresh(command) {
    if (busy) return
    requestedCommand = command === "doctor" ? "doctor" : "status"
    report = null
    failure = ""
    timedOut = false
    watchdog.restart()
    probe.running = true
  }

  onOpenedChanged: if (opened) refresh("status")

  Process {
    id: probe
    command: [root.executable, root.requestedCommand, "--json"]
    stdout: StdioCollector {
      onStreamFinished: {
        if (root.timedOut) return
        try {
          root.report = Model.readReport(this.text)
        } catch (error) {
          root.report = null
          root.failure = "Could not read diagnostics. Run omarchy-studio doctor from this checkout."
        }
      }
    }
    onExited: function(exitCode, exitStatus) {
      watchdog.stop()
      if (root.timedOut) return
      if ([0, 4, 5].indexOf(exitCode) < 0 || exitStatus !== 0) {
        root.report = null
        root.failure = "Diagnostics failed. Check the CLI dependencies and run doctor in a terminal."
      }
    }
  }

  Timer {
    id: watchdog
    interval: 20000
    onTriggered: {
      root.timedOut = true
      probe.running = false
      root.report = null
      root.failure = "Diagnostics timed out. Check the user audio session with the CLI."
    }
  }

  Ui.WidgetButton {
    id: button
    bar: root.bar
    text: "Studio"
    tooltipText: "Omarchy Studio - audio diagnostics"
    textRotation: bar && bar.vertical ? -90 : 0
    onPressed: root.toggle()
  }

  Ui.KeyboardPanel {
    id: popup
    anchorItem: button
    owner: root
    bar: root.bar
    open: root.opened
    focusTarget: content
    contentWidth: fittedContentWidth(Style.space(380))
    contentHeight: fittedContentHeight(content.implicitHeight, Style.space(580))

    Flickable {
      anchors.fill: parent
      clip: true
      contentWidth: width
      contentHeight: content.implicitHeight
      boundsBehavior: Flickable.StopAtBounds
      Panel {
        id: content
        width: parent.width
        report: root.report
        failure: root.failure
        busy: root.busy
        onRefreshRequested: root.refresh("status")
        onDoctorRequested: root.refresh("doctor")
        Keys.onEscapePressed: root.close()
      }
    }
  }
}
