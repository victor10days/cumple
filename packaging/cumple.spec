# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the cumple desktop app.

    uv run pyinstaller packaging/cumple.spec --noconfirm --clean

One directory per platform (`dist/cumple-app`, `dist/cumple.app` on macOS): onefile would unpack
about 150 MB on every launch. The release workflow zips the result; see .github/workflows/release.yml.
"""

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files

ROOT = Path(SPECPATH).parent  # noqa: F821  (SPECPATH is injected by PyInstaller)
sys.path.insert(0, str(ROOT / "src"))
from cumple import __version__  # noqa: E402

UI = ROOT / "src" / "cumple" / "app" / "ui"
MAC = sys.platform == "darwin"
WIN = sys.platform == "win32"
LINUX = sys.platform.startswith("linux")

hidden = ["cumple.app.main", "cumple.app.api", "cumple.app.selftest", "cumple.app.desktop", "cumple.app.ui"]
if MAC:
    hidden += ["webview.platforms.cocoa", "objc", "AppKit", "Foundation", "WebKit", "Quartz", "Security", "UniformTypeIdentifiers"]
if WIN:
    hidden += ["webview.platforms.winforms", "webview.platforms.edgechromium", "clr", "clr_loader"]
if LINUX:
    hidden += [
        "webview.platforms.qt",
        "qtpy",
        "PyQt6.QtWebEngineWidgets",
        "PyQt6.QtWebEngineCore",
        "PyQt6.QtWebChannel",
        "PyQt6.QtNetwork",
        "PyQt6.QtPrintSupport",
    ]

excludes = [
    "tkinter",
    "pytest",
    "IPython",
    "matplotlib",
    "PIL",
    "pyloudnorm",
    "fontTools",
    "PyQt5",
    "PySide2",
    "PySide6",
    "gi",
    "cefpython3",
    "webview.platforms.cef",
]
if LINUX:
    excludes += [
        "PyQt6.QtBluetooth",
        "PyQt6.QtMultimedia",
        "PyQt6.QtMultimediaWidgets",
        "PyQt6.QtSql",
        "PyQt6.QtTest",
        "PyQt6.QtSensors",
        "PyQt6.QtSerialPort",
        "PyQt6.QtNfc",
        "PyQt6.QtRemoteObjects",
        "PyQt6.QtQuick",
        "PyQt6.QtQuick3D",
        "PyQt6.QtQml",
        "PyQt6.QtCharts",
        "PyQt6.QtDataVisualization",
    ]
else:
    excludes += ["PyQt6", "qtpy"]

a = Analysis(  # noqa: F821
    [str(ROOT / "packaging" / "cumple_app.py")],
    pathex=[str(ROOT / "src")],
    datas=collect_data_files("cumple"),
    hiddenimports=hidden,
    excludes=excludes,
)
pyz = PYZ(a.pure)  # noqa: F821
exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    exclude_binaries=True,
    name="cumple-app",
    console=False,
    argv_emulation=MAC,
    icon=str(UI / "icon.icns") if MAC else (str(UI / "icon.ico") if WIN else None),
)
coll = COLLECT(exe, a.binaries, a.datas, name="cumple-app")  # noqa: F821
if MAC:
    app = BUNDLE(  # noqa: F821
        coll,
        name="cumple.app",
        icon=str(UI / "icon.icns"),
        bundle_identifier="com.tendaysmusic.cumple",
        version=__version__,
        info_plist={
            "CFBundleName": "cumple",
            "CFBundleDisplayName": "cumple",
            "CFBundleShortVersionString": __version__,
            "CFBundleVersion": __version__,
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "12.0",
            "LSApplicationCategoryType": "public.app-category.music",
            "NSHumanReadableCopyright": "MIT License. Victor E. Diaz.",
            "CFBundleDocumentTypes": [
                {
                    "CFBundleTypeName": "Audio file",
                    "CFBundleTypeRole": "Viewer",
                    "LSHandlerRank": "Alternate",
                    "LSItemContentTypes": [
                        "public.audio",
                        "com.microsoft.waveform-audio",
                        "public.aiff-audio",
                        "org.xiph.flac",
                    ],
                },
                {
                    "CFBundleTypeName": "Delivery folder",
                    "CFBundleTypeRole": "Viewer",
                    "LSHandlerRank": "Alternate",
                    "LSItemContentTypes": ["public.folder"],
                },
            ],
        },
    )
