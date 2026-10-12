import QtQuick

Rectangle {
    id: tabs
    property var model: []
    property int currentIndex: 0
    signal selected(int index)

    implicitHeight: 44
    implicitWidth: row.implicitWidth + 8
    radius: Theme.radiusSmall
    color: Theme.background
    activeFocusOnTab: true
    Accessible.role: Accessible.PageTabList
    Keys.onLeftPressed: if (currentIndex > 0) selected(currentIndex - 1)
    Keys.onRightPressed: if (currentIndex < model.length - 1) selected(currentIndex + 1)

    Rectangle {
        anchors.fill: parent
        anchors.margins: -3
        radius: Theme.radiusSmall + 3
        color: "transparent"
        border.width: 2
        border.color: Theme.accent
        visible: tabs.activeFocus
    }
    Row {
        id: row
        anchors.fill: parent
        anchors.margins: 4
        spacing: 4
        Repeater {
            model: tabs.model
            delegate: Rectangle {
                required property var modelData
                required property int index
                readonly property bool active: index === tabs.currentIndex
                height: parent.height
                width: Math.max(96, caption.implicitWidth + 32)
                radius: Theme.radiusSmall - 2
                color: active ? Theme.surface : hoverArea.containsMouse ? Qt.rgba(Theme.surface.r, Theme.surface.g, Theme.surface.b, 0.55) : Qt.rgba(Theme.surface.r, Theme.surface.g, Theme.surface.b, 0)
                border.width: active ? 1 : 0
                border.color: Theme.border
                Behavior on color { ColorAnimation { duration: Theme.motion } }
                Text {
                    id: caption
                    anchors.centerIn: parent
                    text: modelData
                    color: parent.active ? Theme.accent : Theme.muted
                    font.family: Theme.font
                    font.pixelSize: 13
                    font.weight: Font.DemiBold
                }
                MouseArea {
                    id: hoverArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: { tabs.forceActiveFocus(); tabs.selected(index) }
                }
                Accessible.role: Accessible.PageTab
                Accessible.name: modelData
            }
        }
    }
}
