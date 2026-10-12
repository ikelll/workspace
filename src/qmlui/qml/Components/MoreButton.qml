import QtQuick
import QtQuick.Controls
import "../Ui"

Item {
    id: root
    property real size: 35
    signal clicked()
    width: size
    height: size
    activeFocusOnTab: true
    Accessible.role: Accessible.Button
    Accessible.name: qsTr("More")
    Keys.onSpacePressed: root.clicked()
    Keys.onReturnPressed: root.clicked()
    Rectangle {
        anchors.fill: parent
        radius: 8
        color: hover.containsMouse ? (Theme.dark ? "#273449" : "#f3f6fa") : Qt.rgba(0.95, 0.96, 0.98, 0)
        border.width: root.activeFocus ? 2 : 0
        border.color: Theme.accent
        Behavior on color { ColorAnimation { duration: 120 } }
    }
    Row {
        anchors.centerIn: parent
        spacing: 4
        Repeater { model: 3; delegate: Rectangle { width: 4; height: 4; radius: 2; color: hover.containsMouse ? Theme.accent : "#65758a" } }
    }
    MouseArea { id: hover; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.clicked() }
    ToolTip.visible: hover.containsMouse
    ToolTip.text: qsTr("Transport and actions")
    ToolTip.delay: 600
}
