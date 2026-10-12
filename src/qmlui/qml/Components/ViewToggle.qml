import QtQuick
import "../Ui"

Rectangle {
    id: toggle
    property string mode: "cards"
    signal selected(string mode)
    implicitWidth: 96
    implicitHeight: 44
    radius: Theme.radiusSmall
    color: Theme.surface
    border.width: 1
    border.color: Theme.border
    activeFocusOnTab: true
    Keys.onLeftPressed: toggle.selected("cards")
    Keys.onRightPressed: toggle.selected("list")
    Row {
        anchors.fill: parent
        anchors.margins: 4
        spacing: 4
        Repeater {
            model: [{ id: "cards", icon: Icons.grid, title: qsTr("Grid") }, { id: "list", icon: Icons.list, title: qsTr("List") }]
            delegate: Rectangle {
                required property var modelData
                readonly property bool active: toggle.mode === modelData.id
                width: (parent.width - 4) / 2
                height: parent.height
                radius: Theme.radiusSmall - 2
                color: active ? Theme.accent : (h.containsMouse ? Theme.soft : "transparent")
                Icon { anchors.centerIn: parent; paths: modelData.icon; size: 18; color: parent.active ? "white" : Theme.muted }
                MouseArea { id: h; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: toggle.selected(modelData.id) }
                Accessible.role: Accessible.RadioButton
                Accessible.name: modelData.title
            }
        }
    }
}
