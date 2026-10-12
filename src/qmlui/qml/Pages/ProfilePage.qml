import QtQuick
import QtQuick.Layouts
import "../Ui"
import "../Components"
import "../Dialogs"

PageScaffold {
    id: page
    objectName: "pageProfile"
    title: qsTr("Profile")
    subtitle: qsTr("Account and saved connections")
    showFooter: false
    readonly property bool twoColumns: contentWidth >= Theme.columnsBreakpoint
    property var pendingDelete: ({})

    GridLayout {
        Layout.fillWidth: true
        columns: page.twoColumns ? 2 : 1
        columnSpacing: 24
        rowSpacing: 24
        Card {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignTop
            RowLayout {
                Layout.fillWidth: true
                spacing: 16
                Avatar { size: 64; initials: client.initials; tint: client.avatarColor; online: true }
                Column {
                    Layout.fillWidth: true
                    spacing: 4
                    Text { width: parent.width; text: client.displayName; color: Theme.ink; font.family: Theme.font; font.pixelSize: 20; font.weight: Font.Bold; elide: Text.ElideRight }
                    Text { width: parent.width; text: client.username; color: Theme.muted; font.family: Theme.font; font.pixelSize: 13; elide: Text.ElideRight }
                }
            }
            Rectangle { Layout.fillWidth: true; height: 1; color: Theme.border }
            KeyValueRow { Layout.fillWidth: true; label: qsTr("Server"); value: client.currentProfile.host || client.serverHost || "—" }
            KeyValueRow { Layout.fillWidth: true; label: qsTr("Authenticator"); value: client.currentProfile.authName || "—" }
            KeyValueRow { Layout.fillWidth: true; label: qsTr("Login Method"); value: client.currentProfile.negotiate === true ? qsTr("Corporate (SSO)") : qsTr("Password") }
            KeyValueRow { Layout.fillWidth: true; visible: client.lastLogin.length > 0; label: qsTr("Previous Login"); value: client.lastLogin }
            AppButton { Layout.topMargin: 6; variant: "danger"; iconPaths: Icons.logout; text: qsTr("Logout"); onClicked: logoutDialog.open() }
        }
        Card {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignTop
            title: qsTr("Saved Connections")
            subtitle: qsTr("Available on the login screen. Switching is done after logout.")
            Repeater {
                model: client.profiles
                delegate: ProfileTile {
                    required property var modelData
                    Layout.fillWidth: true
                    profile: modelData
                    showDelete: modelData.id !== client.currentProfile.id
                    onClicked: {}
                    onDeleteRequested: { page.pendingDelete = modelData; deleteDialog.open() }
                }
            }
        }
    }

    ConfirmDialog {
        id: logoutDialog
        title: qsTr("Logout of workspace?")
        text: qsTr("Active tunnels will be closed. Open desktop sessions will continue to run.")
        primaryText: qsTr("Logout")
        primaryDanger: true
        onAccepted: client.logout()
    }
    ConfirmDialog {
        id: deleteDialog
        title: qsTr("Delete connection?")
        text: qsTr("Connection «%1» will be deleted along with its settings.").arg(page.pendingDelete.label || "")
        primaryText: qsTr("Delete")
        primaryDanger: true
        onAccepted: client.deleteProfile(page.pendingDelete.id)
    }
}
