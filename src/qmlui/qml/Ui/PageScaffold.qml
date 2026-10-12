import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: page

    property string title: ""
    property string subtitle: ""
    property string footerNote: ""
    property bool showFooter: true
    property int maximumWidth: Theme.maxFormWidth
    property alias headerTrailing: headerTrailing.data
    property alias footerActions: actions.data
    default property alias content: body.data
    readonly property int padding: Theme.pagePadding(width)
    readonly property int contentWidth: Math.min(width - padding * 2, maximumWidth)
    readonly property bool compact: width < Theme.compactBreakpoint
    property alias flickable: scroll

    signal submit()

    Keys.onReturnPressed: page.submit()
    Keys.onEnterPressed: page.submit()

    Flickable {
        id: scroll
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: footer.visible ? footer.top : parent.bottom
        contentWidth: width
        contentHeight: column.implicitHeight + page.padding * 2
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

        ColumnLayout {
            id: column
            x: page.padding
            y: page.padding
            width: page.contentWidth
            spacing: 24
            GridLayout {
                Layout.fillWidth: true
                columns: page.contentWidth < 760 ? 1 : 2
                columnSpacing: 16
                rowSpacing: 16
                Column {
                    Layout.fillWidth: true
                    spacing: 8
                    Text {
                        width: parent.width
                        text: page.title
                        color: Theme.ink
                        font.family: Theme.font
                        font.pixelSize: page.compact ? 22 : 26
                        font.weight: Font.Bold
                        wrapMode: Text.WordWrap
                    }
                    Text {
                        width: parent.width
                        visible: page.subtitle.length > 0
                        text: page.subtitle
                        color: Theme.muted
                        font.family: Theme.font
                        font.pixelSize: 14
                        lineHeight: 1.3
                        wrapMode: Text.WordWrap
                    }
                }
                Row { id: headerTrailing; spacing: 8; Layout.alignment: Qt.AlignTop | Qt.AlignRight; visible: children.length > 0 }
            }
            ColumnLayout {
                id: body
                Layout.fillWidth: true
                spacing: 24
            }
        }
    }

    Rectangle {
        id: footer
        visible: page.showFooter && (actions.children.length > 0 || page.footerNote.length > 0)
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: footerLayout.implicitHeight + 24
        color: Qt.rgba(1, 1, 1, 0.92)
        Rectangle { anchors.top: parent.top; width: parent.width; height: 1; color: Theme.border }
        GridLayout {
            id: footerLayout
            x: page.padding
            y: 12
            width: page.contentWidth
            columns: page.compact ? 1 : 2
            columnSpacing: 16
            rowSpacing: 12
            Text {
                Layout.fillWidth: true
                visible: page.footerNote.length > 0
                text: page.footerNote
                color: Theme.muted
                font.family: Theme.font
                font.pixelSize: 12
                lineHeight: 1.25
                wrapMode: Text.WordWrap
            }
            GridLayout {
                id: actions
                Layout.alignment: page.compact ? Qt.AlignLeft : Qt.AlignRight | Qt.AlignVCenter
                Layout.fillWidth: page.compact
                columns: page.compact ? 1 : 100
                layoutDirection: Qt.RightToLeft
                columnSpacing: 12
                rowSpacing: 12
            }
        }
    }
}
