import QtQuick
import QtQuick.Layouts
import "../Ui"

Item {
    id: screen
    Rectangle { anchors.fill: parent; color: Theme.background }
    ColumnLayout {
        anchors.centerIn: parent
        width: Math.min(420, parent.width - 48)
        spacing: 20
        Brand { Layout.alignment: Qt.AlignHCenter; compact: true; logoHeight: 56 }
        Spinner { Layout.alignment: Qt.AlignHCenter; Layout.topMargin: 12; size: 40; lineWidth: 4; running: client.loadingError.length === 0 }
        Text {
            Layout.fillWidth: true
            text: client.loadingError.length > 0 ? client.loadingError : client.loadingText
            color: client.loadingError.length > 0 ? Theme.danger : Theme.ink
            font.family: Theme.font
            font.pixelSize: 15
            font.weight: Font.Medium
            lineHeight: 1.35
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
        }
        AppButton {
            objectName: "loadingCancel"
            Layout.alignment: Qt.AlignHCenter
            visible: client.loadingError.length === 0
            text: qsTranslate("ClientController", "Cancel")
            onClicked: client.connecting ? client.cancelConnection() : client.backToLogin()
        }
        AppButton {
            Layout.alignment: Qt.AlignHCenter
            visible: client.loadingError.length > 0
            iconPaths: Icons.arrowLeft
            text: qsTr("Back to login")
            onClicked: client.backToLogin()
        }
    }
}
