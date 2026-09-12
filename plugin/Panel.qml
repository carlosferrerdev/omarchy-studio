pragma ComponentBehavior: Bound
import QtQuick
import qs.Commons
import qs.Ui as Ui
import "Model.js" as Model

Column {
  id: root
  property var report: null
  property string failure: ""
  property bool busy: false
  signal refreshRequested()
  signal doctorRequested()
  spacing: Style.space(12)

  Text {
    text: "OMARCHY STUDIO"
    color: Color.foreground
    font.family: Style.font.family
    font.pixelSize: Style.font.body
    font.bold: true
  }
  Text {
    width: parent.width
    text: root.busy ? "Reading audio system..." : root.failure || Model.summary(root.report)
    textFormat: Text.PlainText
    wrapMode: Text.Wrap
    color: Color.foreground
    font.family: Style.font.family
    font.pixelSize: Style.font.body
  }
  Row {
    spacing: Style.space(8)
    Ui.Button {
      text: "Refresh"
      focusable: true
      enabled: !root.busy
      onClicked: root.refreshRequested()
    }
    Ui.Button {
      text: "Doctor"
      focusable: true
      enabled: !root.busy
      onClicked: root.doctorRequested()
    }
  }
  Repeater {
    model: Model.rows(root.report)
    delegate: Column {
      required property var modelData
      width: root.width
      spacing: Style.space(3)
      Text {
        text: parent.modelData.title
        textFormat: Text.PlainText
        color: Color.foreground
        opacity: 0.7
        font.family: Style.font.family
        font.pixelSize: Style.font.body
      }
      Text {
        width: parent.width
        text: parent.modelData.value
        textFormat: Text.PlainText
        wrapMode: Text.Wrap
        color: Color.foreground
        font.family: Style.font.family
        font.pixelSize: Style.font.body
      }
    }
  }
  Text {
    width: parent.width
    text: "Session defaults; your DAW may use another route. Period duration is not round-trip latency. Performance is not verified."
    wrapMode: Text.Wrap
    color: Color.foreground
    opacity: 0.7
    font.family: Style.font.family
    font.pixelSize: Style.font.body
  }
  Repeater {
    model: Model.findings(root.report)
    delegate: Text {
      required property var modelData
      width: root.width
      text: Model.findingText(modelData)
      textFormat: Text.PlainText
      wrapMode: Text.Wrap
      color: Color.foreground
      font.family: Style.font.family
      font.pixelSize: Style.font.body
    }
  }

}
