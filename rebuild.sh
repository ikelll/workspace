#!/bin/bash
set -e

pyside6-uic ui/profile_card.ui -o ui/ui_profile_card.py
pyside6-uic ui/confirm_dialog.ui -o ui/ui_confirm_dialog.py
pyside6-uic ui/app_card.ui -o ui/ui_app_card.py
pyside6-uic ui/desktop_card.ui -o ui/ui_desktop_card.py
pyside6-uic ui/form.ui -o ui/ui_form.py

pyside6-rcc resources/resource.qrc -o resources/rc_resource.py

PY_FILES=$(find . -name '*.py' \
    -not -path './ui/ui_*.py' \
    -not -path './resources/rc_resource.py' \
    -not -path './venv/*' \
    -not -path './__pycache__/*' \
    | sort)

UI_FILES=$(find ui -name '*.ui' | sort)

ALL_FILES="$PY_FILES $UI_FILES"

pyside6-lupdate $ALL_FILES -ts i18n/ru_RU.ts
pyside6-lupdate $ALL_FILES -ts i18n/en_US.ts

pyside6-lrelease i18n/ru_RU.ts -qm i18n/ru_RU.qm
pyside6-lrelease i18n/en_US.ts -qm i18n/en_US.qm

echo "Build complete."