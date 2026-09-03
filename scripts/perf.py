"""Performance on long files: wall time, real-time factor and peak memory.

Generates synthetic programmes under ~/.cache/cumple/perf (not in the repo), runs
`cumple check` on each through /usr/bin/time -l, and prints a Markdown section.

Run: uv run python scripts/perf.py > docs/PERF.md
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

import numpy as np
import soundfile as sf

from cumple import __version__

OUT = Path.home() / ".cache" / "cumple" / "perf"
FS = 48000
CASES = [("stereo-5min.wav", 2, 5), ("stereo-60min.wav", 2, 60), ("5.1-30min.wav", 6, 30)]


def make(path: Path, channels: int, minutes: int) -> None:
    if path.exists():
        return
    rng = np.random.default_rng(1)
    chunk = FS * 10
    with sf.SoundFile(str(path), "w", samplerate=FS, channels=channels, subtype="PCM_24") as fh:
        for _ in range(minutes * 6):
            x = rng.normal(0, 0.05, size=(chunk, channels))
            # a slow level swell so the gates and LRA have something to do
            fh.write(x * (0.5 + 0.5 * np.abs(np.sin(np.linspace(0, np.pi, chunk)))[:, None]))


def run(path: Path) -> tuple[float, float]:
    cmd = ["/usr/bin/time", "-l", sys.executable, "-m", "cumple.cli", "check", str(path), "--spec", "ebu-r128", "--json"]
    t0 = time.time()
    res = subprocess.run(cmd, capture_output=True, text=True)
    wall = time.time() - t0
    m = re.search(r"(\d+)\s+maximum resident set size", res.stderr)
    rss = int(m.group(1)) / 1e6 if m else float("nan")
    return wall, rss


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"# Performance of cumple {__version__}\n")
    print(f"Generated {date.today().isoformat()} on this machine ({os.uname().machine}); synthetic 24-bit PCM programmes at 48 kHz. Peak memory is the maximum resident set size reported by `/usr/bin/time -l` for the whole `cumple check --json` process, Python and NumPy included.\n")
    print("| file | channels | duration | file size | wall time | real-time factor | peak memory |")
    print("|---|---|---|---|---|---|---|")
    for name, ch, minutes in CASES:
        p = OUT / name
        make(p, ch, minutes)
        wall, rss = run(p)
        size = p.stat().st_size / 1e9
        print(f"| {name} | {ch} | {minutes} min | {size:.2f} GB | {wall:.0f} s | {minutes * 60 / wall:.0f}x | {rss:.0f} MB |")
    print("\nMemory should not grow with duration: the meters keep 10 ms energies and filter state, never the audio.")


if __name__ == "__main__":
    main()
