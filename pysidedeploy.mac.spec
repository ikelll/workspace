[app]
title = GorizontVS-VDI
project_dir = .
input_file = GorizontVS-VDI.py
project_file = pyproject.toml
exec_directory = dist

# important = Use .icns on macOS.
icon = resources/static/app.icns

[python]
python_path = venv/bin/python3
packages = Nuitka==4.0.*,ordered_set,zstandard

[qt]
modules = Core,DBus,Gui,Svg,SvgWidgets,Widgets
plugins = iconengines,imageformats,platforminputcontexts,styles

[nuitka]
mode = onefile
extra_args = 
	--windows-console-mode=force
	--quiet
	--noinclude-qt-translations
	--include-package=spnego
	--include-package=gssapi
	--include-package=krb5
macos.permissions = 

