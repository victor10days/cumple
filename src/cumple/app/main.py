"""The window: pywebview over the Api. The only module in the package that imports pywebview."""

from __future__ import annotations

import json
import logging
import os
import sys
import webbrowser
from pathlib import Path

from .. import __version__
from . import desktop, selftest, ui
from .api import REPO_URL, SITE_URL, Api

log = logging.getLogger("cumple.app.main")

WEBVIEW2_MESSAGE = (
    "cumple needs the Microsoft Edge WebView2 Runtime, which is free from Microsoft. "
    "The download page opens now; run the installer and start cumple again."
)


def run(paths: list[Path], spec: str | None) -> int:
    """Open the window. Returns the process exit code."""
    desktop.setup_logging()
    log.info("cumple %s starting (frozen=%s, platform=%s)", __version__, getattr(sys, "frozen", False), sys.platform)
    if sys.platform == "win32" and not desktop.webview2_installed():
        desktop.message_box("cumple", WEBVIEW2_MESSAGE)
        webbrowser.open(desktop.WEBVIEW2_DOWNLOAD)
        return 3

    import webview
    from webview.dom import DOMEventHandler
    from webview.menu import Menu, MenuAction, MenuSeparator

    api = Api(initial_paths=[p for p in paths if not str(p).startswith("-psn")], initial_spec=spec)
    window = webview.create_window(
        "cumple",
        html=ui.render(),
        js_api=api,
        width=1180,
        height=780,
        min_size=(760, 520),
        text_select=True,
    )
    api.window = window

    def bind(w) -> None:
        """Runs on a thread once the GUI loop is up: the drop handlers need the DOM."""

        def on_drag(e) -> None:
            pass

        def on_drop(e) -> None:
            files = (e.get("dataTransfer") or {}).get("files") or []
            dropped = [str(f["pywebviewFullPath"]).rstrip("/\\") for f in files if f.get("pywebviewFullPath")]
            log.info("drop: %d files, %d with a path", len(files), len(dropped))
            w.run_js(f"app.onDrop({json.dumps(dropped)}, {len(files)})")

        w.dom.document.events.dragenter += DOMEventHandler(on_drag, True, True)
        w.dom.document.events.dragover += DOMEventHandler(on_drag, True, True, debounce=500)
        w.dom.document.events.drop += DOMEventHandler(on_drop, True, True)

    def closing() -> bool:
        api.shutdown()
        return True

    window.events.closing += closing

    gui = "qt" if sys.platform.startswith("linux") and getattr(sys, "frozen", False) else None
    menu = [
        Menu(
            "File",
            [
                MenuAction("Open files...", lambda: window.run_js("app.pickFiles()")),
                MenuAction("Open folder...", lambda: window.run_js("app.pickFolder()")),
                MenuSeparator(),
                MenuAction("Save PDF", lambda: window.run_js("app.savePdf()")),
            ],
        ),
        Menu(
            "Help",
            [
                MenuAction("cumple on GitHub", lambda: webbrowser.open(REPO_URL)),
                MenuAction("The cumple page", lambda: webbrowser.open(SITE_URL)),
                MenuSeparator(),
                MenuAction(f"cumple {__version__}", lambda: None),
            ],
        ),
    ]
    webview.start(
        bind,
        window,
        gui=gui,
        menu=menu,
        icon=str(ui.icon_path()),
        debug=bool(os.environ.get("CUMPLE_APP_DEBUG")),
    )
    log.info("window closed")
    return 0


def main(argv: list[str] | None = None) -> int:
    """The frozen entry point: `cumple-app [--selftest] [--spec ID] [PATH ...]`, no typer needed."""
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        desktop.setup_logging()
        return selftest.main()
    spec: str | None = None
    paths: list[Path] = []
    while args:
        a = args.pop(0)
        if a in ("--spec", "-s") and args:
            spec = args.pop(0)
        elif a.startswith("--spec="):
            spec = a.split("=", 1)[1]
        elif not a.startswith("-"):
            paths.append(Path(a))
    return run(paths, spec)


if __name__ == "__main__":
    sys.exit(main())
