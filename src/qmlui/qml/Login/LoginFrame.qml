import QtQuick
import QtQuick.Layouts
import "../Ui"

ColumnLayout {
    id: frame
    property string title: ""
    property string subtitle: ""
    property string error: client.loginError
    property var iconPaths: Icons.lock
    default property alias content: body.data
    property alias actions: footer.data
    property alias links: linkRow.data
    spacing: 18

    function focusInitial() {
        var field = firstOf(body, function(c) { return c.forceFocus !== undefined && c.visible && c.enabled && c.kind !== "select" })
        if (field) { field.forceFocus(); return }
        var button = firstOf(footer, function(c) { return c.activeFocusOnTab && c.visible && c.enabled })
        if (button) button.forceActiveFocus()
    }
    function firstOf(item, test) {
        for (var i = 0; i < item.children.length; ++i) {
            var child = item.children[i]
            if (test(child)) return child
            var nested = firstOf(child, test)
            if (nested) return nested
        }
        return null
    }
    function wireFields(item) {
        for (var i = 0; i < item.children.length; ++i) {
            var child = item.children[i]
            if (child.accepted !== undefined && child.forceFocus !== undefined) child.accepted.connect(frame.trySubmit)
            wireFields(child)
        }
    }
    function trySubmit() { if (frame.submit !== undefined && !client.loginBusy) frame.submit() }

    Component.onCompleted: { wireFields(body); Qt.callLater(function() { if (frame && frame.focusInitial) frame.focusInitial() }) }

    Rectangle {
        Layout.preferredWidth: 56
        Layout.preferredHeight: 56
        radius: Theme.radius
        color: Theme.soft
        Icon { anchors.centerIn: parent; paths: frame.iconPaths; color: Theme.accent; size: 26 }
    }
    Column {
        Layout.fillWidth: true
        spacing: 6
        Text { width: parent.width; text: frame.title; color: Theme.ink; font.family: Theme.font; font.pixelSize: 24; font.weight: Font.Bold; wrapMode: Text.WordWrap }
        Text { width: parent.width; visible: frame.subtitle.length > 0; text: frame.subtitle; color: Theme.muted; font.family: Theme.font; font.pixelSize: 14; lineHeight: 1.35; wrapMode: Text.WordWrap }
    }
    ColumnLayout { id: body; Layout.fillWidth: true; spacing: 16 }
    ColumnLayout { id: footer; Layout.fillWidth: true; spacing: 10 }
    Notice { objectName: "loginErrorNotice"; visible: frame.error.length > 0; kind: "danger"; text: frame.error }
    ColumnLayout { id: linkRow; Layout.fillWidth: true; spacing: 6; visible: children.length > 0 }
}
