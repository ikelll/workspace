import QtQuick
import QtQuick.Controls
import "../Ui"

Item {
    id: root
    property bool checked: false
    property real size: 35
    signal toggled()
    width: size
    height: size
    activeFocusOnTab: true
    Accessible.role: Accessible.CheckBox
    Accessible.name: qsTr("Add to favorites")
    Accessible.checked: checked
    Keys.onSpacePressed: root.toggled()
    Keys.onReturnPressed: root.toggled()
    Rectangle {
        anchors.fill: parent
        radius: 8
        color: hover.containsMouse ? (Theme.dark ? "#273449" : "#f3f6fa") : Qt.rgba(0.95, 0.96, 0.98, 0)
        border.width: root.activeFocus ? 2 : 0
        border.color: Theme.accent
        Behavior on color { ColorAnimation { duration: 120 } }
    }
    Icon {
        anchors.centerIn: parent
        paths: Icons.star
        size: 19
        filled: root.checked
        color: root.checked ? Theme.accent : (hover.containsMouse ? Theme.accent : "#65758a")
    }
    MouseArea { id: hover; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.toggled() }
    ToolTip.visible: hover.containsMouse
    ToolTip.text: root.checked ? qsTr("Remove from favorites") : qsTr("Add to favorites")
    ToolTip.delay: 600
}
