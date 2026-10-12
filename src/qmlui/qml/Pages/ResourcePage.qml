import QtQuick
import QtQuick.Layouts
import "../Ui"
import "../Components"

PageScaffold {
    id: page
    property ServiceMenu menu: null
    property string search: ""
    property string viewMode: "cards"
    property var sourceServices: client.services
    property var filtered: []
    property string emptyTitle: qsTr("No resources")
    property string emptyText: ""
    property var emptyIcon: Icons.apps
    property bool showViewToggle: false
    property alias filters: filterRow.data
    showFooter: false
    maximumWidth: Theme.maxWorkspaceWidth

    function matchesSearch(svc) {
        var q = search.trim().toLowerCase()
        if (q.length === 0) return true
        var haystack = [svc.title, svc.name, svc.description, svc.group, svc.kindTitle].join(" ").toLowerCase()
        return haystack.indexOf(q) >= 0
    }
    function byTitle(a, b) { return a.title.toLowerCase() < b.title.toLowerCase() ? -1 : a.title.toLowerCase() > b.title.toLowerCase() ? 1 : 0 }

    headerTrailing: [
        RowLayout {
            readonly property bool stacked: page.contentWidth < 760
            width: stacked ? page.contentWidth : implicitWidth
            spacing: 10
            AppField {
                Layout.fillWidth: parent.stacked
                Layout.preferredWidth: 300
                Layout.minimumWidth: 140
                leadingIcon: Icons.search
                placeholderText: qsTr("Search resources…")
                onEdited: function(text) { page.search = text }
            }
            Row { id: filterRow; spacing: 10 }
            ViewToggle { visible: page.showViewToggle; mode: page.viewMode === "list" ? "list" : "cards"; onSelected: function(m) { page.viewMode = m } }
            AppButton { variant: "secondary"; iconPaths: Icons.refresh; implicitWidth: 44; busy: client.servicesBusy; tooltip: qsTr("Refresh list"); onClicked: client.refreshServices(false) }
        }
    ]

    ServiceGrid {
        visible: page.filtered.length > 0
        services: page.filtered
        mode: page.viewMode
        menu: page.menu
        onConnectRequested: function(id) { client.connectService(id, "") }
        onFavoriteToggled: function(id) { client.toggleFavorite(id) }
    }
    EmptyState {
        visible: page.filtered.length === 0
        iconPaths: page.search.trim().length > 0 ? Icons.search : page.emptyIcon
        title: page.search.trim().length > 0 ? qsTr("Nothing found") : page.emptyTitle
        text: page.search.trim().length > 0 ? qsTr("No resources found for query «%1». Try a different name.").arg(page.search.trim()) : page.emptyText
    }
}
