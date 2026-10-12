import QtQuick

Item {
    id: brand
    property bool compact: false
    property real logoHeight: 50
    implicitWidth: compact ? logoHeight * 48 / 50 : logoHeight * 3
    implicitHeight: logoHeight
    CrispImage {
        anchors.left: parent.left
        anchors.verticalCenter: parent.verticalCenter
        height: brand.logoHeight
        width: brand.compact ? brand.logoHeight * 48 / 50 : brand.logoHeight * 3
        source: brand.compact ? "qrc:/img/static/logo-small.svg" : "qrc:/img/static/logo.svg"
    }
}