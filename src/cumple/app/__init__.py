"""The desktop app: a webview over the same engine the CLI uses.

`cumple app` opens it; `packaging/cumple.spec` freezes it. Only `main.py` imports pywebview, so the
API and its tests run headless.
"""
