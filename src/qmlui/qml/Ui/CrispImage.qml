import QtQuick

Image {
    readonly property bool isSvg: source.toString().toLowerCase().endsWith(".svg")
    sourceSize.width: isSvg && width > 0 ? Math.ceil(width) : -1
    sourceSize.height: isSvg && height > 0 ? Math.ceil(height) : -1
    smooth: true
    fillMode: Image.PreserveAspectFit
    asynchronous: false
}
