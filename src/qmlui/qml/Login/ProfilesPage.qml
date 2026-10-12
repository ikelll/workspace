import QtQuick
import QtQuick.Layouts
import "../Ui"
import "../Components"

LoginFrame {
    id: page
    title: qsTr("Saved connections")
    subtitle: qsTr("Select a connection or add a new one.")
    iconPaths: Icons.user
    signal deleteRequested(var profile)
    function submit() {}
    Repeater {
        model: client.profiles
        delegate: ProfileTile {
            required property var modelData
            Layout.fillWidth: true
            profile: modelData
            onClicked: client.selectProfile(modelData.id)
            onDeleteRequested: page.deleteRequested(modelData)
        }
    }
    actions: [
        AppButton { Layout.fillWidth: true; Layout.topMargin: 4; variant: "primary"; iconPaths: Icons.plus; text: qsTr("Add connection"); onClicked: client.addConnection() }
    ]
}
