"""A frozen build proves itself: the profiles load, the fonts are embedded, a tone measures right, a sheet renders.

`cumple-app --selftest` runs this on every platform in CI, where nobody can click a window.
"""

from __future__ import annotations

import json
import logging
import sys
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

from .. import __version__
from ..checks.engine import evaluate
from ..meters.measure import measure, measure_args
from ..report.qc_sheet import find_chrome, render_html
from ..report.style import document_css
from ..specs.registry import get, load_all

log = logging.getLogger("cumple.app.selftest")


def run() -> dict:
    profiles = len(load_all())
    fonts = document_css().count("@font-face")
    with tempfile.TemporaryDirectory(prefix="cumple-selftest-") as d:
        path = Path(d) / "tone.wav"
        t = np.arange(int(48000 * 2.0)) / 48000
        x = 10 ** (-23 / 20) * np.sin(2 * np.pi * 1000 * t)  # a -23 dBFS 1 kHz tone reads -23 LUFS on both channels
        sf.write(path, np.column_stack([x, x]), 48000, subtype="PCM_24")
        profile = get("ebu-r128")
        report = evaluate(profile, measure(path, **measure_args(profile)))
        sheet = render_html(report)
    return {
        "version": __version__,
        "python": sys.version.split()[0],
        "frozen": bool(getattr(sys, "frozen", False)),
        "profiles": profiles,
        "fonts": fonts,
        "integrated_lufs": round(report.measurement.loudness.integrated, 2),
        "verdict": report.verdict,
        "sheet_bytes": len(sheet),
        "chrome": find_chrome(),
    }


def ok(result: dict) -> bool:
    return (
        result["profiles"] >= 39
        and result["fonts"] == 5
        and result["verdict"] == "PASS"
        and abs(result["integrated_lufs"] + 23.0) < 0.2
        and result["sheet_bytes"] > 5000
    )


def main() -> int:
    result = run()
    line = json.dumps(result)
    log.info("selftest %s", line)
    if sys.stdout is not None:
        print(line)
    return 0 if ok(result) else 1
