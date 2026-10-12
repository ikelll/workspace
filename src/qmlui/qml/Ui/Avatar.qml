import QtQuick

Rectangle {
    id: avatar
    property string initials: "?"
    property color tint: Theme.accent
    property real size: 40
    property bool online: false
    width: size
    height: size
    radius: size / 2
    color: tint
    Text {
        anchors.centerIn: parent
        text: avatar.initials
        color: "white"
        font.family: Theme.font
        font.pixelSize: Math.round(avatar.size * 0.38)
        font.weight: Font.Bold
    }
    Rectangle {
        visible: avatar.online
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        width: Math.max(10, avatar.size * 0.28)
        height: width
        radius: width / 2
        color: Theme.success
        border.width: 2
        border.color: Theme.surface
    }
}
