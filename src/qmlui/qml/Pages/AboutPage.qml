import QtQuick
import QtQuick.Layouts
import "../Ui"

PageScaffold {
    id: page
    objectName: "pageAbout"
    title: qsTr("About Client")
    subtitle: qsTr("Application information")
    showFooter: false
    readonly property bool twoColumns: contentWidth >= Theme.columnsBreakpoint

    Card {
        Layout.fillWidth: true
        RowLayout {
            Layout.fillWidth: true
            spacing: 20
            Brand { compact: true; logoHeight: 56 }
            Column {
                Layout.fillWidth: true
                spacing: 6
                Text { width: parent.width; text: "Gorizont-VS VDI Client"; color: Theme.ink; font.family: Theme.font; font.pixelSize: 24; font.weight: Font.Bold; wrapMode: Text.WordWrap }
                Text { width: parent.width; text: qsTr("Client for accessing virtual desktops and applications of the Gorizont-VS infrastructure."); color: Theme.muted; font.family: Theme.font; font.pixelSize: 14; wrapMode: Text.WordWrap }
            }
            StatusPill { Layout.alignment: Qt.AlignTop; text: qsTr("Version %1").arg(client.about.version); kind: "accent" }
        }
    }
    GridLayout {
        Layout.fillWidth: true
        columns: page.twoColumns ? 2 : 1
        columnSpacing: 24
        rowSpacing: 24
        Card {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignTop
            title: qsTr("Application")
            spacing: 14
            KeyValueRow { Layout.fillWidth: true; label: qsTr("Version"); value: client.about.version }
            Rectangle { Layout.fillWidth: true; height: 1; color: Theme.border }
            KeyValueRow { Layout.fillWidth: true; label: qsTr("Platform"); value: client.about.platform }
            Rectangle { Layout.fillWidth: true; height: 1; color: Theme.border }
            KeyValueRow { Layout.fillWidth: true; label: qsTr("Log"); value: client.about.logFile || "—" }
        }
        Card {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignTop
            title: qsTr("Connection")
            spacing: 14
            KeyValueRow { Layout.fillWidth: true; label: qsTr("Server"); value: client.serverHost || "—" }
            Rectangle { Layout.fillWidth: true; height: 1; color: Theme.border }
            KeyValueRow { Layout.fillWidth: true; label: qsTr("User"); value: client.username || "—" }
            Rectangle { Layout.fillWidth: true; height: 1; color: Theme.border }
            KeyValueRow { Layout.fillWidth: true; label: qsTr("User-Agent"); value: client.about.userAgent }
        }
    }
    Text { Layout.fillWidth: true; text: qsTr("© 2026 Pangeo-Gorizont"); color: Theme.muted; font.family: Theme.font; font.pixelSize: 12 }
}
