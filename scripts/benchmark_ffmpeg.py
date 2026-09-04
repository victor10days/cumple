"""Compare cumple with ffmpeg's ebur128 filter and pyloudnorm on the official EBU test signals.

Run: uv run python scripts/benchmark_ffmpeg.py > docs/BENCHMARK.md
Needs the EBU Loudness Test Set unpacked under ~/.cache/cumple (see tests/test_ebu_conformance.py),
ffmpeg on PATH, and the dev dependency group (pyloudnorm).
"""

from __future__ import annotations

import glob
import os
import re
import subprocess
from datetime import date
from importlib.metadata import version as dist_version

import numpy as np
import pyloudnorm
import soundfile as sf

from cumple import __version__
from cumple.meters.measure import measure

ROOT = os.path.expanduser("~/.cache/cumple/ebu-loudness-test-set")
CASES = [
    ("seq-3341-1-16bit.wav", -23.0, None, None),
    ("seq-3341-2-16bit.wav", -33.0, None, None),
    ("seq-3341-3-16bit-v02.wav", -23.0, None, None),
    ("seq-3341-4-16bit-v02.wav", -23.0, None, None),
    ("seq-3341-5-16bit-v02.wav", -23.0, None, None),
    ("seq-3341-6-5channels-16bit.wav", -23.0, None, None),
    ("seq-3341-6-6channels-WAVEEX-16bit.wav", -23.0, None, None),
    ("seq-3341-7_seq-3342-5-24bit.wav", -23.0, None, 5.0),
    ("seq-3341-2011-8_seq-3342-6-24bit-v02.wav", -23.0, None, 15.0),
    ("seq-3341-15-24bit.wav.wav", None, -6.0, None),
    ("seq-3341-16-24bit.wav.wav", None, -6.0, None),
    ("seq-3341-19-24bit.wav.wav", None, 3.0, None),
    ("seq-3341-20-24bit.wav.wav", None, 0.0, None),
    ("seq-3341-23-24bit.wav.wav", None, 0.0, None),
    ("seq-3342-1-16bit.wav", None, None, 10.0),
    ("seq-3342-2-16bit.wav", None, None, 5.0),
    ("seq-3342-3-16bit.wav", None, None, 20.0),
    ("seq-3342-4-16bit.wav", None, None, 15.0),
]


def ffmpeg_summary(path: str) -> tuple[float, float, float]:
    out = subprocess.run(
        ["ffmpeg", "-nostats", "-hide_banner", "-i", path, "-filter_complex", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True,
        text=True,
    ).stderr
    tail = out.split("Summary:")[-1]
    i = re.search(r"I:\s+(-?[\d.]+) LUFS", tail)
    lra = re.search(r"LRA:\s+(-?[\d.]+) LU", tail)
    tp = re.search(r"Peak:\s+(-?[\d.]+) dBFS", tail)
    return tuple(float(x.group(1)) if x else float("nan") for x in (i, tp, lra))


def pyloudnorm_integrated(path: str) -> float:
    """Whole-file integrated loudness from pyloudnorm.

    pyloudnorm takes at most five channels in L R C Ls Rs order, so a six-channel
    L R C LFE Ls Rs file has its LFE removed first (BS.1770 excludes it anyway).
    """
    data, rate = sf.read(path, always_2d=True, dtype="float64")
    if data.shape[1] == 6:
        data = np.delete(data, 3, axis=1)
    return float(pyloudnorm.Meter(rate).integrated_loudness(data))


def fmt(x, expected=None, kind="I"):
    """kind: I (±0.1 LU), TP (+0.2/−0.4 dBTP per Tech 3341), LRA (±1 LU per Tech 3342)."""
    if x is None:
        return ""
    s = f"{x:.2f}"
    if expected is not None:
        if kind == "TP":
            ok = expected - 0.4 <= x <= expected + 0.2
        elif kind == "LRA":
            ok = abs(x - expected) <= 1.0
        else:
            ok = abs(x - expected) <= 0.1
        s += " ✓" if ok else " ✗"
    return s


def main() -> None:
    ff = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True).stdout.split("\n")[0]
    print("# cumple vs ffmpeg ebur128 and pyloudnorm on the EBU Loudness Test Set v5.0\n")
    print(
        f"Generated {date.today().isoformat()} with cumple {__version__}, `{ff}` and pyloudnorm {dist_version('pyloudnorm')}. "
        "Expected values from EBU Tech 3341 Table 1 (±0.1 LU; true peak +0.2/−0.4 dBTP) and Tech 3342 (±1 LU). "
        "✓ means inside the published tolerance. pyloudnorm measures integrated loudness only (no true peak, no loudness range), so it has one column.\n"
    )
    print("| file | expected | cumple I | ffmpeg I | pyloudnorm I | cumple TP | ffmpeg TP | cumple LRA | ffmpeg LRA |")
    print("|---|---|---|---|---|---|---|---|---|")
    for name, ei, etp, elra in CASES:
        hits = glob.glob(f"{ROOT}/**/{name}", recursive=True)
        if not hits:
            continue
        m = measure(hits[0])
        fi, ftp, flra = ffmpeg_summary(hits[0])
        pi = pyloudnorm_integrated(hits[0])
        exp = " ".join(
            x
            for x in [
                f"I {ei:g}" if ei is not None else "",
                f"TP {etp:+g}" if etp is not None else "",
                f"LRA {elra:g}" if elra is not None else "",
            ]
            if x
        )
        print(
            f"| {name} | {exp} | {fmt(m.loudness.integrated, ei)} | {fmt(fi, ei)} | {fmt(pi, ei)} | {fmt(m.peaks.true_peak_dbtp, etp, 'TP')} | {fmt(ftp, etp, 'TP')} | {fmt(m.loudness.lra, elra, 'LRA')} | {fmt(flra, elra, 'LRA')} |"
        )
    print(
        "\nNotes: ffmpeg's ebur128 is an independent implementation with no published conformance report. "
        "On the five- and six-channel case 6 files it reports a true peak of −28 dBFS where the centre channel sits at −24 dBFS; cumple reports the centre channel. "
        "On the true-peak burst files ffmpeg reports a loudness range of about 20 LU for what is a single steady tone; those files carry no LRA expectation in Tech 3342, so this is noted, not scored. "
        "pyloudnorm reads the whole file into memory and takes at most five channels, so the six-channel case 6 file was passed to it without its LFE channel; cumple and ffmpeg read the file as delivered."
    )
    print("\nSpeed and memory on long programmes are in [PERF.md](PERF.md).")


if __name__ == "__main__":
    main()
