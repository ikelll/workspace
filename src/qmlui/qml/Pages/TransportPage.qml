import QtQuick
import QtQuick.Layouts
import "../Ui"

PageScaffold {
    id: page
    objectName: "pageTransport"
    title: qsTr("Transport")
    subtitle: qsTr("Parameters for connecting to desktops for profile «%1»").arg(client.currentProfile.label || client.username)
    showFooter: false
    readonly property var spice: client.spiceSettings
    readonly property bool twoColumns: contentWidth >= Theme.columnsBreakpoint

    function save(patch) {
        var next = { multiMonitorEnabled: spice.multiMonitorEnabled, monitorCount: spice.monitorCount,
                     webdavEnabled: spice.webdavEnabled, webdavPath: spice.webdavPath }
        for (var k in patch) next[k] = patch[k]
        client.saveSpiceSettings(next)
    }

    Notice { visible: !page.spice.available; kind: "warning"; title: qsTr("No active connection"); text: qsTr("Transport settings are bound to the saved connection.") }

    GridLayout {
        Layout.fillWidth: true
        enabled: page.spice.available
        columns: page.twoColumns ? 2 : 1
        columnSpacing: 24
        rowSpacing: 24
        Card {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignTop
            title: qsTr("Screen")
            subtitle: qsTr("SPICE: using multiple monitors")
            AppCheckBox {
                Layout.fillWidth: true
                label: qsTr("Multiple monitors")
                description: qsTr("The desktop will be spread across the specified number of monitors.")
                checked: page.spice.multiMonitorEnabled === true
                onToggled: function(v) { page.save({ multiMonitorEnabled: v }) }
            }
            AppSlider {
                Layout.fillWidth: true
                enabled: page.spice.multiMonitorEnabled === true
                label: qsTr("Number of monitors")
                from: 1; to: 4; step: 1
                defaultValue: 1
                value: String(page.spice.monitorCount || 1)
                onEdited: function(text) { page.save({ monitorCount: text === "" ? 1 : Number(text) }) }
            }
        }
        Card {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignTop
            title: qsTr("Shared folder")
            subtitle: qsTr("SPICE: folder of this computer, available inside the desktop (WebDAV)")
            AppCheckBox {
                Layout.fillWidth: true
                label: qsTr("Connect shared folder")
                checked: page.spice.webdavEnabled === true
                onToggled: function(v) { page.save({ webdavEnabled: v }) }
            }
            RowLayout {
                Layout.fillWidth: true
                enabled: page.spice.webdavEnabled === true
                spacing: 10
                AppField {
                    id: pathField
                    Layout.fillWidth: true
                    label: qsTr("Folder")
                    placeholderText: qsTr("Not selected")
                    value: page.spice.webdavPath || ""
                    onEdited: function(text) { page.save({ webdavPath: text }) }
                }
                AppButton {
                    Layout.alignment: Qt.AlignBottom
                    implicitHeight: Theme.fieldHeight
                    iconPaths: Icons.folder
                    text: qsTr("Browse…")
                    onClicked: { var chosen = client.browseFolder(pathField.text); if (chosen.length > 0) page.save({ webdavPath: chosen }) }
                }
            }
        }
    }
    Notice { kind: "info"; iconPaths: Icons.info; title: qsTr("When settings are applied"); text: qsTr("Parameters are used when connecting to the desktop via SPICE. Settings for other transports are set by the administrator.") }
}
