import QtQuick

Item {
    id: root
    property string label: ""
    property string hint: ""
    property string error: ""
    property var options: []
    property string value: ""
    signal edited(string text)

    readonly property var selected: value.split(",").map(function(s) { return s.trim() }).filter(function(s) { return s.length > 0 })
    readonly property var extra: selected.filter(function(v) { return !options.some(function(o) { return String(o.value) === v }) })
    readonly property var chips: options.map(function(o) { return { value: String(o.value), label: String(o.label) } })
                                        .concat(extra.map(function(v) { return { value: v, label: v } }))

    implicitHeight: labelText.height + 8 + flow.implicitHeight + (hint.length > 0 || error.length > 0 ? 6 + hintText.implicitHeight : 0)
    implicitWidth: 240
    height: implicitHeight
    opacity: enabled ? 1 : 0.55

    function toggle(v) {
        var next = selected.slice()
        var index = next.indexOf(v)
        if (index >= 0) next.splice(index, 1); else next.push(v)
        next.sort(function(a, b) { return root.order(a) - root.order(b) })
        edited(next.join(", "))
    }
    function order(v) {
        for (var i = 0; i < chips.length; ++i) if (chips[i].value === v) return i
        return chips.length
    }

    Text {
        id: labelText
        width: parent.width
        height: 20
        text: root.label
        color: Theme.ink
        font.family: Theme.font
        font.pixelSize: 14
        font.weight: Font.DemiBold
        elide: Text.ElideRight
    }
    Flow {
        id: flow
        y: labelText.height + 8
        width: parent.width
        spacing: 8
        Repeater {
            model: root.chips
            delegate: Rectangle {
                id: chip
                required property var modelData
                readonly property bool active: root.selected.indexOf(modelData.value) >= 0
                height: 36
                width: caption.implicitWidth + 28
                radius: 18
                color: active ? Theme.soft : Theme.surface
                border.width: active || chip.activeFocus ? 1.5 : 1
                border.color: active ? Theme.accent : chip.activeFocus ? Theme.accent : chipHover.containsMouse ? Theme.accentHover : Theme.border
                Behavior on color { ColorAnimation { duration: Theme.motion } }
                activeFocusOnTab: true
                Accessible.role: Accessible.CheckBox
                Accessible.name: modelData.label
                Accessible.checked: active
                Accessible.onToggleAction: root.toggle(modelData.value)
                Keys.onSpacePressed: root.toggle(modelData.value)
                Keys.onReturnPressed: root.toggle(modelData.value)
                Row {
                    anchors.centerIn: parent
                    spacing: 6
                    Icon { anchors.verticalCenter: parent.verticalCenter; visible: chip.active; paths: Icons.check; size: 14; color: Theme.accent; strokeWidth: 2.2 }
                    Text {
                        id: caption
                        anchors.verticalCenter: parent.verticalCenter
                        text: chip.modelData.label
                        color: chip.active ? Theme.accent : Theme.ink
                        font.family: Theme.font
                        font.pixelSize: 13
                        font.weight: chip.active ? Font.DemiBold : Font.Medium
                    }
                }
                MouseArea {
                    id: chipHover
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: root.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
                    onClicked: { chip.forceActiveFocus(); root.toggle(chip.modelData.value) }
                }
            }
        }
    }
    Text {
        id: hintText
        y: flow.y + flow.implicitHeight + 6
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
