import QtQuick
import "../Ui"

ResourcePage {
    id: page
    objectName: "pageApps"
    property string category: ""
    readonly property var categories: {
        var seen = {}; var list = []
        sourceServices.forEach(function(s) { if (s.kind === "app" && s.group && !seen[s.group]) { seen[s.group] = true; list.push(s.group) } })
        return list.sort()
    }
    title: qsTr("Applications")
    subtitle: qsTr("Available applications for launch")
    viewMode: "tiles"
    emptyIcon: Icons.apps
    emptyTitle: qsTr("No applications")
    emptyText: qsTr("Published applications will appear here.")
    filtered: sourceServices.filter(function(s) { return s.kind === "app" && (page.category === "" || s.group === page.category) && matchesSearch(s) }).sort(byTitle)
    filters: [
        AppField {
            visible: page.categories.length > 1
            width: 200
            kind: "select"
            options: [{ value: "", label: qsTr("All categories") }].concat(page.categories.map(function(c) { return { value: c, label: c } }))
            value: page.category
            onEdited: function(text) { page.category = text }
        }
    ]
}
