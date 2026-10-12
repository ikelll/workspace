import QtQuick
import QtQuick.Controls

Item {
    id: control

    property string text: ""
    property string variant: "secondary"
    property bool busy: false
    property string busyText: ""
    property var iconPaths: []
    property bool compact: false
    property bool fill: false
    property string tooltip: ""
    readonly property bool primary: variant === "primary"
    readonly property bool danger: variant === "danger"
    readonly property bool ghost: variant === "ghost"
    readonly property bool outline: variant === "outline"
    readonly property bool soft: variant === "soft"
    readonly property bool iconOnly: text.length === 0 && iconPaths.length > 0
    readonly property bool interactive: enabled && !busy
    readonly property bool hovered: pointer.containsMouse
    readonly property string shownText: busy && busyText.length > 0 ? busyText : text

    signal clicked()

    implicitHeight: compact ? 36 : Theme.controlHeight
    implicitWidth: iconOnly ? implicitHeight : Math.max(compact ? 72 : 96, row.implicitWidth + (compact ? 28 : 36))
    height: implicitHeight
    width: implicitWidth
    opacity: enabled ? 1 : 0.5

    activeFocusOnTab: true
    Accessible.role: Accessible.Button
    Accessible.name: shownText
    Accessible.onPressAction: control.activate()
    Keys.onReturnPressed: control.activate()
    Keys.onEnterPressed: control.activate()
    Keys.onSpacePressed: control.activate()

    function activate() { if (interactive) clicked() }

    Rectangle {
        id: face
        anchors.fill: parent
        radius: Theme.radiusSmall
        color: control.primary ? (control.hovered && control.interactive ? Theme.accentHover : Theme.accent)
             : control.danger ? (control.hovered && control.interactive ? "#B02C2C" : Theme.danger)
             : control.ghost ? (control.hovered && control.interactive ? Theme.soft : Qt.rgba(Theme.soft.r, Theme.soft.g, Theme.soft.b, 0))
             : control.soft ? (control.hovered && control.interactive ? Qt.darker(Theme.soft, 1.06) : Theme.soft)
             : control.outline ? (control.hovered && control.interactive ? Theme.soft : Theme.surface)
             : (control.hovered && control.interactive ? Qt.darker(Theme.surface, 1.04) : Theme.surface)
        border.width: control.primary || control.danger || control.ghost || control.soft ? 0 : 1
        border.color: control.outline ? Theme.accent : Theme.border
        Behavior on color { ColorAnimation { duration: Theme.motion } }
    }
    Rectangle {
        anchors.fill: parent
        anchors.margins: -3
        radius: Theme.radiusSmall + 3
        color: "transparent"
        border.width: control.activeFocus ? 2 : 0
        border.color: Theme.accent
        visible: control.activeFocus
    }
    Row {
        id: row
        anchors.centerIn: parent
        spacing: 8
        Spinner {
            anchors.verticalCenter: parent.verticalCenter
            running: control.busy
            size: 16
            color: control.primary || control.danger ? "white" : Theme.accent
        }
        Icon {
            anchors.verticalCenter: parent.verticalCenter
            visible: !control.busy && control.iconPaths.length > 0
            paths: control.iconPaths
            size: 18
            color: control.primary || control.danger ? "white" : control.outline || control.soft ? Theme.accent : Theme.ink
        }
        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: control.shownText
            font.family: Theme.font
            font.pixelSize: control.compact ? 13 : 14
            font.weight: Font.DemiBold
            color: control.primary || control.danger ? "white" : control.outline || control.soft ? Theme.accent : Theme.ink
            elide: Text.ElideRight
            maximumLineCount: 1
        }
    }
    MouseArea {
        id: pointer
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: control.interactive ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: { control.forceActiveFocus(); control.activate() }
    }
    ToolTip.visible: control.tooltip.length > 0 && pointer.containsMouse
    ToolTip.text: control.tooltip
    ToolTip.delay: 500
}
