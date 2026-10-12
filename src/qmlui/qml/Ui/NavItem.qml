import QtQuick
import QtQuick.Controls

Rectangle {
    id: item
    property string text: ""
    property var iconPaths: []
    property bool active: false
    property bool collapsed: false
    property int badge: 0
    signal activated()

    height: 46
    radius: Theme.radiusSmall
    color: active ? Theme.soft : hover.containsMouse ? Theme.background : Theme.surface
    Behavior on color { ColorAnimation { duration: Theme.motion } }

    activeFocusOnTab: true
    Accessible.role: Accessible.Button
    Accessible.name: text
    Accessible.onPressAction: item.activated()
    Keys.onReturnPressed: item.activated()
    Keys.onEnterPressed: item.activated()
    Keys.onSpacePressed: item.activated()

    Rectangle { anchors.fill: parent; radius: parent.radius; color: "transparent"; border.width: 2; border.color: Theme.accent; visible: item.activeFocus }
    Icon {
        id: glyph
        x: collapsed ? (parent.width - 20) / 2 : 12
        y: 13
        paths: item.iconPaths
        color: item.active ? Theme.accent : Theme.muted
        strokeWidth: item.active ? 2 : 1.7
        Behavior on x { NumberAnimation { duration: Theme.motion } }
    }
    Text {
        anchors.left: glyph.right
        anchors.leftMargin: 12
        anchors.right: counter.visible ? counter.left : parent.right
        anchors.rightMargin: 12
        anchors.verticalCenter: parent.verticalCenter
        visible: !item.collapsed
        text: item.text
        color: item.active ? Theme.accent : Theme.ink
        font.family: Theme.font
        font.pixelSize: 14
        font.weight: item.active ? Font.DemiBold : Font.Medium
        elide: Text.ElideRight
    }
    Rectangle {
        id: counter
        visible: !item.collapsed && item.badge > 0
        anchors.right: parent.right
        anchors.rightMargin: 10
        anchors.verticalCenter: parent.verticalCenter
        width: Math.max(22, badgeText.implicitWidth + 12)
        height: 22
        radius: 11
        color: item.active ? Theme.accent : Theme.border
        Text { id: badgeText; anchors.centerIn: parent; text: item.badge; color: item.active ? "white" : Theme.muted; font.family: Theme.font; font.pixelSize: 11; font.weight: Font.DemiBold }
    }
    MouseArea {
        id: hover
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: { item.forceActiveFocus(); item.activated() }
    }
    ToolTip.visible: item.collapsed && hover.containsMouse
    ToolTip.text: item.text
    ToolTip.delay: 400
}
