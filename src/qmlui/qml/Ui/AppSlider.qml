import QtQuick
import QtQuick.Controls

Item {
    id: root
    property string label: ""
    property string hint: ""
    property string value: ""
    property real defaultValue: 0
    property real from: 0
    property real to: 100
    property real step: 1
    property string unit: ""
    property string error: ""
    readonly property bool isDefault: value === ""
    readonly property real shown: isDefault ? defaultValue : Number(value)
    signal edited(string text)

    implicitHeight: header.implicitHeight + 6 + control.implicitHeight + (hint.length > 0 || error.length > 0 ? 4 + hintText.implicitHeight : 0)
    implicitWidth: 240
    height: implicitHeight
    opacity: enabled ? 1 : 0.55

    function format(number) { return String(Math.round(number * 100) / 100) + (root.unit.length > 0 ? " " + root.unit : "") }

    Row {
        id: header
        width: parent.width
        spacing: 8
        Text {
            text: root.label + ": " + root.format(root.shown)
            color: Theme.ink
            font.family: Theme.font
            font.pixelSize: 14
            font.weight: Font.DemiBold
        }
        Text {
            anchors.verticalCenter: parent.verticalCenter
            visible: root.isDefault
            text: "по умолчанию"
            color: Theme.muted
            font.family: Theme.font
            font.pixelSize: 12
        }
        Item { width: 1; height: 1 }
        AppButton {
            anchors.verticalCenter: parent.verticalCenter
            visible: !root.isDefault
            compact: true
            variant: "ghost"
            text: "Сбросить"
            onClicked: root.edited("")
        }
    }
    Slider {
        id: control
        y: header.implicitHeight + 6
        width: parent.width
        from: root.from
        to: root.to
        stepSize: root.step
        snapMode: Slider.SnapAlways
        value: root.shown
        implicitHeight: 24
        Accessible.name: root.label
        onMoved: root.edited(String(Math.round(value / root.step) * root.step))
        background: Rectangle {
            x: control.leftPadding
            y: control.topPadding + control.availableHeight / 2 - height / 2
            width: control.availableWidth
            height: 6
            radius: 3
            color: Theme.disabled
            Rectangle { width: control.visualPosition * parent.width; height: parent.height; radius: 3; color: Theme.accent }
        }
        handle: Rectangle {
            x: control.leftPadding + control.visualPosition * (control.availableWidth - width)
            y: control.topPadding + control.availableHeight / 2 - height / 2
            width: 22
            height: 22
            radius: 11
            color: Theme.surface
            border.width: 2
            border.color: control.pressed || control.hovered || control.activeFocus ? Theme.accentHover : Theme.accent
            Rectangle {
                anchors.fill: parent
                anchors.margins: -3
                radius: 14
                color: "transparent"
                border.width: 2
                border.color: Theme.accent
                visible: control.activeFocus
            }
        }
    }
    Text {
        id: hintText
        y: control.y + control.implicitHeight + 4
        width: parent.width
        visible: root.hint.length > 0 || root.error.length > 0
        text: root.error.length > 0 ? root.error : root.hint
        color: root.error.length > 0 ? Theme.danger : Theme.muted
        font.family: Theme.font
        font.pixelSize: 12
        lineHeight: 1.25
        wrapMode: Text.WordWrap
    }
}
