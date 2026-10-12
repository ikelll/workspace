import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: sidebar
    property bool collapsed: false
    property string currentPage: "home"
    property var primaryPages: []
    property var secondaryPages: []
    property string userName: ""
    property string userDetail: ""
    property string initials: "?"
    property color avatarTint: Theme.accent
    property bool online: false
    signal navigate(string page)
    signal profileClicked()
    signal logoutRequested()

    implicitWidth: collapsed ? Theme.railWidth : Theme.sidebarWidth
    width: implicitWidth
    color: Theme.surface
    Behavior on width { NumberAnimation { duration: Theme.motion; easing.type: Easing.OutCubic } }
    Rectangle { anchors.right: parent.right; width: 1; height: parent.height; color: Theme.border }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: sidebar.collapsed ? 12 : 20
        anchors.topMargin: 22
        spacing: 0

        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: sidebar.collapsed ? 2 : 4
            spacing: 12
            Brand { compact: sidebar.collapsed; logoHeight: sidebar.collapsed ? 40 : 50 }
        }

        Item { Layout.preferredHeight: sidebar.collapsed ? 20 : 28 }
        Repeater {
            model: sidebar.primaryPages
            delegate: NavItem {
                required property var modelData
                Layout.fillWidth: true
                Layout.bottomMargin: 6
                text: modelData.title
                iconPaths: modelData.icon
                badge: modelData.badge || 0
                collapsed: sidebar.collapsed
                active: sidebar.currentPage === modelData.id
                onActivated: sidebar.navigate(modelData.id)
            }
        }
        Item { Layout.fillHeight: true; Layout.minimumHeight: 12 }
        Rectangle { Layout.fillWidth: true; Layout.topMargin: 12; Layout.bottomMargin: 18; height: 1; color: Theme.border }
        Repeater {
            model: sidebar.secondaryPages
            delegate: NavItem {
                required property var modelData
                Layout.fillWidth: true
                Layout.bottomMargin: 6
                text: modelData.title
                iconPaths: modelData.icon
                collapsed: sidebar.collapsed
                active: sidebar.currentPage === modelData.id
                onActivated: sidebar.navigate(modelData.id)
            }
        }
        Rectangle { Layout.fillWidth: true; Layout.topMargin: 12; Layout.bottomMargin: 16; height: 1; color: Theme.border }

        Item {
            id: userBlock
            Layout.fillWidth: true
            Layout.bottomMargin: 4
            height: 52
            activeFocusOnTab: true
            Accessible.role: Accessible.Button
            Accessible.name: qsTr("User profile")
            Accessible.onPressAction: sidebar.profileClicked()
            Keys.onReturnPressed: sidebar.profileClicked()
            Keys.onEnterPressed: sidebar.profileClicked()
            Keys.onSpacePressed: sidebar.profileClicked()
            Rectangle {
                anchors.fill: parent
                anchors.margins: -6
                radius: Theme.radiusSmall
                color: userHover.containsMouse ? Theme.background : "transparent"
                border.width: userBlock.activeFocus ? 2 : 0
                border.color: Theme.accent
            }
            Avatar {
                id: userAvatar
                x: sidebar.collapsed ? (parent.width - size) / 2 : 0
                anchors.verticalCenter: parent.verticalCenter
                size: 40
                initials: sidebar.initials
                tint: sidebar.avatarTint
                online: sidebar.online
            }
            Column {
                anchors.left: userAvatar.right
                anchors.leftMargin: 12
                anchors.right: logoutButton.left
                anchors.rightMargin: 6
                anchors.verticalCenter: parent.verticalCenter
                visible: !sidebar.collapsed
                spacing: 2
                Text { width: parent.width; text: sidebar.userName; color: Theme.ink; font.family: Theme.font; font.pixelSize: 14; font.weight: Font.DemiBold; elide: Text.ElideRight }
                Text { width: parent.width; text: sidebar.userDetail; color: Theme.muted; font.family: Theme.font; font.pixelSize: 11; elide: Text.ElideRight }
                Row {
                    spacing: 6
                    visible: sidebar.online
                    Rectangle { anchors.verticalCenter: parent.verticalCenter; width: 7; height: 7; radius: 3.5; color: Theme.success }
                    Text { text: qsTr("Online"); color: Theme.success; font.family: Theme.font; font.pixelSize: 11 }
                }
            }
            MouseArea { id: userHover; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: sidebar.profileClicked() }
            ToolTip.visible: sidebar.collapsed && userHover.containsMouse
            ToolTip.text: sidebar.userName + (sidebar.userDetail.length > 0 ? " · " + sidebar.userDetail : "")
            AppButton {
                id: logoutButton
                visible: !sidebar.collapsed
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                variant: "ghost"
                compact: true
                implicitWidth: 36
                iconPaths: Icons.logout
                tooltip: qsTr("Logout")
                Accessible.name: qsTr("Logout")
                onClicked: sidebar.logoutRequested()
            }
        }
        AppButton {
            visible: sidebar.collapsed
            Layout.alignment: Qt.AlignHCenter
            Layout.topMargin: 6
            variant: "ghost"
            compact: true
            implicitWidth: 36
            iconPaths: Icons.logout
            tooltip: qsTr("Logout")
            Accessible.name: qsTr("Logout")
            onClicked: sidebar.logoutRequested()
        }
    }
}
