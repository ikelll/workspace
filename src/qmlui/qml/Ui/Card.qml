import QtQuick
import QtQuick.Layouts

Rectangle {
    id: card
    property string title: ""
    property string subtitle: ""
    property int padding: Theme.cardPadding(width)
    property int spacing: 20
    property alias headingTrailing: heading.trailing
    default property alias content: body.data

    implicitHeight: body.implicitHeight + padding * 2 + (heading.visible ? heading.implicitHeight + spacing : 0)
    implicitWidth: 320
    Layout.fillWidth: true
    color: Theme.surface
    radius: Theme.radius
    border.width: 1
    border.color: Theme.border

    SectionHeading {
        id: heading
        visible: card.title.length > 0
        x: card.padding
        y: card.padding
        width: card.width - card.padding * 2
        title: card.title
        subtitle: card.subtitle
    }
    ColumnLayout {
        id: body
        x: card.padding
        y: card.padding + (heading.visible ? heading.implicitHeight + card.spacing : 0)
        width: card.width - card.padding * 2
        spacing: card.spacing
    }
}
