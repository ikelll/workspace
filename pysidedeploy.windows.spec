[app]

# User-facing app name.
title = GorizontVS-VDI

# Root of the project.
project_dir = .

# Entry point.
input_file = GorizontVS-VDI.py
project_file = pyproject.toml

# Output directory for Windows artifacts.
exec_directory = dist-win

# Windows icon.
icon = resources/static/app.ico

[python]

# Use the Python from the active project venv on Windows.
python_path = venv\Scripts\python.exe

# Packages that pyside6-deploy may need to install for deployment.
packages = Nuitka==4.0.*,ordered_set,zstandard

[qt]

# Keep this close to the modules actually used by the app.
modules = Widgets,Core,Gui,Svg,SvgWidgets,Network
plugins = iconengines,imageformats,platforminputcontexts,styles

[nuitka]

# Start with standalone. Switch to onefile after validation.
mode = onefile
extra_args =
    --assume-yes-for-downloads
    --msvc=latest  
    --quiet
    --noinclude-qt-translations
    --windows-console-mode=disable
    --include-package=spnego
    --include-package=sspilib
    --include-module=win32crypt 
    --include-module=win32api
