[app]
title = GorizontVS-VDI
project_dir = .
input_file = GorizontVS-VDI.py
project_file = pyproject.toml
exec_directory = dist-linux
icon = resources/static/app.ico

[python]
python_path = venv/bin/python
packages = Nuitka==4.0.*,ordered_set,zstandard,patchelf

[qt]
modules = Core,DBus,Gui,Network,Svg,SvgWidgets,Widgets
plugins = iconengines,imageformats,platforminputcontexts,styles,tls

[nuitka]
mode = onefile
extra_args =
    --quiet
    --noinclude-qt-translations
    --include-package=gssapi
    --include-package=krb5
    --include-package=spnego
