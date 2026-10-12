import QtQuick
import "../Ui"

ResourcePage {
    objectName: "pageHome"
    title: qsTr("Welcome, %1!").arg(client.displayName || client.username)
    subtitle: qsTr("Your assigned resources")
    showViewToggle: true
    emptyTitle: qsTr("No resources assigned")
    emptyText: qsTr("Your administrator has not yet assigned you any desktops or applications. Click «Refresh» to check again.")
    filtered: sourceServices.filter(matchesSearch).sort(function(a, b) {
        if (a.favorite !== b.favorite) return a.favorite ? -1 : 1
        if (a.kind !== b.kind) return a.kind === "desktop" ? -1 : 1
        return byTitle(a, b)
    })
}
