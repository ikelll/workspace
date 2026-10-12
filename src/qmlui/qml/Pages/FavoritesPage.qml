import QtQuick
import "../Ui"

ResourcePage {
    objectName: "pageFavorites"
    title: qsTr("Favorites")
    subtitle: qsTr("Resources you have marked with a star")
    showViewToggle: true
    emptyIcon: Icons.star
    emptyTitle: qsTr("No favorites")
    emptyText: qsTr("Click the star icon on a resource card to add it here.")
    filtered: sourceServices.filter(function(s) { return s.favorite === true && matchesSearch(s) }).sort(byTitle)
}
