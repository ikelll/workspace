import QtQuick
import QtQuick.Layouts

Item {
    id: heading
    property string title: ""
    property string subtitle: ""
    property alias trailing: trailingRow.data
    implicitHeight: column.implicitHeight
    Layout.fillWidth: true

    RowLayout {
        anchors.fill: parent
        spacing: 12
        Column {
            id: column
            Layout.fillWidth: true
            spacing: 4
            Text {
                width: parent.width
                text: heading.title
                color: Theme.ink
                font.family: Theme.font
                font.pixelSize: 18
                font.weight: Font.DemiBold
                wrapMode: Text.WordWrap
            }
            Text {
                width: parent.width
                visible: heading.subtitle.length > 0
                text: heading.subtitle
                color: Theme.muted
                font.family: Theme.font
                font.pixelSize: 12
                lineHeight: 1.25
                wrapMode: Text.WordWrap
            }
        }
        Row {
            id: trailingRow
            spacing: 8
            Layout.alignment: Qt.AlignTop
        }
    }
}
