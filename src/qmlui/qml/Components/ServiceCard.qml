import QtQuick
import QtQuick.Layouts
import "../Ui"

Rectangle {
    id: card
    property var service: ({})
    signal connectRequested()
    signal favoriteToggled()
    signal menuRequested(Item anchor)

    readonly property bool hovered: cardHover.containsMouse
    implicitHeight: art.height + body.implicitHeight + 27
    radius: Theme.radius
    color: Theme.surface
    border.width: 1
    border.color: hovered ? (Theme.dark ? "#3b4d66" : "#cdd9e9") : Theme.border
    clip: true
    transform: Translate { y: card.hovered ? -3 : 0; Behavior on y { NumberAnimation { duration: 150; easing.type: Easing.OutCubic } } }
    Behavior on border.color { ColorAnimation { duration: 150 } }

    Artwork {
        id: art
        width: parent.width
        height: 137
        style: card.service.artwork || "other"
        symbol: card.service.symbol || "?"
        service: card.service
    }
    ArtBadge { x: 13; y: 12; text: card.service.statusText || ""; kind: card.service.statusKind || "neutral" }

    ColumnLayout {
        id: body
        anchors.top: art.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 14
        spacing: 5
        Text {
            Layout.fillWidth: true
            text: card.service.title || ""
            color: Theme.ink
            font.family: Theme.font
            font.pixelSize: 15
            font.weight: Font.DemiBold
            elide: Text.ElideRight
        }
        Text {
            Layout.fillWidth: true
            text: card.service.kindTitle || ""
            color: Theme.muted
            font.family: Theme.font
            font.pixelSize: 12
            elide: Text.ElideRight
        }
        RowLayout {
            Layout.fillWidth: true
            Layout.topMargin: 9
            spacing: 6
            ConnectButton { Layout.fillWidth: true; service: card.service; onClicked: card.connectRequested() }
            FavoriteButton { checked: card.service.favorite === true; onToggled: card.favoriteToggled() }
            MoreButton { id: more; onClicked: card.menuRequested(more) }
        }
    }
    MouseArea { id: cardHover; anchors.fill: parent; hoverEnabled: true; acceptedButtons: Qt.NoButton; z: -1 }
}
