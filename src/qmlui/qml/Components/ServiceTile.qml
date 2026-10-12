import QtQuick
import QtQuick.Layouts
import "../Ui"

Rectangle {
    id: tile
    property var service: ({})
    signal connectRequested()
    signal favoriteToggled()
    signal menuRequested(Item anchor)
    readonly property bool hovered: tileHover.containsMouse

    implicitHeight: art.height + column.implicitHeight + 28
    radius: Theme.radius
    color: Theme.surface
    border.width: 1
    border.color: hovered ? (Theme.dark ? "#3b4d66" : "#cdd9e9") : Theme.border
    clip: true
    transform: Translate { y: tile.hovered ? -3 : 0; Behavior on y { NumberAnimation { duration: 150; easing.type: Easing.OutCubic } } }
    Behavior on border.color { ColorAnimation { duration: 150 } }

    Artwork {
        id: art
        width: parent.width
        height: 104
        style: tile.service.artwork || "other"
        symbol: tile.service.symbol || "?"
        service: tile.service
        symbolSize: 52
    }
    ArtBadge { visible: tile.service.statusKind !== "success"; x: 12; y: 11; text: tile.service.statusText || ""; kind: tile.service.statusKind || "neutral" }

    ColumnLayout {
        id: column
        anchors.top: art.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 14
        spacing: 4
        Text { Layout.fillWidth: true; text: tile.service.title || ""; color: Theme.ink; font.family: Theme.font; font.pixelSize: 14; font.weight: Font.DemiBold; elide: Text.ElideRight; horizontalAlignment: Text.AlignHCenter }
        Text { Layout.fillWidth: true; text: tile.service.group || tile.service.kindTitle || ""; color: Theme.muted; font.family: Theme.font; font.pixelSize: 12; elide: Text.ElideRight; horizontalAlignment: Text.AlignHCenter }
        RowLayout {
            Layout.fillWidth: true
            Layout.topMargin: 8
            spacing: 4
            ConnectButton { Layout.fillWidth: true; compact: true; service: tile.service; onClicked: tile.connectRequested() }
            FavoriteButton { checked: tile.service.favorite === true; onToggled: tile.favoriteToggled() }
            MoreButton { id: more; visible: (tile.service.showTransports === true) || (tile.service.actions || []).length > 0; onClicked: tile.menuRequested(more) }
        }
    }
    MouseArea { id: tileHover; anchors.fill: parent; hoverEnabled: true; acceptedButtons: Qt.NoButton; z: -1 }
}
