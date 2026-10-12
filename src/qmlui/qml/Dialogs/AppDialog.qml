import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../Ui"

Popup {
    id: dialog

    property string title: ""
    property string subtitle: ""
    property string primaryText: "Сохранить"
    property string secondaryText: "Отмена"
    property bool primaryEnabled: true
    property bool primaryBusy: false
    property string primaryBusyText: ""
    property bool primaryDanger: false
    property bool showPrimary: true
    property bool showSecondary: true
    property bool closeOnEscape: true
    property bool closeOnAccept: true
    property int preferredWidth: 560
    property int preferredHeight: 0
    property Item initialFocus: null
    property string footerNote: ""
    default property alias content: body.data
    readonly property bool compact: width < 440
    property bool accepted_: false

    signal accepted()
    signal rejected()

    parent: Overlay.overlay
    anchors.centerIn: parent
    modal: true
    focus: true
    dim: true
    padding: 0
    closePolicy: closeOnEscape ? Popup.CloseOnEscape : Popup.NoAutoClose
    width: parent ? Math.min(preferredWidth, parent.width - 32) : preferredWidth
    height: parent ? Math.min(preferredHeight > 0 ? preferredHeight : implicitHeight, parent.height - 32) : implicitHeight
    implicitHeight: layout.implicitHeight

    Overlay.modal: Rectangle { color: Theme.overlay }

    enter: Transition {
        NumberAnimation { property: "opacity"; from: 0; to: 1; duration: Theme.motion }
        NumberAnimation { property: "scale"; from: 0.97; to: 1; duration: Theme.motion; easing.type: Easing.OutCubic }
    }
    exit: Transition { NumberAnimation { property: "opacity"; to: 0; duration: 120 } }

    background: Rectangle {
        color: Theme.surface
        radius: Theme.radius
        border.width: 1
        border.color: Theme.border
    }

    function accept() {
        if (!primaryEnabled || primaryBusy) return
        accepted_ = true
        accepted()
        if (closeOnAccept) close()
    }
    function reject() { accepted_ = false; close() }
    function focusInitial() {
        if (initialFocus) { if (initialFocus.forceFocus) initialFocus.forceFocus(); else initialFocus.forceActiveFocus(); return }
        var first = firstFocusable(body)
        if (first) { if (first.forceFocus) first.forceFocus(); else first.forceActiveFocus() }
        else if (primaryButton.visible) primaryButton.forceActiveFocus()
        else if (secondaryButton.visible) secondaryButton.forceActiveFocus()
    }
    function firstFocusable(item) {
        for (var i = 0; i < item.children.length; ++i) {
            var child = item.children[i]
            if (!child.visible) continue
            if (child.forceFocus !== undefined || (child.activeFocusOnTab && child.enabled)) return child
            var nested = firstFocusable(child)
            if (nested) return nested
        }
        return null
    }
    function inMultiline(item) {
        while (item) {
            if (item instanceof TextArea) return true
            item = item.parent
        }
        return false
    }

    onAboutToShow: { accepted_ = false; Qt.callLater(focusInitial) }
    onOpened: if (!scope.activeFocus) focusInitial()
    onClosed: if (!accepted_) rejected()

    contentItem: FocusScope {
        id: scope
        Keys.onEscapePressed: function(event) { if (dialog.closeOnEscape) { dialog.reject(); event.accepted = true } }
        Keys.onReturnPressed: function(event) { if (!dialog.inMultiline(Window.activeFocusItem)) { dialog.accept(); event.accepted = true } }
        Keys.onEnterPressed: function(event) { if (!dialog.inMultiline(Window.activeFocusItem)) { dialog.accept(); event.accepted = true } }

        ColumnLayout {
            id: layout
            anchors.fill: parent
            spacing: 0

            RowLayout {
                Layout.fillWidth: true
                Layout.margins: dialog.compact ? 20 : 28
                Layout.bottomMargin: 0
                spacing: 12
                Column {
                    Layout.fillWidth: true
                    spacing: 6
                    Text {
                        width: parent.width
                        text: dialog.title
                        color: Theme.ink
                        font.family: Theme.font
                        font.pixelSize: 18
                        font.weight: Font.DemiBold
                        wrapMode: Text.WordWrap
                    }
                    Text {
                        width: parent.width
                        visible: dialog.subtitle.length > 0
                        text: dialog.subtitle
                        color: Theme.muted
                        font.family: Theme.font
                        font.pixelSize: 12
                        lineHeight: 1.3
                        wrapMode: Text.WordWrap
                    }
                }
                AppButton {
                    Layout.alignment: Qt.AlignTop
                    variant: "ghost"
                    compact: true
                    iconPaths: Icons.close
                    implicitWidth: 36
                    tooltip: "Закрыть (Esc)"
                    enabled: dialog.closeOnEscape
                    Accessible.name: "Закрыть"
                    onClicked: dialog.reject()
                }
            }
            Flickable {
                id: bodyScroll
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.topMargin: 20
                Layout.leftMargin: dialog.compact ? 20 : 28
                Layout.rightMargin: dialog.compact ? 20 : 28
                implicitHeight: body.implicitHeight
                contentWidth: width
                contentHeight: body.implicitHeight
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: ScrollBar { policy: bodyScroll.contentHeight > bodyScroll.height ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff }
                ColumnLayout {
                    id: body
                    width: bodyScroll.width - (bodyScroll.contentHeight > bodyScroll.height ? 14 : 0)
                    spacing: 20
                }
            }
            GridLayout {
                Layout.fillWidth: true
                Layout.margins: dialog.compact ? 20 : 28
                Layout.topMargin: 24
                columns: dialog.compact ? 1 : 2
                columnSpacing: 12
                rowSpacing: 12
                Text {
                    Layout.fillWidth: true
                    visible: dialog.footerNote.length > 0 || !dialog.compact
                    text: dialog.footerNote
                    color: Theme.muted
                    font.family: Theme.font
                    font.pixelSize: 12
                    lineHeight: 1.25
                    wrapMode: Text.WordWrap
                }
                GridLayout {
                    Layout.alignment: dialog.compact ? Qt.AlignLeft : Qt.AlignRight | Qt.AlignVCenter
                    Layout.fillWidth: dialog.compact
                    columns: dialog.compact ? 1 : 2
                    layoutDirection: Qt.RightToLeft
                    columnSpacing: 12
                    rowSpacing: 12
                    AppButton {
                        id: primaryButton
                        visible: dialog.showPrimary
                        Layout.fillWidth: dialog.compact
                        text: dialog.primaryText
                        variant: dialog.primaryDanger ? "danger" : "primary"
                        enabled: dialog.primaryEnabled
                        busy: dialog.primaryBusy
                        busyText: dialog.primaryBusyText
                        onClicked: dialog.accept()
                    }
                    AppButton {
                        id: secondaryButton
                        visible: dialog.showSecondary
                        Layout.fillWidth: dialog.compact
                        text: dialog.secondaryText
                        onClicked: dialog.reject()
                    }
                }
            }
        }
    }
}
