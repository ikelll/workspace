import QtQuick
import QtQuick.Layouts
import "../Ui"

LoginFrame {
    id: page
    title: qsTr("Verification code")
    subtitle: client.mfa.message || qsTr("Enter the one-time code from your authenticator app.")
    iconPaths: Icons.key
    function submit() { if (!client.loginBusy) client.verifyMfa(codeField.text, rememberBox.checked) }
    AppField {
        id: codeField
        objectName: "mfaCode"
        Layout.fillWidth: true
        label: client.mfa.label || qsTr("Код")
        placeholderText: "000000"
        enabled: !client.loginBusy
    }
    AppCheckBox { id: rememberBox; Layout.fillWidth: true; label: qsTr("Remember this device"); checked: client.mfa.remember === true; onToggled: function(v) { checked = v } }

    actions: [
        AppButton { objectName: "mfaSubmit"; Layout.fillWidth: true; variant: "primary"; text: qsTr("Verify"); busy: client.loginBusy; busyText: qsTr("Verifying…"); onClicked: page.submit() }
    ]
    links: [
        AppButton { Layout.fillWidth: true; variant: "ghost"; iconPaths: Icons.arrowLeft; text: qsTr("Back"); onClicked: client.mfaBack() }
    ]
}
