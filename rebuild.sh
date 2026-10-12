#!/bin/bash
set -e

PY_FILES=$(find . -name '*.py' \
    -not -path './resources/rc_resource.py' \
    -not -path './venv/*' \
    -not -path './tests/*' \
    -not -path './__pycache__/*' \
    | sort)

QML_FILES=$(find src/qmlui/qml -name '*.qml' | sort)

ALL_FILES="$PY_FILES $QML_FILES"

pyside6-lupdate $ALL_FILES -no-obsolete -ts i18n/ru_RU.ts
pyside6-lupdate $ALL_FILES -no-obsolete -ts i18n/en_US.ts

pyside6-lrelease i18n/ru_RU.ts -qm i18n/ru_RU.qm
pyside6-lrelease i18n/en_US.ts -qm i18n/en_US.qm

pyside6-rcc resources/resource.qrc -o resources/rc_resource.py

echo "Build complete."
