"""Entry point for the frozen desktop app (PyInstaller). `cumple app` from the CLI does the same through typer."""

import sys

from cumple.app.main import main

if __name__ == "__main__":
    sys.exit(main())
