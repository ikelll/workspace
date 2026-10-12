import QtQuick
import QtQuick.Controls

Item {
    id: root

    property string kind: "text"
    property string label: ""
    property string hint: ""
    property string error: ""
    property string placeholderText: ""
    property string value: ""
    property var options: []
    property bool revealed: false
    property bool decimals: false
    property int minimumValue: -2147483647
    property int maximumValue: 2147483647
    property int multilineHeight: 120
    property alias text: input.text
    property alias multilineText: area.text
    property alias echoField: input
    readonly property bool isSelect: kind === "select"
    readonly property bool isMultiline: kind === "multiline"
    readonly property bool isPassword: kind === "password"
    readonly property bool focused: input.activeFocus || selector.activeFocus || area.activeFocus
    readonly property real boxHeight: isMultiline ? multilineHeight : Theme.fieldHeight

    signal edited(string text)
    signal accepted()

    function clear() { input.text = ""; area.text = ""; revealed = false }
    function forceFocus() { if (isSelect) selector.forceActiveFocus(); else if (isMultiline) area.forceActiveFocus(); else input.forceActiveFocus() }
    function optionValue(index) { var o = options[index]; return (o !== undefined && o !== null && typeof o === "object") ? String(o.value) : String(o) }
    function optionLabel(index) { var o = options[index]; return (o !== undefined && o !== null && typeof o === "object") ? String(o.label) : String(o) }
    function optionIndex(v) { for (var i = 0; i < options.length; ++i) if (optionValue(i) === String(v)) return i; return -1 }

    property var leadingIcon: []
    readonly property int labelSpace: label.length > 0 ? 28 : 0
    implicitHeight: labelSpace + boxHeight + (hint.length > 0 || error.length > 0 ? 6 + hintText.implicitHeight : 0)
    implicitWidth: 240
    height: implicitHeight

    Text {
        id: labelText
        width: parent.width
        height: 20
        visible: root.label.length > 0
        text: root.label
        color: Theme.ink
        font.family: Theme.font
        font.pixelSize: 14
        font.weight: Font.DemiBold
        elide: Text.ElideRight
    }
    Rectangle {
        id: box
        y: root.labelSpace
        width: parent.width
        height: root.boxHeight
        radius: Theme.radiusSmall
        color: root.enabled ? Theme.surface : Theme.background
        border.color: root.error.length > 0 ? Theme.danger : root.focused ? Theme.accent : Theme.border
        border.width: root.focused || root.error.length > 0 ? 1.5 : 1
        Behavior on border.color { ColorAnimation { duration: Theme.motion } }

        Icon {
            visible: root.leadingIcon.length > 0
            anchors.left: parent.left
            anchors.leftMargin: 14
            anchors.verticalCenter: parent.verticalCenter
            paths: root.leadingIcon
            size: 18
            color: root.focused ? Theme.accent : Theme.muted
        }
        TextField {
            id: input
            anchors.fill: parent
            leftPadding: root.leadingIcon.length > 0 ? 44 : 16
            rightPadding: root.isPassword ? 48 : 16
            visible: !root.isSelect && !root.isMultiline
            text: root.value
            placeholderText: root.placeholderText
            placeholderTextColor: Theme.muted
            echoMode: root.isPassword && !root.revealed ? TextInput.Password : TextInput.Normal
            selectByMouse: true
            font.family: Theme.font
            font.pixelSize: 14
            color: Theme.ink
            background: Item {}
            inputMethodHints: root.kind === "number" ? Qt.ImhFormattedNumbersOnly : Qt.ImhNone
            validator: root.kind === "number" ? numberValidator : null
            Accessible.name: root.label
            onTextEdited: root.edited(text)
            // Enter обрабатывается здесь же (не полагаемся на всплытие события до экрана)
            Keys.onReturnPressed: function(event) { event.accepted = true; root.accepted() }
            Keys.onEnterPressed: function(event) { event.accepted = true; root.accepted() }
        }
        RegularExpressionValidator {
            id: numberValidator
            regularExpression: root.decimals ? /^-?\d{0,9}([.,]\d{0,3})?$/ : /^-?\d{0,9}$/
        }
        ScrollView {
            id: areaScroll
            anchors.fill: parent
            anchors.margins: 2
            visible: root.isMultiline
            clip: true
            contentWidth: availableWidth
            TextArea {
                id: area
                text: root.value
                placeholderText: root.placeholderText
                placeholderTextColor: Theme.muted
                selectByMouse: true
                wrapMode: TextEdit.Wrap
                font.family: Theme.font
                font.pixelSize: 14
                color: Theme.ink
                leftPadding: 14
                rightPadding: 14
                topPadding: 12
                background: Item {}
                Accessible.name: root.label
                onTextChanged: if (root.isMultiline && activeFocus) root.edited(text)
            }
        }
        ComboBox {
            id: selector
            objectName: "styledSelector"
            anchors.fill: parent
            visible: root.isSelect
            model: root.options.length ? root.options.map(function(o, i) { return root.optionLabel(i) }) : [root.value]
            currentIndex: Math.max(0, root.optionIndex(root.value))
            font.family: Theme.font
            font.pixelSize: 14
            leftPadding: 16
            rightPadding: 44
            contentItem: Text {
                text: selector.displayText
                color: Theme.ink
                font: selector.font
                verticalAlignment: Text.AlignVCenter
                elide: Text.ElideRight
            }
            indicator: Icon {
                paths: Icons.chevron
                size: 20
                x: selector.width - 36
                y: (selector.height - 20) / 2
                rotation: selector.popup.visible ? 180 : 0
                Behavior on rotation { NumberAnimation { duration: Theme.motion } }
            }
            background: Item {}
            delegate: ItemDelegate {
                required property var modelData
                required property int index
                width: selector.width - 12
                height: 44
                highlighted: selector.highlightedIndex === index
                leftPadding: 12
                rightPadding: 36
                contentItem: Text {
                    text: modelData
                    font: selector.font
                    color: index === selector.currentIndex ? Theme.accent : Theme.ink
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideRight
                }
                background: Rectangle {
                    radius: 7
                    color: parent.highlighted || parent.hovered ? Theme.soft : "transparent"
                }
                Icon {
                    anchors.right: parent.right
                    anchors.rightMargin: 10
                    anchors.verticalCenter: parent.verticalCenter
                    visible: index === selector.currentIndex
                    paths: Icons.check
                    size: 18
                    color: Theme.accent
                }
            }
            popup: Popup {
                objectName: "selectPopup"
                y: selector.height + 6
                width: selector.width
                padding: 6
                implicitHeight: Math.min(288, choices.contentHeight + 12)
                background: Rectangle {
                    color: Theme.surface
                    border.color: Theme.border
                    radius: Theme.radiusSmall
                }
                contentItem: ListView {
                    id: choices
                    clip: true
                    implicitHeight: contentHeight
                    model: selector.popup.visible ? selector.delegateModel : null
                    currentIndex: selector.highlightedIndex
                    boundsBehavior: Flickable.StopAtBounds
                    ScrollIndicator.vertical: ScrollIndicator {}
                }
            }
            onActivated: function(index) { root.edited(root.options.length ? root.optionValue(index) : currentText) }
            Accessible.name: root.label
        }
        Item {
            id: reveal
            visible: root.isPassword
            anchors.right: parent.right
            anchors.rightMargin: 4
            anchors.verticalCenter: parent.verticalCenter
            width: 40
            height: 40
            activeFocusOnTab: true
            Accessible.role: Accessible.Button
            Accessible.name: root.revealed ? "Скрыть пароль" : "Показать пароль"
            Accessible.onPressAction: root.revealed = !root.revealed
            Keys.onSpacePressed: root.revealed = !root.revealed
            Keys.onReturnPressed: root.revealed = !root.revealed
            Keys.onEnterPressed: root.revealed = !root.revealed
            Rectangle {
                anchors.fill: parent
                radius: Theme.radiusSmall
                color: revealHover.containsMouse || reveal.activeFocus ? Theme.soft : "transparent"
                border.width: reveal.activeFocus ? 2 : 0
                border.color: Theme.accent
            }
            Icon {
                anchors.centerIn: parent
                paths: root.revealed ? Icons.eyeOff : Icons.eye
                size: 20
                color: revealHover.containsMouse ? Theme.ink : Theme.muted
            }
            MouseArea {
                id: revealHover
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: { root.revealed = !root.revealed; input.forceActiveFocus() }
            }
            ToolTip.visible: revealHover.containsMouse
            ToolTip.text: root.revealed ? "Скрыть пароль" : "Показать пароль"
            ToolTip.delay: 600
        }
    }
    Text {
        id: hintText
        y: box.y + box.height + 6
        width: parent.width
        visible: root.hint.length > 0 || root.error.length > 0
        text: root.error.length > 0 ? root.error : root.hint
        font.family: Theme.font
        font.pixelSize: 12
        lineHeight: 1.25
        color: root.error.length > 0 ? Theme.danger : Theme.muted
        wrapMode: Text.WordWrap
    }
}
