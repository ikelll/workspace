import QtQuick
import QtQuick.Controls
import "../Ui"

Item {
    id: root
    property var service: ({})
    property bool compact: false
    readonly property bool ready: service.available === true && !client.connecting
    readonly property bool busy: client.connecting && client.connectingServiceId === (service.id || "")
    readonly property bool hovered: area.containsMouse
    signal clicked()
    implicitHeight: compact ? 34 : 36
    implicitWidth: 120
    activeFocusOnTab: ready
    Accessible.role: Accessible.Button
    Accessible.name: label.text
    Keys.onReturnPressed: if (ready) root.clicked()
    Keys.onEnterPressed: if (ready) root.clicked()
    Keys.onSpacePressed: if (ready) root.clicked()
    Rectangle {
        anchors.fill: parent
        radius: 8
        color: !root.ready ? (Theme.dark ? "#1f2a3a" : "#f2f4f7") : (root.hovered ? Theme.accent : Theme.surface)
        border.width: 1
        border.color: !root.ready ? (Theme.dark ? "#334155" : "#e5eaf1") : (root.hovered ? Theme.accent : "#bdd2fc")
        Behavior on color { ColorAnimation { duration: 120 } }
        Rectangle { anchors.fill: parent; anchors.margins: -3; radius: 11; color: "transparent"; border.width: 2; border.color: Theme.accent; visible: root.activeFocus }
    }
    Row {
        anchors.centerIn: parent
        spacing: 8
        Spinner {
            anchors.verticalCenter: parent.verticalCenter
            running: root.busy
            size: 14
            lineWidth: 2
            color: Theme.accent
        }
        Text {
            id: label
            anchors.verticalCenter: parent.verticalCenter
            text: root.busy ? qsTr("Connecting…")
                            : root.service.available === true ? qsTr("Connect")
                            : (root.service.statusKind === "warning" ? qsTr("Please wait") : qsTr("Unavailable"))
            color: root.busy ? Theme.accent : !root.ready ? "#9ba6b4" : (root.hovered ? "#ffffff" : Theme.accent)
            font.family: Theme.font
            font.pixelSize: 13
            font.weight: Font.DemiBold
        }
    }
    MouseArea {
        id: area
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: root.ready ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: if (root.ready) { root.forceActiveFocus(); root.clicked() }
    }
    ToolTip.visible: !root.service.available && area.containsMouse && (root.service.statusDetail || root.service.statusText || "").length > 0
    ToolTip.text: root.service.statusDetail || root.service.statusText || ""
    ToolTip.delay: 500
}
