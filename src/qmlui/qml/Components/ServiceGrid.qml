import QtQuick
import QtQuick.Layouts
import "../Ui"

Item {
    id: root
    property var services: []
    property string mode: "cards"
    property ServiceMenu menu: null
    signal connectRequested(string serviceId)
    signal favoriteToggled(string serviceId)

    readonly property int spacing: 18
    readonly property int minWidth: mode === "tiles" ? Theme.tileMinWidth : Theme.cardMinWidth
    readonly property int columns: mode === "list" ? 1 : Theme.gridColumns(width, minWidth, spacing)
    readonly property real cellWidth: Math.max(1, Math.floor((width - spacing * (columns - 1)) / columns))
    readonly property real itemMaxWidth: mode === "list" ? Math.max(1, width)
                                       : Math.max(mode === "tiles" ? Theme.tileMaxWidth : Theme.cardMaxWidth, cellWidth)
    readonly property int count: services ? services.length : 0

    Layout.fillWidth: true
    implicitHeight: grid.implicitHeight

    GridLayout {
        id: grid
        width: root.count >= root.columns ? root.width
             : Math.min(root.width, root.count * root.itemMaxWidth + Math.max(0, root.count - 1) * root.spacing)
        columns: root.columns
        columnSpacing: root.spacing
        rowSpacing: root.spacing

        Repeater {
            model: root.services
            delegate: Loader {
                required property var modelData
                Layout.fillWidth: true
                Layout.preferredWidth: 1 
                Layout.maximumWidth: root.itemMaxWidth
                Layout.alignment: Qt.AlignLeft | Qt.AlignTop
                sourceComponent: root.mode === "tiles" ? tileComponent : root.mode === "list" ? rowComponent : cardComponent
                onLoaded: item.service = modelData
                onModelDataChanged: if (item) item.service = modelData
            }
        }
        Component {
            id: cardComponent
            ServiceCard {
                width: parent ? parent.width : 300
                onConnectRequested: root.connectRequested(service.id)
                onFavoriteToggled: root.favoriteToggled(service.id)
                onMenuRequested: function(anchor) { if (root.menu) root.menu.openFor(service, anchor) }
            }
        }
        Component {
            id: tileComponent
            ServiceTile {
                width: parent ? parent.width : 220
                onConnectRequested: root.connectRequested(service.id)
                onFavoriteToggled: root.favoriteToggled(service.id)
                onMenuRequested: function(anchor) { if (root.menu) root.menu.openFor(service, anchor) }
            }
        }
        Component {
            id: rowComponent
            ServiceRow {
                width: parent ? parent.width : 600
                onConnectRequested: root.connectRequested(service.id)
                onFavoriteToggled: root.favoriteToggled(service.id)
                onMenuRequested: function(anchor) { if (root.menu) root.menu.openFor(service, anchor) }
            }
        }
    }
}
