import QtQuick
import "../Ui"

Item {
    id: root
    property var service: ({})
    property real size: 64
    property color fallbackTint: Theme.accent
    property bool darkBackground: false
    width: size
    height: size

    Image {
        id: picture
        anchors.fill: parent
        visible: status === Image.Ready
        source: root.service.imageId && client.imageAvailable(root.service.imageId, client.imageVersion)
                ? "image://services/" + root.service.imageId + "?v=" + client.imageVersion : ""
        sourceSize.width: Math.ceil(root.size * 2)
        sourceSize.height: Math.ceil(root.size * 2)
        fillMode: Image.PreserveAspectFit
        smooth: true
        asynchronous: false
    }
    Rectangle {
        anchors.fill: parent
        visible: picture.status !== Image.Ready
        radius: root.size * 0.28
        color: root.darkBackground ? Qt.rgba(1, 1, 1, 0.22) : root.fallbackTint
        Text {
            anchors.centerIn: parent
            text: (root.service.title || "?").trim().charAt(0).toUpperCase()
            color: "white"
            font.family: Theme.font
            font.pixelSize: root.size * 0.46
            font.weight: Font.Bold
        }
    }
}
