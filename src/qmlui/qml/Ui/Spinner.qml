import QtQuick

Canvas {
    id: spinner
    property bool running: true
    property color color: Theme.accent
    property real size: 18
    property real lineWidth: 2.5
    implicitWidth: size
    implicitHeight: size
    width: size
    height: size
    visible: running
    antialiasing: true
    renderTarget: Canvas.Image

    onColorChanged: requestPaint()
    onSizeChanged: requestPaint()
    onPaint: {
        var ctx = getContext("2d")
        ctx.reset()
        ctx.clearRect(0, 0, width, height)
        ctx.lineWidth = lineWidth
        ctx.lineCap = "round"
        ctx.strokeStyle = color
        ctx.beginPath()
        ctx.arc(width / 2, height / 2, width / 2 - lineWidth / 2, -Math.PI / 2, Math.PI * 0.4)
        ctx.stroke()
    }
    RotationAnimation on rotation {
        running: spinner.running && spinner.visible
        from: 0
        to: 360
        duration: 900
        loops: Animation.Infinite
    }
}
