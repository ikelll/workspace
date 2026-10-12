import QtQuick
import QtQuick.Layouts
import "../Ui"
import "../Pages"
import "../Components"
import "../Dialogs"

Item {
    id: screen
    property string page: "home"
    readonly property bool collapsedSidebar: width < Theme.railBreakpoint
    readonly property int favoritesCount: client.services.filter(function(s) { return s.favorite === true }).length
    readonly property var primaryPages: [
        { id: "home", title: qsTr("Home"), icon: Icons.home },
        { id: "apps", title: qsTr("Applications"), icon: Icons.apps, badge: client.services.filter(function(s) { return s.kind === "app" }).length },
        { id: "desktops", title: qsTr("Desktops"), icon: Icons.monitor, badge: client.services.filter(function(s) { return s.kind === "desktop" }).length },
        { id: "favorites", title: qsTr("Favorites"), icon: Icons.star, badge: favoritesCount }
    ]
    readonly property var secondaryPages: [
        { id: "settings", title: qsTr("Settings"), icon: Icons.settings },
        { id: "transport", title: qsTr("Transport"), icon: Icons.transport },
        { id: "profile", title: qsTr("Profile"), icon: Icons.user },
        { id: "about", title: qsTr("About"), icon: Icons.info }
    ]
    readonly property var pageIndex: ({ home: 0, apps: 1, desktops: 2, favorites: 3, settings: 4, transport: 5, profile: 6, about: 7 })

    Rectangle { anchors.fill: parent; color: Theme.background }

    Sidebar {
        id: sidebar
        objectName: "sidebar"
        height: parent.height
        collapsed: screen.collapsedSidebar
        currentPage: screen.page
        primaryPages: screen.primaryPages
        secondaryPages: screen.secondaryPages
        userName: client.displayName
        userDetail: client.username !== client.displayName ? client.username : (client.serverHost || "")
        initials: client.initials
        avatarTint: client.avatarColor
        online: client.authenticated
        onNavigate: function(id) { screen.page = id }
        onProfileClicked: screen.page = "profile"
        onLogoutRequested: logoutDialog.open()
    }

    Item {
        id: main
        objectName: "mainContent"
        x: sidebar.width
        width: parent.width - sidebar.width
        height: parent.height
        clip: true
        CrispImage {
            anchors.right: parent.right
            height: parent.height
            width: height * 750 / 1339
            source: Theme.dark ? "qrc:/img/static/main-bg-dark.svg" : "qrc:/img/static/main-bg-white.svg"
            opacity: main.width > 900 ? 1 : 0
        }
        StackLayout {
            anchors.fill: parent
            currentIndex: screen.pageIndex[screen.page] || 0
            HomePage { menu: serviceMenu }
            AppsPage { menu: serviceMenu }
            DesktopsPage { menu: serviceMenu }
            FavoritesPage { menu: serviceMenu }
            SettingsPage {}
            TransportPage {}
            ProfilePage {}
            AboutPage {}
        }
    }

    ConfirmDialog {
        id: logoutDialog
        objectName: "logoutDialog"
        title: qsTr("Logout from workspace?")
        text: qsTr("Active tunnels will be closed. Open sessions of desktops will continue to work.")
        primaryText: qsTr("Logout")
        primaryDanger: true
        onAccepted: client.logout()
    }

    ServiceMenu {
        id: serviceMenu
        onTransportChosen: function(serviceId, transportId) { client.connectService(serviceId, transportId) }
        onActionChosen: function(serviceId, actionId) { client.serviceAction(serviceId, actionId) }
    }
}
