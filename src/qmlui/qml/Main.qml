import QtQuick
import QtQuick.Controls
import "Ui"
import "Screens"
import "Dialogs"

ApplicationWindow {
    id: window
    visible: true
    width: 1360
    height: 860
    minimumWidth: Theme.minimumWindowWidth
    minimumHeight: Theme.minimumWindowHeight
    title: "Gorizont-VS VDI"
    color: Theme.background
    font.family: Theme.font
    font.pixelSize: 14

    Binding { target: Theme; property: "dark"; value: client.theme === "dark" }

    Connections {
        target: client
        function onNotify(kind, text) { Notifications.show(kind, text) }
    }
    Connections {
        target: prompts
        function onRequested(id, kind, title, text, confirmText, cancelText) {
            promptDialog.promptId = id
            promptDialog.kind = kind
            promptDialog.title = title
            promptDialog.text = text
            promptDialog.primaryText = confirmText
            promptDialog.secondaryText = cancelText
            promptDialog.showSecondary = cancelText.length > 0
            promptDialog.primaryDanger = kind === "danger"
            promptDialog.open()
        }
    }

    Loader {
        id: screen
        anchors.fill: parent
        sourceComponent: client.screen === "main" ? mainScreen : client.screen === "loading" ? loadingScreen : loginScreen
    }
    Component { id: loginScreen; LoginScreen {} }
    Component { id: loadingScreen; LoadingScreen {} }
    Component { id: mainScreen; MainScreen {} }

    ConfirmDialog {
        id: promptDialog
        objectName: "promptDialog"
        property int promptId: 0
        property string kind: "primary"
        property bool answered: false
        onAccepted: { answered = true; prompts.answer(promptId, true) }
        onRejected: { if (!answered) prompts.answer(promptId, false); answered = false }
        onOpened: answered = false
    }

    ToastHost {
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        anchors.margins: 20
        width: Math.min(420, parent.width - 40)
    }
}
