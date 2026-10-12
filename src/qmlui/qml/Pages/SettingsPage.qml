import QtQuick
import QtQuick.Layouts
import "../Ui"

PageScaffold {
    id: page
    objectName: "pageSettings"
    title: qsTr("Settings")
    subtitle: qsTr("Appearance and behavior of the client")
    showFooter: false
    readonly property bool twoColumns: contentWidth >= Theme.columnsBreakpoint

    GridLayout {
        Layout.fillWidth: true
        columns: page.twoColumns ? 2 : 1
        columnSpacing: 24
        rowSpacing: 24
        Card {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignTop
            title: qsTr("Appearance")
            subtitle: qsTr("Theme and language of the interface")
            AppField {
                Layout.fillWidth: true
                kind: "select"
                label: qsTr("Theme")
                options: [{ value: "light", label: qsTr("Light") }, { value: "dark", label: qsTr("Dark") }]
                value: client.theme
                onEdited: function(text) { client.setTheme(text) }
            }
            AppField {
                Layout.fillWidth: true
                kind: "select"
                label: qsTr("Language")
                options: [{ value: "ru_RU", label: qsTr("Russian") }, { value: "en_US", label: qsTr("English") }]
                value: client.language
                onEdited: function(text) { client.setLanguage(text) }
            }
        }
        Card {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignTop
            title: qsTr("Workspace")
            subtitle: qsTr("How the client updates the resource list")
            KeyValueRow { Layout.fillWidth: true; label: qsTr("Auto-refresh"); value: qsTr("Every 30 seconds") }
            Rectangle { Layout.fillWidth: true; height: 1; color: Theme.border }
            KeyValueRow { Layout.fillWidth: true; label: qsTr("Server"); value: client.serverHost || "—" }
            Rectangle { Layout.fillWidth: true; height: 1; color: Theme.border }
            KeyValueRow { Layout.fillWidth: true; label: qsTr("Log"); value: client.about.logFile || "—" }
        }
    }
}
