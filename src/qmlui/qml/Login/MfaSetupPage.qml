import QtQuick
import QtQuick.Layouts
import "../Ui"

LoginFrame {
    id: page
    title: qsTr("Multi-factor Authentication")
    subtitle: client.mfa.message || qsTr("Scan the QR code with your authenticator app, then enter the verification code.")
    iconPaths: Icons.qr

    function submit() {
        client.mfaContinue()
    }

    Item {
        Layout.fillWidth: true
        implicitHeight: qrCard.height

        Rectangle {
            id: qrCard
            anchors.horizontalCenter: parent.horizontalCenter
            width: 232
            height: 232
            radius: Theme.radius
            color: "white"
            border.width: 1
            border.color: Theme.border

            Image {
                objectName: "mfaQrImage"
                anchors.fill: parent
                anchors.margins: 12
                source: client.mfa.qrImage || ""
                fillMode: Image.PreserveAspectFit
                smooth: false
            }
        }
    }

    actions: [
        AppButton {
            Layout.fillWidth: true
            variant: "primary"
            text: qsTr("Continue")
            onClicked: client.mfaContinue()
        }
    ]

    links: [
        AppButton {
            Layout.fillWidth: true
            variant: "ghost"
            iconPaths: Icons.arrowLeft
            text: qsTr("Back")
            onClicked: client.cancelMfa()
        }
    ]
}