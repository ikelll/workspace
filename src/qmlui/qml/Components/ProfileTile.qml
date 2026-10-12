import QtQuick
import QtQuick.Layouts
import "../Ui"

Rectangle {
    id: tile
    property var profile: ({})
    property bool showDelete: true
    signal clicked()
    signal deleteRequested()
    implicitHeight: 76
    radius: Theme.radius
    color: hover.containsMouse || tile.activeFocus ? Theme.soft : Theme.surface
    border.width: 1
    border.color: tile.activeFocus ? Theme.accent : Theme.border
    activeFocusOnTab: true
    Accessible.role: Accessible.Button
    Accessible.name: profile.label || ""
    Keys.onReturnPressed: tile.clicked()
    Keys.onEnterPressed: tile.clicked()
    Keys.onSpacePressed: tile.clicked()
    RowLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 14
        Avatar { size: 44; initials: tile.profile.initials || "?"; tint: tile.profile.color || Theme.accent }
        Column {
            Layout.fillWidth: true
            spacing: 3
            Text { width: parent.width; text: tile.profile.username || qsTr("Unnamed"); color: Theme.ink; font.family: Theme.font; font.pixelSize: 15; font.weight: Font.DemiBold; elide: Text.ElideRight }
            Text {
                width: parent.width
                text: (tile.profile.host || "") + (tile.profile.authName ? " · " + tile.profile.authName : "") + (tile.profile.negotiate ? " · SSO" : "")
                color: Theme.muted; font.family: Theme.font; font.pixelSize: 12; elide: Text.ElideRight
            }
        }
        StatusPill { visible: tile.profile.isLast === true; text: qsTr("Last used"); kind: "accent" }
        AppButton { visible: tile.showDelete; variant: "ghost"; compact: true; iconPaths: Icons.trash; implicitWidth: 36; tooltip: qsTr("Delete connection"); onClicked: tile.deleteRequested() }
    }
    MouseArea { id: hover; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; z: -1; onClicked: tile.clicked() }
}
