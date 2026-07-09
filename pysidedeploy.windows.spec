[app]

# User-facing app name.
title = Gorizont-VS-VDI

# Root of the project.
project_dir = .

# Entry point.
input_file = Gorizont-VS-VDI.py
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
    --include-package=src
    --include-package=src.auth
    --include-module=src.auth.negotiate
    --include-package=spnego
    --include-package=spnego._sspi
    --include-package=spnego._negotiate
    --include-package=spnego._ntlm
    --include-package=sspilib
    --include-module=win32api
    --include-module=win32crypt
    --include-module=win32security
    --include-module=win32con
