"""Audio repair: De-click and De-clip through a compiled DSP core, and the harness that scores them.

The compiled core is the separate distribution `cumple-dsp` (import name `cumple_dsp`). The
metrics, the synthetic damage, the parameters, the chains and the receipt in this package are pure
Python and need no core; the runner (`runner.repair_file`) does, and calls `require()` first.
"""

from __future__ import annotations

import importlib.util

INSTALL_ROUTE = (
    'uv tool install --python 3.12 "cumple[repair] @ git+https://github.com/victor10days/cumple", which '
    "compiles the Rust core, so it needs cargo (https://rustup.rs); from a clone, uv sync --extra repair. "
    "cumple is not on PyPI, so pip install will not find it"
)


class RepairUnavailable(RuntimeError):
    """The compiled DSP core is not installed; the message names the install route."""


def available() -> bool:
    """True when the compiled core (`cumple_dsp`) can be imported."""
    return importlib.util.find_spec("cumple_dsp") is not None


def require() -> None:
    """Raise RepairUnavailable, with the install route, unless the compiled core is present."""
    if not available():
        raise RepairUnavailable(
            f"audio repair needs the compiled core (cumple_dsp), which is not installed. Install it with {INSTALL_ROUTE}"
        )
