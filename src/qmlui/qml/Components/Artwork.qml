import QtQuick
import "../Ui"

Item {
    id: art
    property string style: "wave"
    property string symbol: "?"
    property var service: ({})
    property real symbolSize: 58
    clip: true

    readonly property var styles: ({
        windows:        { stops: [[0, "#d8edff"], [0.45, "#b9dcff"], [1, "#81b5fc"]], folds: true },
        windows_server: { stops: [[0, "#c6dbf6"], [0.5, "#8fb3e6"], [1, "#4f7cc4"]], folds: true },
        ubuntu:         { stops: [[0, "#65144a"], [0.55, "#bd3d45"], [1, "#ee792f"]], ring: true },
        wave:           { stops: [[0, "#f2f8ff"], [0.6, "#eaf2ff"], [1, "#d9e9ff"]], wave: true, tile: "#ffffff", text: "#3163a8", light: true },
        excel:          { stops: [[0, "#075436"], [1, "#0d8a55"]], tile: "#0c9b5f" },
        word:           { stops: [[0, "#dbeeff"], [1, "#8dc4ff"]], tile: "#146cd1" },
        powerpoint:     { stops: [[0, "#ffe6d8"], [1, "#f7a97a"]], tile: "#c43e1c" },
        photoshop:      { stops: [[0, "#f5eafe"], [0.58, "#d7c9ff"], [1, "#b4a0ff"]], wave: true, tile: "#22145c", text: "#77c5ff" },
        vscode:         { stops: [[0, "#dbe9ff"], [1, "#9cc3ff"]], tile: "#1f78d1" },
        postgres:       { stops: [[0, "#e4ecf7"], [1, "#b7c9e6"]], tile: "#336791" },
        cad:            { stops: [[0, "#ffe9e9"], [1, "#f7b0b0"]], tile: "#c62828" },
        mint:           { stops: [[0, "#edfbf5"], [0.6, "#dcf5ea"], [1, "#b9e8d5"]], wave: true, tile: "#ffffff", text: "#1f7a5c", light: true },
        sand:           { stops: [[0, "#fff7ea"], [0.6, "#fdefd6"], [1, "#f6ddb0"]], wave: true, tile: "#ffffff", text: "#a0661b", light: true },
        lilac:          { stops: [[0, "#f6effd"], [0.6, "#ece2fb"], [1, "#d6c4f3"]], wave: true, tile: "#ffffff", text: "#6b3fb0", light: true },
        astra_linux:    { stops: [[0, "#163a6b"], [0.6, "#2d64b3"], [1, "#f4a259"]], ring: true },
        redos:          { stops: [[0, "#5a1016"], [0.55, "#b3202a"], [1, "#f26d3d"]], ring: true },
        alt_linux:      { stops: [[0, "#0f3b63"], [0.55, "#1b6db8"], [1, "#f5c843"]], ring: true },
        rosa_linux:     { stops: [[0, "#0d2a6b"], [0.55, "#2358c7"], [1, "#78b4ff"]], ring: true },
        debian:         { stops: [[0, "#5a0a26"], [0.55, "#a80030"], [1, "#e6598a"]], ring: true },
        centos:         { stops: [[0, "#3b2a7a"], [0.5, "#8d5cc9"], [1, "#9ccd2a"]], ring: true },
        rocky_linux:    { stops: [[0, "#0b3f2d"], [0.55, "#10b981"], [1, "#8ef0c7"]], ring: true },
        almalinux:      { stops: [[0, "#0d2550"], [0.55, "#1f4f9e"], [1, "#86da2f"]], ring: true },
        fedora:         { stops: [[0, "#1b2f5e"], [0.55, "#294172"], [1, "#60a5fa"]], ring: true },
        opensuse:       { stops: [[0, "#2a5a12"], [0.55, "#73ba25"], [1, "#c6f08a"]], ring: true },
        linux:          { stops: [[0, "#2b3645"], [0.55, "#475569"], [1, "#94a3b8"]], ring: true },
        other:          { stops: [[0, "#334155"], [1, "#64748b"]] }
    })
    readonly property var spec: styles[style] || styles.other
    function mid(a, b) { var x = Qt.color(a), y = Qt.color(b); return Qt.rgba((x.r + y.r) / 2, (x.g + y.g) / 2, (x.b + y.b) / 2, 1) }
    readonly property bool hasImage: service && service.imageId && client.imageAvailable(service.imageId, client.imageVersion)

    Rectangle {
        id: fill
        width: Math.max(art.width, art.height) * 1.9
        height: width
        anchors.centerIn: parent
        rotation: -35
        gradient: Gradient {
            GradientStop { position: art.spec.stops[0][0]; color: art.spec.stops[0][1] }
            GradientStop { position: art.spec.stops.length > 2 ? art.spec.stops[1][0] : 0.5; color: art.spec.stops.length > 2 ? art.spec.stops[1][1] : art.mid(art.spec.stops[0][1], art.spec.stops[1][1]) }
            GradientStop { position: art.spec.stops[art.spec.stops.length - 1][0]; color: art.spec.stops[art.spec.stops.length - 1][1] }
        }
    }
    Rectangle { anchors.fill: parent; gradient: Gradient { GradientStop { position: 0; color: Qt.rgba(1, 1, 1, 0.04) } GradientStop { position: 1; color: Qt.rgba(0.02, 0.08, 0.18, 0.03) } } }

    Repeater {
        model: art.spec.folds ? [{ w: 95, h: 72, dx: -31, dy: 13, rot: -26, op: 0.75 }, { w: 85, h: 63, dx: 31, dy: -13, rot: 25, op: 0.6 }] : []
        delegate: Item {
            required property var modelData
            anchors.centerIn: parent
            anchors.horizontalCenterOffset: modelData.dx
            anchors.verticalCenterOffset: modelData.dy
            width: modelData.w; height: modelData.h
            rotation: modelData.rot
            opacity: modelData.op
            Rectangle {
                anchors.fill: parent
                radius: height / 2
                gradient: Gradient { orientation: Gradient.Horizontal; GradientStop { position: 0; color: "#1a75ee" } GradientStop { position: 1; color: "#064bb8" } }
            }
            Rectangle { x: parent.width * 0.3; y: -parent.height * 0.15; width: parent.width * 0.6; height: parent.height * 0.75; radius: height / 2; gradient: Gradient { orientation: Gradient.Horizontal; GradientStop { position: 0; color: "#1a75ee" } GradientStop { position: 1; color: "#064bb8" } } }
        }
    }
    Repeater {
        model: art.spec.wave ? [[0, 0.5, 1.5], [-16, 0.7, 1.2], [-32, 0.6, 1]] : []
        delegate: Rectangle {
            required property var modelData
            width: art.width * 1.5
            height: 55
            x: art.width * 0.2
            y: art.height / 2 - 2 + modelData[0]
            rotation: -7
            radius: height / 2
            color: "transparent"
            border.width: modelData[2]
            border.color: Qt.rgba(0.3, 0.33, 0.9, modelData[1])
        }
    }

    Rectangle {
        id: tile
        anchors.centerIn: parent
        width: art.symbolSize
        height: art.symbolSize
        radius: art.spec.ring ? width / 2 : 14
        color: art.spec.ring ? Qt.rgba(1, 1, 1, 0.14) : (art.spec.tile || Qt.rgba(16 / 255, 54 / 255, 115 / 255, 0.86))
        border.width: art.spec.ring ? 4 : 0
        border.color: Qt.rgba(1, 1, 1, 0.9)
        Rectangle { visible: !art.spec.ring && !art.spec.light; anchors.fill: parent; anchors.topMargin: 12; anchors.leftMargin: 4; anchors.rightMargin: 4; radius: parent.radius; color: Qt.rgba(20 / 255, 60 / 255, 130 / 255, 0.21); z: -1; y: 14 }
        Text {
            anchors.centerIn: parent
            visible: !art.hasImage
            text: art.symbol
            color: art.spec.text || "#ffffff"
            font.family: Theme.font
            font.pixelSize: art.symbol.length > 2 ? art.symbolSize * 0.3 : art.symbol.length > 1 ? art.symbolSize * 0.36 : art.symbolSize * 0.42
            font.weight: Font.ExtraBold
            font.letterSpacing: -1
        }
        ServiceImage { anchors.centerIn: parent; visible: art.hasImage; service: art.service; size: art.symbolSize * 0.62 }
    }
}
