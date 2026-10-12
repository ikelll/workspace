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

    Column {
        id: copy
        anchors.left: parent.left
        anchors.right: knob.left
        anchors.rightMargin: 16
        spacing: 4
        Text {
            width: parent.width
            text: root.label
            color: Theme.ink
            font.family: Theme.font
            font.pixelSize: 14
            font.weight: Font.DemiBold
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
    Rectangle {
        id: knob
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.topMargin: -2
        width: 40
        height: 24
        radius: 12
        color: root.checked ? Theme.accent : Theme.disabled
        Behavior on color { ColorAnimation { duration: Theme.motion } }
        Rectangle {
            x: root.checked ? 19 : 3
            y: 3
            width: 18
            height: 18
            radius: 9
            color: "white"
            Behavior on x { NumberAnimation { duration: Theme.motion; easing.type: Easing.OutCubic } }
        }
        Rectangle {
            anchors.fill: parent
            anchors.margins: -3
            radius: 15
            color: "transparent"
            border.width: 2
            border.color: Theme.accent
            visible: root.activeFocus
        }
    }
    MouseArea {
        anchors.fill: parent
        cursorShape: root.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: { root.forceActiveFocus(); root.flip() }
    }
}
