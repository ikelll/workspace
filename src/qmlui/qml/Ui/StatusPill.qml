import QtQuick

Rectangle {
    id: pill
    property string text: ""
    property string kind: "neutral"
    readonly property color tone: kind === "success" ? Theme.success : kind === "accent" ? Theme.accent
                                : kind === "danger" ? Theme.danger : kind === "warning" ? Theme.warning : Theme.muted
    implicitHeight: 34
    implicitWidth: row.implicitWidth + 28
    radius: Theme.radiusSmall
    color: kind === "success" ? Theme.successSoft : kind === "accent" ? Theme.soft : kind === "danger" ? Theme.dangerSoft
         : kind === "warning" ? Theme.warningSoft : Theme.background
    Row {
        id: row
        anchors.centerIn: parent
        spacing: 9
        Rectangle { anchors.verticalCenter: parent.verticalCenter; width: 6; height: 6; radius: 3; color: pill.tone }
        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: pill.text
            color: pill.kind === "neutral" ? Theme.muted : pill.tone
            font.family: Theme.font
            font.pixelSize: 12
        }
    }
}
