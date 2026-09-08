"""Small platform helpers for the desktop app: reveal a path, the WebView2 check, settings, logging.

Nothing here imports pywebview, so the API and the tests use it headless on any platform.
"""

from __future__ import annotations

import faulthandler
import json
import logging
import os
import platform
import subprocess
import sys
import threading
from collections.abc import Callable
from pathlib import Path

from ..specs.registry import user_dir

log = logging.getLogger("cumple.app")

# The Evergreen WebView2 runtime registers this client id under EdgeUpdate (HKLM or HKCU, 64-bit or
# WOW6432Node). pywebview falls back to IE11 silently when it is missing, so the app checks first.
WEBVIEW2_CLIENT = r"Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
WEBVIEW2_DOWNLOAD = "https://developer.microsoft.com/microsoft-edge/webview2/"


def _registry_reader(hive: str, key: str, value: str) -> str | None:
    import winreg  # Windows only; the caller guards the platform

    root = {"HKLM": winreg.HKEY_LOCAL_MACHINE, "HKCU": winreg.HKEY_CURRENT_USER}[hive]
    try:
        with winreg.OpenKey(root, key) as k:
            v, _ = winreg.QueryValueEx(k, value)
            return str(v)
    except OSError:
        return None


def webview2_installed(reader: Callable[[str, str, str], str | None] | None = None) -> bool:
    """True when the WebView2 runtime is registered; `reader(hive, key, value)` is injectable for tests."""
    reader = reader or _registry_reader
    for hive in ("HKLM", "HKCU"):
        for prefix in ("SOFTWARE\\WOW6432Node\\", "SOFTWARE\\"):
            pv = reader(hive, prefix + WEBVIEW2_CLIENT, "pv")
            if pv and pv != "0.0.0.0":
                return True
    return False


def reveal_command(path: Path | str, system: str | None = None) -> list[str]:
    """The command that shows `path` in the file manager: Finder, Explorer, or the folder on Linux."""
    system = system or platform.system()
    p = Path(path)
    if system == "Darwin":
        return ["open", "-R", str(p)]
    if system == "Windows":
        return ["explorer", "/select,", str(p)]
    return ["xdg-open", str(p if p.is_dir() else p.parent)]


def reveal(path: Path | str) -> bool:
    try:
        subprocess.Popen(reveal_command(path), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError as e:
        log.warning("cannot reveal %s: %s", path, e)
        return False
    return True


def message_box(title: str, text: str) -> None:
    """A native error box on Windows (the only platform that needs one before a window exists)."""
    if sys.platform == "win32":
        import ctypes

        ctypes.windll.user32.MessageBoxW(None, text, title, 0x10)  # MB_ICONERROR
    else:
        print(f"{title}: {text}", file=sys.stderr)


def log_path() -> Path:
    system = platform.system()
    if system == "Darwin":
        base = Path.home() / "Library" / "Logs" / "cumple"
    elif system == "Windows":
        base = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))) / "cumple"
    else:
        base = Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local" / "state"))) / "cumple"
    return base / "app.log"


def settings_path() -> Path:
    """`~/.config/cumple/app.json` (or under `$XDG_CONFIG_HOME`), next to the user profiles directory."""
    return user_dir().parent / "app.json"


def load_settings() -> dict:
    try:
        data = json.loads(settings_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def save_settings(values: dict) -> dict:
    current = load_settings()
    current.update({k: v for k, v in values.items() if v is not None})
    p = settings_path()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(current, indent=2), encoding="utf-8")
    except OSError as e:
        log.warning("cannot save settings to %s: %s", p, e)
    return current


def setup_logging() -> Path | None:
    """Log to a file as well as stderr: a windowed build has no console, and CI reads the file."""
    handlers: list[logging.Handler] = []
    if sys.stderr is not None:
        handlers.append(logging.StreamHandler())
    path: Path | None = log_path()
    try:
        assert path is not None
        path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(path, encoding="utf-8"))
    except OSError:
        path = None
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handlers,
        force=True,
    )
    try:
        faulthandler.enable(file=sys.stderr if sys.stderr is not None else open(path, "a"))  # noqa: SIM115
    except (OSError, TypeError, AttributeError):
        pass

    def excepthook(exc_type, exc, tb):
        log.error("uncaught exception", exc_info=(exc_type, exc, tb))

    def thread_hook(args):
        log.error("uncaught exception in a thread", exc_info=(args.exc_type, args.exc_value, args.exc_traceback))

    sys.excepthook = excepthook
    threading.excepthook = thread_hook
    return path
