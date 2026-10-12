import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../Ui"
import "../Login"
import "../Dialogs"

Item {
    id: screen
    readonly property bool wide: width >= 900
    property var pendingDelete: ({})

    function askDelete(profile) {
        pendingDelete = profile
        deleteDialog.open()
    }

    Rectangle { anchors.fill: parent; color: Theme.background }

    Rectangle {
        id: brandPanel
        visible: screen.wide
        width: screen.wide ? Math.min(screen.width * 4 / 9, 620) : 0
        height: parent.height
        color: Theme.surface
        clip: true
        Rectangle { anchors.right: parent.right; width: 1; height: parent.height; color: Theme.border }
        Image {
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: parent.height
            width: height * 7000 / 1339
            sourceSize.height: 560
            sourceSize.width: Math.round(560 * 7000 / 1339)
            source: Theme.dark ? "qrc:/img/static/login-bg-dark.svg" : "qrc:/img/static/login-bg-white.svg"
            fillMode: Image.PreserveAspectFit
            smooth: true
            opacity: 0.6
        }
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 40
            spacing: 22
            Brand { logoHeight: 48 }
            Item { Layout.fillHeight: true }
            Text { text: qsTr("WORKSPACE"); color: Theme.accent; font.family: Theme.font; font.pixelSize: 11; font.weight: Font.DemiBold; font.letterSpacing: 1 }
            Text { Layout.fillWidth: true; text: qsTr("Your workspaces\nand applications — in one place."); color: Theme.ink; font.family: Theme.font; font.pixelSize: brandPanel.width < 480 ? 30 : 38; font.weight: Font.Bold; lineHeight: 1.15; wrapMode: Text.WordWrap }
            Text { Layout.fillWidth: true; text: qsTr("Connect to assigned infrastructure resources of Gorizont-VS from any computer."); color: Theme.muted; font.family: Theme.font; font.pixelSize: 14; lineHeight: 1.4; wrapMode: Text.WordWrap }
            Item {
                id: illustration
                Layout.topMargin: 24
                Layout.preferredWidth: Math.min(520, brandPanel.width - 80)
                Layout.preferredHeight: Layout.preferredWidth * 250 / 520
                visible: brandPanel.height > 640
                CrispImage { width: illustration.width; height: illustration.height; source: "qrc:/img/static/illustration.svg" }
            }
            Item { Layout.fillHeight: true }
            Text { text: qsTr("Gorizont-VS · VDI Client "); color: Theme.muted; font.family: Theme.font; font.pixelSize: 12 }
        }
    }

    Row {
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.margins: 16
        spacing: 8
        z: 2
        AppButton { variant: "ghost"; compact: true; text: client.language.indexOf("ru") === 0 ? "RU" : "EN"; iconPaths: Icons.globe; tooltip: qsTr("Language"); onClicked: client.setLanguage(client.language.indexOf("ru") === 0 ? "en_US" : "ru_RU") }
        AppButton { variant: "ghost"; compact: true; iconPaths: Theme.dark ? Icons.sun : Icons.moon; implicitWidth: 36; tooltip: Theme.dark ? qsTr("Light theme") : qsTr("Dark theme"); onClicked: client.setTheme(Theme.dark ? "light" : "dark") }
    }

    Flickable {
        id: scroll
        anchors.left: brandPanel.visible ? brandPanel.right : parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        contentWidth: width
        contentHeight: Math.max(height, pageLoader.height + 128)
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

        FocusScope {
            id: formScope
            width: parent.width
            height: scroll.contentHeight
            focus: true

            Column {
                anchors.centerIn: parent
                width: Math.min(440, parent.width - 48)
                spacing: 24
                Brand { visible: !screen.wide; logoHeight: 44 }
                Loader {
                    id: pageLoader
                    objectName: "loginPage"
                    width: parent.width
                    source: {
                        switch (client.loginPage) {
                        case "profiles": return "../Login/ProfilesPage.qml"
                        case "credentials": return "../Login/CredentialsPage.qml"
                        case "password": return "../Login/PasswordPage.qml"
                        case "mfaSetup": return "../Login/MfaSetupPage.qml"
                        case "mfaVerify": return "../Login/MfaVerifyPage.qml"
                        default: return "../Login/ServerPage.qml"
                        }
                    }
                    onLoaded: {
                        if (item.deleteRequested !== undefined) item.deleteRequested.connect(screen.askDelete)
                        if (item.focusInitial !== undefined) Qt.callLater(function() { if (pageLoader.item && pageLoader.item.focusInitial) pageLoader.item.focusInitial() })
                    }
                }
            }
        }
    }

    ConfirmDialog {
        id: deleteDialog
        title: qsTr("Delete connection?")
        text: qsTr("Connection «%1» will be deleted along with its settings.").arg(screen.pendingDelete.label || "")
        primaryText: qsTr("Delete")
        primaryDanger: true
        onAccepted: client.deleteProfile(screen.pendingDelete.id)
    }
}
