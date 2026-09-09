import QtQuick
import Quickshell.Io
import qs.Ui

BarWidget {
  id: root
  moduleName: "carlosferrerdev.omarchy-studio"
  property bool launchFailed: false

  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  function doctor() {
    if (launcher.running) return
    launchFailed = false
    // An argv array keeps spaces and shell metacharacters in the checkout safe.
    launcher.command = ["xdg-terminal-exec", "--title=Omarchy Studio", "-e", "bash",
      decodeURIComponent(Qt.resolvedUrl("bin/studio-doctor-terminal").toString().replace(/^file:\/\//, ""))]
    startWatch.restart()
    launcher.running = true
  }

  WidgetButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    text: root.launchFailed ? "Studio !" : (root.vertical ? "ST" : "Studio")
    tooltipText: root.launchFailed
      ? "Terminal launch failed. Run bin/omarchy-studio doctor from the plugin directory."
      : "Studio Doctor — inspect this computer for music production"
    onPressed: function(button) { if (button === Qt.LeftButton) root.doctor() }
  }

  Process {
    id: launcher
    onStarted: startWatch.stop()
    onExited: function(exitCode) { root.launchFailed = exitCode !== 0 }
  }

  Timer {
    id: startWatch
    interval: 2000
    onTriggered: root.launchFailed = true
  }
}
