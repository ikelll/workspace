# rebuild.ps1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Run from project root.
if (-not (Test-Path "venv\Scripts\python.exe")) {
    Write-Host "[ERROR] venv\Scripts\python.exe not found"
    exit 1
}

& "venv\Scripts\Activate.ps1"

# Translations
Write-Host "[LUPDATE]"
$qml = Get-ChildItem "src\qmlui\qml" -Recurse -Filter "*.qml" | ForEach-Object { $_.FullName }
pyside6-lupdate Gorizont-VS-VDI.py src $qml -no-obsolete -ts i18n\ru_RU.ts i18n\en_US.ts
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "[LRELEASE]"
pyside6-lrelease i18n\ru_RU.ts i18n\en_US.ts
if ($LASTEXITCODE -ne 0) { exit 1 }

# Resources
if (Test-Path "resources\resource.qrc") {
    Write-Host "[RCC] resources\resource.qrc"
    pyside6-rcc "resources\resource.qrc" -o "resources\rc_resource.py"
    if ($LASTEXITCODE -ne 0) { exit 1 }
}

Write-Host "Build complete."
