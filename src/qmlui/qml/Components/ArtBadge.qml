import QtQuick
import "../Ui"

Rectangle {
    id: badge
    property string text: ""
    property string kind: "neutral"
    readonly property color dot: kind === "success" ? "#11b981" : kind === "warning" ? "#f5b91b" : kind === "danger" ? "#ef4444"
                               : kind === "accent" ? "#8b5cf6" : "#9da8b7"
    implicitHeight: 26
    implicitWidth: row.implicitWidth + 20
    radius: 13
    color: Qt.rgba(1, 1, 1, 0.84)
    Row {
        id: row
        anchors.centerIn: parent
        spacing: 7
        Rectangle { anchors.verticalCenter: parent.verticalCenter; width: 7; height: 7; radius: 3.5; color: badge.dot }
        Text { anchors.verticalCenter: parent.verticalCenter; text: badge.text; color: "#314053"; font.family: Theme.font; font.pixelSize: 12; font.weight: Font.Medium }
    }
}
