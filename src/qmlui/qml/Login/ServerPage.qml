import QtQuick
import QtQuick.Layouts
import "../Ui"

LoginFrame {
    id: page
    title: qsTr("Connect to Server")
    subtitle: qsTr("Enter the broker address or the connection code received from your administrator.")
    iconPaths: Icons.server
    function submit() { if (!client.loginBusy) client.connectServer(serverField.text) }
    AppField {
        id: serverField
        objectName: "serverField"
        Layout.fillWidth: true
        label: qsTr("Server address or connection code")
        placeholderText: "https://vdi.example.ru"
        value: client.serverUrl
        enabled: !client.loginBusy
        error: client.loginError.length > 0 && text.trim().length === 0 ? " " : ""
    }

    actions: [
        AppButton {
            objectName: "serverContinue"
            Layout.fillWidth: true
            variant: "primary"
            text: qsTr("Continue")
            busy: client.loginBusy
            busyText: qsTr("Connecting…")
            onClicked: page.submit()
        }
    ]
    links: [
        AppButton { visible: client.hasProfiles; Layout.fillWidth: true; variant: "ghost"; iconPaths: Icons.arrowLeft; text: qsTr("To saved connections"); onClicked: client.showProfiles() }
    ]
}
