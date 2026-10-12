import QtQuick
import QtQuick.Layouts
import "../Ui"

LoginFrame {
    id: page
    title: qsTr("Sign in")
    subtitle: client.negotiateAvailable
              ? qsTr("Enter username and password or leave fields empty for automatic login (SSO).")
              : qsTr("Enter your credentials to log in to the workspace.")
    iconPaths: Icons.lock
    function submit() { if (!client.loginBusy) client.loginWithCredentials(userField.text, passwordField.text) }

    RowLayout {
        Layout.fillWidth: true
        spacing: 10
        Icon { paths: Icons.server; size: 16; color: Theme.muted }
        Text { Layout.fillWidth: true; text: client.serverHost; color: Theme.muted; font.family: Theme.font; font.pixelSize: 13; elide: Text.ElideMiddle }
        AppButton { variant: "ghost"; compact: true; text: qsTr("Change"); onClicked: client.backToServer() }
    }
    AppField {
        objectName: "authenticatorField"
        Layout.fillWidth: true
        visible: client.authenticators.length > 1
        kind: "select"
        label: qsTr("Authenticator")
        options: client.authenticators.map(function(a) { return { value: a.id, label: a.name } })
        value: client.selectedAuthenticator
        enabled: !client.loginBusy
        onEdited: function(text) { client.selectAuthenticator(text) }
    }
    AppField {
        id: userField
        objectName: "userField"
        Layout.fillWidth: true
        label: qsTr("Username")
        placeholderText: client.negotiatePreferred ? qsTr("Leave empty for automatic login") : qsTr("Username")
        enabled: !client.loginBusy
    }
    AppField {
        id: passwordField
        objectName: "passwordField"
        Layout.fillWidth: true
        kind: "password"
        label: qsTr("Password")
        placeholderText: client.negotiatePreferred ? qsTr("Leave empty for automatic login") : qsTr("Password")
        enabled: !client.loginBusy
    }
    actions: [
        AppButton {
            objectName: "loginSubmit"
            Layout.fillWidth: true
            variant: "primary"
            text: client.negotiateAvailable && userField.text.trim().length === 0 && passwordField.text.length === 0 ? qsTr("Sign in automatically") : qsTr("Sign in")
            busy: client.loginBusy
            busyText: qsTr("Signing in…")
            onClicked: page.submit()
        }
    ]
}
