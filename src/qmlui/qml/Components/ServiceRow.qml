import QtQuick
import QtQuick.Layouts
import "../Ui"

Rectangle {
    id: row
    property var service: ({})
    signal connectRequested()
    signal favoriteToggled()
    signal menuRequested(Item anchor)
    readonly property bool hovered: rowHover.containsMouse
    readonly property bool compact: width < 640

    implicitHeight: compact ? art.height + copy.implicitHeight + actions.implicitHeight + 36 : 112
    radius: Theme.radius
    color: Theme.surface
    border.width: 1
    border.color: hovered ? (Theme.dark ? "#3b4d66" : "#cdd9e9") : Theme.border
    clip: true
    Behavior on border.color { ColorAnimation { duration: 150 } }

    Artwork {
        id: art
        width: row.compact ? parent.width : 180
        height: 112
        style: row.service.artwork || "other"
        symbol: row.service.symbol || "?"
        service: row.service
        symbolSize: 52
    }
    ArtBadge { x: 13; y: 12; text: row.service.statusText || ""; kind: row.service.statusKind || "neutral" }

    Column {
        id: copy
        x: row.compact ? 14 : art.width + 24
        y: row.compact ? art.height + 12 : Math.round((art.height - height) / 2)
        width: row.compact ? row.width - 28 : Math.max(60, actions.x - 20 - x)
        spacing: 5
        Text { width: parent.width; text: row.service.title || ""; color: Theme.ink; font.family: Theme.font; font.pixelSize: 15; font.weight: Font.DemiBold; elide: Text.ElideRight }
        Text { width: parent.width; text: row.service.kindTitle || ""; color: Theme.muted; font.family: Theme.font; font.pixelSize: 12; elide: Text.ElideRight }
    }
    RowLayout {
        id: actions
        x: row.compact ? 14 : row.width - 14 - width
        y: row.compact ? copy.y + copy.height + 12 : Math.round((art.height - height) / 2)
        width: row.compact ? row.width - 28 : implicitWidth
        spacing: 6
        ConnectButton { Layout.fillWidth: row.compact; Layout.preferredWidth: row.compact ? 120 : 220; service: row.service; onClicked: row.connectRequested() }
        FavoriteButton { checked: row.service.favorite === true; onToggled: row.favoriteToggled() }
        MoreButton { id: more; onClicked: row.menuRequested(more) }
    }
    MouseArea { id: rowHover; anchors.fill: parent; hoverEnabled: true; acceptedButtons: Qt.NoButton; z: -1 }
}
