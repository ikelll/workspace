@echo off
setlocal EnableDelayedExpansion

REM Run from project root.
if not exist venv\Scripts\python.exe (
  echo [ERROR] venv\Scripts\python.exe not found
  exit /b 1
)

call venv\Scripts\activate.bat
if errorlevel 1 exit /b 1

REM Translations: exclude venv/.venv, generated UI, and generated resources.
set PY_FILES=
for /r %%F in (*.py) do (
  echo %%F | findstr /I /C:"\\venv\\" /C:"\\.venv\\" /C:"\\__pycache__\\" /C:"\\resources\\rc_resource.py" >nul
  if errorlevel 1 set PY_FILES=!PY_FILES! "%%F"
)

echo [LUPDATE]
set QML_FILES=
for /r src\qmlui\qml %%F in (*.qml) do set QML_FILES=!QML_FILES! "%%F"
pyside6-lupdate Gorizont-VS-VDI.py src !QML_FILES! -no-obsolete -ts i18n\ru_RU.ts i18n\en_US.ts
if errorlevel 1 exit /b 1

echo [LRELEASE]
pyside6-lrelease i18n\ru_RU.ts i18n\en_US.ts
if errorlevel 1 exit /b 1

REM Resources
if exist resources\resource.qrc (
  echo [RCC] resources\resource.qrc
  pyside6-rcc resources\resource.qrc -o resources\rc_resource.py
  if errorlevel 1 exit /b 1
)

echo Build complete.
endlocal
