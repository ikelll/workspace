import QtQuick

Item {
    id: row
    property string label: ""
    property string value: ""
    property bool wrap: true
    implicitHeight: Math.max(labelText.implicitHeight, valueText.implicitHeight)
    Text {
        id: labelText
        anchors.left: parent.left
        width: Math.min(188, parent.width * 0.45)
        text: row.label
        color: Theme.muted
        font.family: Theme.font
        font.pixelSize: 14
        wrapMode: Text.WordWrap
    }
    TextEdit {
        id: valueText
        anchors.left: labelText.right
        anchors.leftMargin: 12
        anchors.right: parent.right
        text: row.value
        readOnly: true
        selectByMouse: true
        color: Theme.ink
        font.family: Theme.font
        font.pixelSize: 14
        font.weight: Font.DemiBold
        wrapMode: row.wrap ? TextEdit.Wrap : TextEdit.NoWrap
        activeFocusOnTab: false
    }
}
