"""The window's HTML: one template with the tokens, the fonts, the stylesheet and the script inlined."""

from __future__ import annotations

import sys
from importlib import resources
from pathlib import Path

from ..report.style import font_faces_css, tokens_css


def ui_dir() -> Path:
    return Path(str(resources.files("cumple.app") / "ui"))


def render() -> str:
    d = ui_dir()
    html = (d / "index.html").read_text(encoding="utf-8")
    parts = (
        ("/*__TOKENS__*/", tokens_css()),
        ("/*__FONTS__*/", font_faces_css()),
        ("/*__APP_CSS__*/", (d / "app.css").read_text(encoding="utf-8")),
        ("/*__APP_JS__*/", (d / "app.js").read_text(encoding="utf-8")),
    )
    for marker, value in parts:
        html = html.replace(marker, value, 1)
    return html


def icon_path() -> Path:
    name = "icon.icns" if sys.platform == "darwin" else "icon.ico" if sys.platform == "win32" else "icon.png"
    return ui_dir() / name
