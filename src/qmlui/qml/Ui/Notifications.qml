pragma Singleton
import QtQuick

QtObject {
    signal show(string kind, string text)
    signal dismissAll()

    function info(text) { show("info", text) }
    function success(text) { show("success", text) }
    function warning(text) { show("warning", text) }
    function error(text) { show("error", text) }
}
