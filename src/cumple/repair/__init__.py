"""Audio repair: De-click and De-clip through a compiled DSP core, and the harness that scores them.

The compiled core is the separate distribution `cumple-dsp` (import name `cumple_dsp`). The
metrics and the synthetic damage in this package are pure numpy and need no core.
"""

from __future__ import annotations

import importlib.util

INSTALL_ROUTE = (
    'uv tool install "cumple[repair]" from the git repository: it compiles the Rust core, so it needs cargo. '
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
            f"audio repair needs the compiled core (cumple_dsp), which is not installed: {INSTALL_ROUTE}"
        )
