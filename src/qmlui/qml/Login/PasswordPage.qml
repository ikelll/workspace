import QtQuick
import QtQuick.Layouts
import "../Ui"

LoginFrame {
    id: page
    readonly property var profile: client.currentProfile
    readonly property bool sso: profile.negotiate === true
    signal deleteRequested(var profile)
    title: qsTr("Welcome back")
    subtitle: sso ? qsTr("You'll be signed in automatically with your corporate account (SSO)") : qsTr("Enter your password to continue.")
    iconPaths: Icons.user
    function submit() { if (!client.loginBusy) client.loginWithProfile(passwordField.text) }

    Rectangle {
        Layout.fillWidth: true
        implicitHeight: identity.implicitHeight + 32
        radius: Theme.radius
        color: Theme.background
        RowLayout {
            id: identity
            anchors.fill: parent
            anchors.margins: 16
            spacing: 14
            Avatar { size: 48; initials: page.profile.initials || "?"; tint: page.profile.color || Theme.accent }
            Column {
                Layout.fillWidth: true
                spacing: 3
                Text { width: parent.width; text: page.profile.username || ""; color: Theme.ink; font.family: Theme.font; font.pixelSize: 16; font.weight: Font.DemiBold; elide: Text.ElideRight }
                Text { width: parent.width; text: (page.profile.host || "") + (page.profile.authName ? " · " + page.profile.authName : ""); color: Theme.muted; font.family: Theme.font; font.pixelSize: 12; elide: Text.ElideRight }
            }
        }
    }
    AppField {
        id: passwordField
        objectName: "profilePassword"
        Layout.fillWidth: true
        visible: !page.sso
        kind: "password"
        label: qsTr("Password")
        placeholderText: qsTr("Enter password")
        enabled: !client.loginBusy
    }

    actions: [
        AppButton {
            objectName: "profileLogin"
            Layout.fillWidth: true
            variant: "primary"
            text: page.sso ? qsTr("Sign in with SSO") : qsTr("Sign in")
            busy: client.loginBusy
            busyText: qsTr("Signing in…")
            onClicked: page.submit()
        }
    ]
    links: [
        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            AppButton { Layout.fillWidth: true; variant: "ghost"; text: qsTr("Other connection"); onClicked: client.hasProfiles && client.profiles.length > 1 ? client.showProfiles() : client.addConnection() }
            AppButton { variant: "ghost"; iconPaths: Icons.trash; implicitWidth: 44; tooltip: qsTr("Delete connection"); onClicked: page.deleteRequested(page.profile) }
        }
    ]
}
