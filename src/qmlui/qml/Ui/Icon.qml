import QtQuick

Canvas {
    id: icon
    property var paths: []
    property color color: Theme.muted
    property real size: 20
    property real viewBox: 20
    property real strokeWidth: 1.7
    property bool filled: false

    implicitWidth: size
    implicitHeight: size
    width: size
    height: size
    antialiasing: true
    renderTarget: Canvas.Image

    onPathsChanged: requestPaint()
    onColorChanged: requestPaint()
    onSizeChanged: requestPaint()
    onStrokeWidthChanged: requestPaint()
    onFilledChanged: requestPaint()

    onPaint: {
        var ctx = getContext("2d")
        ctx.reset()
        ctx.clearRect(0, 0, width, height)
        ctx.scale(width / viewBox, height / viewBox)
        ctx.lineWidth = strokeWidth
        ctx.lineCap = "round"
        ctx.lineJoin = "round"
        ctx.strokeStyle = color
        ctx.fillStyle = color
        for (var i = 0; i < paths.length; ++i) {
            ctx.beginPath()
            ctx.path = paths[i]
            if (filled) ctx.fill(); else ctx.stroke()
        }
    }
}
