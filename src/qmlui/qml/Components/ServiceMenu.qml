import QtQuick
import QtQuick.Controls
import "../Ui"

Popup {
    id: menu
    property var service: ({})
    signal transportChosen(string serviceId, string transportId)
    signal actionChosen(string serviceId, string actionId)

    readonly property var transports: (service.transports || [])
    readonly property var actions: (service.actions || [])
    readonly property bool showTransports: service.showTransports === true && transports.length > 0

    parent: Overlay.overlay
    modal: true
    dim: false
    focus: true
    padding: 8
    width: 280
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    background: Rectangle { color: Theme.surfaceRaised; radius: Theme.radius; border.width: 1; border.color: Theme.border }
    Overlay.modal: Item {}

    function openFor(svc, anchorItem) {
        service = svc
        var p = anchorItem.mapToItem(Overlay.overlay, 0, anchorItem.height + 6)
        x = Math.max(8, Math.min(p.x + anchorItem.width - width, Overlay.overlay.width - width - 8))
        var below = p.y
        y = below + implicitHeight > Overlay.overlay.height - 8 ? Math.max(8, p.y - anchorItem.height - 6 - implicitHeight) : below
        open()
    }

    contentItem: Column {
        spacing: 2
        Text {
            visible: menu.showTransports
            leftPadding: 10; topPadding: 6; bottomPadding: 4
            text: qsTr("TRANSPORT")
            color: Theme.muted
            font.family: Theme.font
            font.pixelSize: 11
            font.weight: Font.DemiBold
            font.letterSpacing: 0.5
        }
        Repeater {
            model: menu.showTransports ? menu.transports : []
            delegate: MenuRow {
                required property var modelData
                width: parent.width
                text: modelData.title
                iconPaths: Icons.transport
                checked: modelData.isDefault === true
                onTriggered: { menu.close(); menu.transportChosen(menu.service.id, modelData.id) }
            }
        }
        Rectangle { visible: menu.showTransports && menu.actions.length > 0; width: parent.width; height: 1; color: Theme.border }
        Text {
            visible: menu.actions.length > 0
            leftPadding: 10; topPadding: 6; bottomPadding: 4
            text: qsTr("ACTIONS")
            color: Theme.muted
            font.family: Theme.font
            font.pixelSize: 11
            font.weight: Font.DemiBold
            font.letterSpacing: 0.5
        }
        Repeater {
            model: menu.actions
            delegate: MenuRow {
                required property var modelData
                width: parent.width
                text: modelData.title
                iconPaths: modelData.icon === "powerOff" ? Icons.powerOff : modelData.icon === "refresh" ? Icons.refresh : Icons.power
                danger: modelData.id === "poweroff"
                onTriggered: { menu.close(); menu.actionChosen(menu.service.id, modelData.id) }
            }
        }
        MenuRow {
            visible: !menu.showTransports && menu.actions.length === 0
            width: parent.width
            text: qsTr("No additional actions")
            enabled: false
        }
    }
}
