@echo off
setlocal

REM Run from project root.
if not exist venv\Scripts\python.exe (
  echo [ERROR] venv\Scripts\python.exe not found
  exit /b 1
)

call venv\Scripts\activate.bat
if errorlevel 1 exit /b 1

REM UI files
for %%F in (ui\*.ui) do (
  echo [UIC] %%F
  pyside6-uic "%%F" -o "ui\ui_%%~nF.py"
  if errorlevel 1 exit /b 1
)

REM Resources
if exist resources\resource.qrc (
  echo [RCC] resources\resource.qrc
  pyside6-rcc resources\resource.qrc -o resources\rc_resource.py
  if errorlevel 1 exit /b 1
)

REM Translations: exclude venv/.venv, generated UI, and generated resources.
set PY_FILES=
for /r %%F in (*.py) do (
  echo %%F | findstr /I /C:"\\venv\\" /C:"\\.venv\\" /C:"\\__pycache__\\" /C:"\\ui\\ui_" /C:"\\resources\\rc_resource.py" >nul
  if errorlevel 1 set PY_FILES=!PY_FILES! "%%F"
)

REM Simpler and more reliable fallback for many projects:
REM pyside6-lupdate main.py src ui -ts i18n\ru_RU.ts i18n\en_US.ts

echo [LUPDATE]
pyside6-lupdate main.py src -ts i18n\ru_RU.ts i18n\en_US.ts
if errorlevel 1 exit /b 1

echo [LRELEASE]
pyside6-lrelease i18n\ru_RU.ts i18n\en_US.ts
if errorlevel 1 exit /b 1

echo Build complete.
endlocal
