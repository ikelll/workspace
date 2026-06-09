# rebuild.ps1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Run from project root.
if (-not (Test-Path "venv\Scripts\python.exe")) {
    Write-Host "[ERROR] venv\Scripts\python.exe not found"
    exit 1
}

& "venv\Scripts\Activate.ps1"

# UI files
Get-ChildItem "ui" -Filter "*.ui" | ForEach-Object {
    Write-Host "[UIC] $($_.FullName)"
    pyside6-uic $_.FullName -o "ui\ui_$($_.BaseName).py"
    if ($LASTEXITCODE -ne 0) { exit 1 }
}

# Resources
if (Test-Path "resources\resource.qrc") {
    Write-Host "[RCC] resources\resource.qrc"
    pyside6-rcc "resources\resource.qrc" -o "resources\rc_resource.py"
    if ($LASTEXITCODE -ne 0) { exit 1 }
}

# Translations
Write-Host "[LUPDATE]"
pyside6-lupdate main.py src -ts i18n\ru_RU.ts i18n\en_US.ts
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "[LRELEASE]"
pyside6-lrelease i18n\ru_RU.ts i18n\en_US.ts
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "Build complete."
