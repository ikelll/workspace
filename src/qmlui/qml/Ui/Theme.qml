pragma Singleton
import QtQuick

QtObject {
    id: theme
    property bool dark: false

    readonly property color background: dark ? "#0f172a" : "#f6f8fc"
    readonly property color surface: dark ? "#1e293b" : "#ffffff"
    readonly property color surfaceRaised: dark ? "#273449" : "#ffffff"
    readonly property color ink: dark ? "#f1f5f9" : "#111827"
    readonly property color muted: dark ? "#94a3b8" : "#64748b"
    readonly property color border: dark ? "#334155" : "#e3e9f2"
    readonly property color accent: dark ? "#2fb2d6" : "#047394"
    readonly property color accentHover: dark ? "#5ec6e3" : "#035d79"
    readonly property color soft: dark ? "#1a3a4a" : "#eaf2ff"
    readonly property color danger: dark ? "#f87171" : "#c93434"
    readonly property color dangerSoft: dark ? "#3b1f22" : "#fff0f0"
    readonly property color success: dark ? "#34d399" : "#07865e"
    readonly property color successSoft: dark ? "#163a30" : "#e7f7f0"
    readonly property color warning: dark ? "#fbbf24" : "#b45309"
    readonly property color warningSoft: dark ? "#3a2f14" : "#fff4e5"
    readonly property color disabled: dark ? "#475569" : "#d4dee8"
    readonly property color navy: "#10384e"
    readonly property color overlay: Qt.rgba(0.04, 0.06, 0.1, dark ? 0.6 : 0.45)
    readonly property color accentForeground: "#ffffff"

    readonly property var cardAccents: dark
        ? ["#1d4ed8", "#0f766e", "#6d28d9", "#be185d", "#c2410c", "#a16207", "#15803d", "#0e7490"]
        : ["#2563eb", "#0d9488", "#7c3aed", "#db2777", "#ea580c", "#ca8a04", "#16a34a", "#047394"]
    function cardAccent(index) { return cardAccents[Math.abs(index) % cardAccents.length] }

    readonly property string font: "Montserrat"
    readonly property string monoFont: Qt.platform.os === "osx" ? "Menlo" : Qt.platform.os === "windows" ? "Consolas" : "Monospace"
    readonly property int radius: 13
    readonly property int radiusSmall: 9
    readonly property int motion: 180

    readonly property int controlHeight: 44
    readonly property int fieldHeight: 48

    readonly property int maxFormWidth: 1320
    readonly property int maxDialogWidth: 880
    readonly property int sidebarWidth: 264
    readonly property int railWidth: 72
    readonly property int railBreakpoint: 1040
    readonly property int columnsBreakpoint: 880
    readonly property int compactBreakpoint: 640
    readonly property int minimumWindowWidth: 480
    readonly property int minimumWindowHeight: 360
    readonly property int cardMinWidth: 260
    readonly property int tileMinWidth: 200
    readonly property int cardMaxWidth: 360
    readonly property int tileMaxWidth: 280
    readonly property int maxWorkspaceWidth: 1400

    function pagePadding(width) { return width < compactBreakpoint ? 16 : width < columnsBreakpoint ? 24 : 36 }
    function cardPadding(width) { return width < 420 ? 16 : 24 }
    function fieldColumns(width) { return width >= 980 ? 3 : width >= 500 ? 2 : 1 }
    function gridColumns(width, minWidth, spacing) { return Math.max(1, Math.floor((width + spacing) / (minWidth + spacing))) }
}
