import QtQuick
import "../Ui"

Rectangle {
    id: row
    property string text: ""
    property var iconPaths: []
    property bool checked: false
    property bool danger: false
    signal triggered()
    height: 40
    radius: Theme.radiusSmall
    color: hover.containsMouse || row.activeFocus ? Theme.soft : "transparent"
    opacity: enabled ? 1 : 0.6
    activeFocusOnTab: true
    Accessible.role: Accessible.MenuItem
    Accessible.name: text
    Keys.onReturnPressed: if (enabled) row.triggered()
    Keys.onSpacePressed: if (enabled) row.triggered()
    Icon { id: glyph; x: 10; anchors.verticalCenter: parent.verticalCenter; visible: row.iconPaths.length > 0; paths: row.iconPaths; size: 18; color: row.danger ? Theme.danger : Theme.muted }
    Text {
        anchors.left: parent.left
        anchors.leftMargin: row.iconPaths.length > 0 ? 38 : 12
        anchors.right: check.visible ? check.left : parent.right
        anchors.rightMargin: 10
        anchors.verticalCenter: parent.verticalCenter
        text: row.text
        color: row.danger ? Theme.danger : Theme.ink
        font.family: Theme.font
        font.pixelSize: 13
        font.weight: Font.Medium
        elide: Text.ElideRight
    }
    Icon { id: check; anchors.right: parent.right; anchors.rightMargin: 10; anchors.verticalCenter: parent.verticalCenter; visible: row.checked; paths: Icons.check; size: 16; color: Theme.accent; strokeWidth: 2.2 }
    MouseArea { id: hover; anchors.fill: parent; hoverEnabled: true; enabled: row.enabled; cursorShape: Qt.PointingHandCursor; onClicked: row.triggered() }
}
