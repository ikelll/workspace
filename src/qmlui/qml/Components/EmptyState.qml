import QtQuick
import QtQuick.Layouts
import "../Ui"

Rectangle {
    id: empty
    property var iconPaths: Icons.apps
    property string title: ""
    property string text: ""
    property alias actions: actionRow.data
    Layout.fillWidth: true
    implicitHeight: column.implicitHeight + 72
    radius: Theme.radius
    color: Theme.surface
    border.width: 1
    border.color: Theme.border
    ColumnLayout {
        id: column
        anchors.centerIn: parent
        width: Math.min(parent.width - 48, 460)
        spacing: 10
        Rectangle {
            Layout.alignment: Qt.AlignHCenter
            width: 64; height: 64; radius: 20
            color: Theme.soft
            Icon { anchors.centerIn: parent; paths: empty.iconPaths; size: 28; color: Theme.accent }
        }
        Text { Layout.fillWidth: true; Layout.topMargin: 6; text: empty.title; color: Theme.ink; font.family: Theme.font; font.pixelSize: 17; font.weight: Font.DemiBold; horizontalAlignment: Text.AlignHCenter; wrapMode: Text.WordWrap }
        Text { Layout.fillWidth: true; visible: empty.text.length > 0; text: empty.text; color: Theme.muted; font.family: Theme.font; font.pixelSize: 13; lineHeight: 1.35; horizontalAlignment: Text.AlignHCenter; wrapMode: Text.WordWrap }
        Row { id: actionRow; Layout.alignment: Qt.AlignHCenter; Layout.topMargin: 8; spacing: 10; visible: children.length > 0 }
    }
}
