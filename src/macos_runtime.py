from __future__ import annotations

import os
import sys
from pathlib import Path


def setup_macos_bundle_environment() -> None:
    if sys.platform != "darwin":
        return

    macos_dir = Path(sys.executable).resolve().parent
    contents_dir = macos_dir.parent
    resources_dir = contents_dir / "Resources"
    frameworks_dir = contents_dir / "Frameworks"
    spice_dir = resources_dir / "spice"

    spice_bin = spice_dir / "bin"
    spice_lib = spice_dir / "lib"
    gst_plugins = spice_lib / "gstreamer-1.0"
    gst_scanner = spice_dir / "libexec" / "gstreamer-1.0" / "gst-plugin-scanner"

    app_support = Path.home() / "Library" / "Application Support" / "GorizontVS"
    app_support.mkdir(parents=True, exist_ok=True)

    def prepend_env(name: str, values: list[str]) -> None:
        old = os.environ.get(name, "")
        parts = [v for v in values if v]
        if old:
            parts.append(old)
        os.environ[name] = os.pathsep.join(parts)

    prepend_env(
        "PATH",
        [
            str(spice_bin),
            str(macos_dir),
            "/usr/local/bin",
            "/opt/homebrew/bin",
            "/usr/bin",
            "/bin",
            "/usr/sbin",
            "/sbin",
        ],
    )

    prepend_env(
        "DYLD_FALLBACK_LIBRARY_PATH",
        [
            str(frameworks_dir),
            str(spice_lib),
            str(gst_plugins),
            "/usr/lib",
        ],
    )

    os.environ["GST_PLUGIN_PATH_1_0"] = str(gst_plugins)
    os.environ["GST_PLUGIN_SCANNER"] = str(gst_scanner)
    os.environ["GST_REGISTRY_REUSE_PLUGIN_SCANNER"] = "1"
    os.environ["GST_REGISTRY"] = str(app_support / "gstreamer-registry.bin")

    os.environ["GIO_MODULE_DIR"] = str(spice_lib / "gio" / "modules")
    os.environ["GI_TYPELIB_PATH"] = str(spice_lib / "girepository-1.0")

    os.environ["GDK_PIXBUF_MODULEDIR"] = str(
        spice_lib / "gdk-pixbuf-2.0" / "2.10.0" / "loaders"
    )
    os.environ["GDK_PIXBUF_MODULE_FILE"] = str(
        spice_lib / "gdk-pixbuf-2.0" / "2.10.0" / "loaders.cache"
    )

    os.environ["XDG_DATA_DIRS"] = f"{spice_dir / 'share'}:/usr/local/share:/usr/share"
    os.environ["GTK_DATA_PREFIX"] = str(spice_dir)
    os.environ["GTK_EXE_PREFIX"] = str(spice_dir)
    os.environ["GTK_PATH"] = str(spice_dir)
    os.environ["TEXTDOMAINDIR"] = str(spice_dir / "share" / "locale")

    if not os.environ.get("LANGUAGE") and os.environ.get("LANG"):
        os.environ["LANGUAGE"] = os.environ["LANG"].split(".", 1)[0]
