import QtQuick
import QtQuick.Layouts
import "../Ui"

AppDialog {
    id: confirm
    property string text: ""
    property var payload: null
    preferredWidth: 480
    primaryText: "Продолжить"
    Text {
        Layout.fillWidth: true
        text: confirm.text
        color: Theme.ink
        font.family: Theme.font
        font.pixelSize: 14
        lineHeight: 1.35
        wrapMode: Text.WordWrap
    }
    function ask(payloadValue) { payload = payloadValue === undefined ? null : payloadValue; open() }
}
