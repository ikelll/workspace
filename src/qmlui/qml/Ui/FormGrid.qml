import QtQuick
import QtQuick.Layouts

GridLayout {
    id: grid
    property int maximumColumns: 2
    columns: Math.min(maximumColumns, Theme.fieldColumns(width))
    columnSpacing: 16
    rowSpacing: 20
    Layout.fillWidth: true
}
