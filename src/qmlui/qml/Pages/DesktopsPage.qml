import QtQuick
import "../Ui"

ResourcePage {
    id: page
    objectName: "pageDesktops"
    property string sortMode: "title"
    title: qsTr("Desktops")
    subtitle: qsTr("Virtual desktops assigned to you")
    showViewToggle: true
    emptyIcon: Icons.monitor
    emptyTitle: qsTr("No desktops")
    emptyText: qsTr("Assigned desktops will appear here.")
    function statusRank(s) { return s.inUse ? 0 : s.statusKind === "success" ? 1 : s.statusKind === "warning" ? 2 : s.statusKind === "neutral" ? 3 : 4 }
    filtered: sourceServices.filter(function(s) { return s.kind === "desktop" && matchesSearch(s) }).sort(function(a, b) {
        if (page.sortMode === "status") { var d = statusRank(a) - statusRank(b); if (d !== 0) return d }
        return byTitle(a, b)
    })
    filters: [
        AppField {
            width: 190
            kind: "select"
            options: [{ value: "title", label: qsTr("By title") }, { value: "status", label: qsTr("By status") }]
            value: page.sortMode
            onEdited: function(text) { page.sortMode = text }
        }
    ]
}
