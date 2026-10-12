import QtQuick
import QtQuick.Controls

Item {
    id: host
    property int maximumVisible: 4
    readonly property int count: toasts.count
    width: Math.min(560, parent ? parent.width - 32 : 560)
    height: list.contentHeight
    z: 1000

    ListModel { id: toasts }

    function push(kind, text) {
        if (!text || String(text).length === 0) return
        for (var i = 0; i < toasts.count; ++i) {
            if (toasts.get(i).text === text && toasts.get(i).kind === kind) { toasts.remove(i); break }
        }
        while (toasts.count >= maximumVisible) toasts.remove(0)
        toasts.append({ kind: String(kind), text: String(text), stamp: Date.now() })
    }
    function dismiss(stamp) {
        for (var i = 0; i < toasts.count; ++i) if (toasts.get(i).stamp === stamp) { toasts.remove(i); return }
    }
    function clear() { toasts.clear() }
    function duration(kind) { return kind === "error" ? 9000 : kind === "warning" ? 7000 : kind === "success" ? 4500 : 3500 }

    Connections {
        target: Notifications
        function onShow(kind, text) { host.push(kind, text) }
        function onDismissAll() { host.clear() }
    }

    ListView {
        id: list
        width: parent.width
        height: contentHeight
        interactive: false
        spacing: 8
        model: toasts
        add: Transition {
            NumberAnimation { property: "opacity"; from: 0; to: 1; duration: Theme.motion }
            NumberAnimation { property: "y"; from: -12; duration: Theme.motion; easing.type: Easing.OutCubic }
        }
        remove: Transition {
            NumberAnimation { property: "opacity"; to: 0; duration: 140 }
        }
        displaced: Transition { NumberAnimation { property: "y"; duration: Theme.motion; easing.type: Easing.OutCubic } }
        delegate: Item {
            id: toast
            required property string kind
            required property string text
            required property double stamp
            readonly property color tone: kind === "error" ? Theme.danger : kind === "warning" ? Theme.warning
                                        : kind === "success" ? Theme.success : Theme.accent
            width: list.width
            height: card.implicitHeight
            Accessible.role: Accessible.AlertMessage
            Accessible.name: text

            Timer {
                interval: host.duration(toast.kind)
                running: !hover.containsMouse
                repeat: false
                onTriggered: host.dismiss(toast.stamp)
            }
            Rectangle {
                id: card
                width: parent.width
                implicitHeight: Math.max(52, message.implicitHeight + 24)
                radius: Theme.radius
                color: toast.kind === "error" ? Theme.dangerSoft : toast.kind === "warning" ? Theme.warningSoft
                     : toast.kind === "success" ? Theme.successSoft : Theme.soft
                border.width: 1
                border.color: Qt.rgba(toast.tone.r, toast.tone.g, toast.tone.b, 0.25)
                Rectangle { x: 0; y: 10; width: 4; height: parent.height - 20; radius: 2; color: toast.tone }
                Icon {
                    id: glyph
                    x: 18
                    y: 16
                    paths: toast.kind === "error" || toast.kind === "warning" ? Icons.warning : toast.kind === "success" ? Icons.check : Icons.info
                    color: toast.tone
                    size: 20
                }
                Text {
                    id: message
                    anchors.left: glyph.right
                    anchors.leftMargin: 12
                    anchors.right: closeButton.left
                    anchors.rightMargin: 8
                    anchors.verticalCenter: parent.verticalCenter
                    text: toast.text
                    color: Theme.ink
                    font.family: Theme.font
                    font.pixelSize: 13
                    lineHeight: 1.3
                    wrapMode: Text.WordWrap
                    maximumLineCount: 6
                    elide: Text.ElideRight
                }
                Item {
                    id: closeButton
                    anchors.right: parent.right
                    anchors.rightMargin: 8
                    anchors.verticalCenter: parent.verticalCenter
                    width: 32
                    height: 32
                    Rectangle { anchors.fill: parent; radius: 8; color: closeHover.containsMouse ? Qt.rgba(0, 0, 0, 0.06) : "transparent" }
                    Icon { anchors.centerIn: parent; paths: Icons.close; size: 16; color: Theme.muted }
                    MouseArea { id: closeHover; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: host.dismiss(toast.stamp) }
                    Accessible.role: Accessible.Button
                    Accessible.name: "Закрыть уведомление"
                }
                MouseArea {
                    id: hover
                    anchors.fill: parent
                    anchors.rightMargin: 48
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: host.dismiss(toast.stamp)
                }
            }
        }
    }
}
