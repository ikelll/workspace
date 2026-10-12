import QtQuick
import QtQuick.Layouts

Rectangle {
    id: notice
    property string title: ""
    property string text: ""
    property string kind: "info"
    property var iconPaths: kind === "warning" || kind === "danger" ? Icons.warning : Icons.info
    property alias actions: actionRow.data
    readonly property color tone: kind === "danger" ? Theme.danger : kind === "warning" ? Theme.warning : Theme.accent

    Layout.fillWidth: true
    implicitHeight: layout.implicitHeight + 40
    radius: Theme.radius
    color: kind === "danger" ? Theme.dangerSoft : kind === "warning" ? Theme.warningSoft : kind === "soft" ? Theme.soft : Theme.background

    ColumnLayout {
        id: layout
        anchors.fill: parent
        anchors.margins: 20
        spacing: 12
        RowLayout {
            Layout.fillWidth: true
            spacing: 12
            Icon { Layout.alignment: Qt.AlignTop; paths: notice.iconPaths; color: notice.tone; size: 20 }
            Column {
                Layout.fillWidth: true
                spacing: 6
                Text {
                    width: parent.width
                    visible: notice.title.length > 0
                    text: notice.title
                    color: Theme.ink
                    font.family: Theme.font
                    font.pixelSize: 14
                    font.weight: Font.DemiBold
                    wrapMode: Text.WordWrap
                }
                Text {
                    width: parent.width
                    visible: notice.text.length > 0
                    text: notice.text
                    color: Theme.muted
                    font.family: Theme.font
                    font.pixelSize: 12
                    lineHeight: 1.3
                    wrapMode: Text.WordWrap
                }
            }
        }
        Flow {
            id: actionRow
            Layout.fillWidth: true
            Layout.leftMargin: 32
            spacing: 8
            visible: children.length > 0
        }
    }
}
