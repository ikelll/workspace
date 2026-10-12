import QtQuick

Item {
    id: root
    property string label: ""
    property string description: ""
    property bool checked: false
    signal toggled(bool checked)

    implicitHeight: Math.max(24, copy.implicitHeight)
    implicitWidth: 240
    height: implicitHeight
    opacity: enabled ? 1 : 0.55

    activeFocusOnTab: true
    Accessible.role: Accessible.CheckBox
    Accessible.name: label
    Accessible.checked: checked
    Accessible.onToggleAction: root.flip()
    Keys.onSpacePressed: root.flip()
    Keys.onReturnPressed: root.flip()
    Keys.onEnterPressed: root.flip()

    function flip() { if (enabled) toggled(!checked) }

    Rectangle {
        id: box
        anchors.left: parent.left
        anchors.top: parent.top
        width: 22
        height: 22
        radius: 6
        color: root.checked ? Theme.accent : Theme.surface
        border.width: root.checked ? 0 : 1.5
        border.color: hover.containsMouse ? Theme.accent : Theme.border
        Behavior on color { ColorAnimation { duration: Theme.motion } }
        Icon { anchors.centerIn: parent; visible: root.checked; paths: Icons.check; size: 16; color: "white"; strokeWidth: 2.2 }
        Rectangle {
            anchors.fill: parent
            anchors.margins: -3
            radius: 9
            color: "transparent"
            border.width: 2
            border.color: Theme.accent
            visible: root.activeFocus
        }
    }
    Column {
        id: copy
        anchors.left: box.right
        anchors.leftMargin: 12
        anchors.right: parent.right
        spacing: 3
        Text {
            width: parent.width
            text: root.label
            color: Theme.ink
            font.family: Theme.font
            font.pixelSize: 14
            font.weight: Font.Medium
            wrapMode: Text.WordWrap
        }
        Text {
            width: parent.width
            visible: root.description.length > 0
            text: root.description
            color: Theme.muted
            font.family: Theme.font
            font.pixelSize: 12
            lineHeight: 1.25
            wrapMode: Text.WordWrap
        }
    }
    MouseArea {
        id: hover
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: root.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: { root.forceActiveFocus(); root.flip() }
    }
}
