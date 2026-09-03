"""Generate docs/CONFORMANCE.md: cumple against the official EBU test signals, the true-peak
filter cross-check, and the Leq(m) weighting response against the TASA tolerances.

Run: uv run python scripts/conformance_report.py > docs/CONFORMANCE.md
"""

from __future__ import annotations

import os
import re
from datetime import date
from pathlib import Path

import numpy as np
from scipy.signal import freqz

from cumple import __version__
from cumple.meters import PeakMeter
from cumple.meters.leqm import TASA_M_WEIGHTING, m_weighting_fir
from cumple.meters.measure import measure
from cumple.meters.truepeak import designed_phases

ROOT = Path(os.environ.get("CUMPLE_EBU_TEST_SET", Path.home() / ".cache" / "cumple")) / "ebu-loudness-test-set"


def files_for(case: str) -> list[Path]:
    doc, num = case.split("-")
    pat = re.compile(rf"seq-{doc}-(?:2011-)?{num}(?:[-_.]|$)")
    return sorted(p for p in ROOT.rglob("*.wav") if pat.search(p.name))


def mark(ok: bool) -> str:
    return "✓" if ok else "✗"


def main() -> None:
    print(f"# Conformance report for cumple {__version__}\n")
    print(f"Generated {date.today().isoformat()}. Tolerances are the published ones: EBU Tech 3341 ±0.1 LU for loudness and +0.2/−0.4 dB for true peak; EBU Tech 3342 ±1 LU for loudness range; TASA Standard §1.4.2 per-frequency tolerances for the M-weighting. The EBU Loudness Test Set v5.0 is free from tech.ebu.ch and is not redistributed here.\n")
    if not ROOT.exists():
        print("EBU test set not found; only the synthetic sections follow.\n")
    else:
        print("## EBU Tech 3341: loudness and true peak\n")
        print("| case | file | quantity | expected | measured | ok |")
        print("|---|---|---|---|---|---|")
        total = passed = 0
        rows = [
            ("3341-1", "I/S/M", -23.0), ("3341-2", "I/S/M", -33.0), ("3341-3", "I", -23.0), ("3341-4", "I", -23.0), ("3341-5", "I", -23.0),
            ("3341-6", "I", -23.0), ("3341-7", "I", -23.0), ("3341-8", "I", -23.0), ("3341-9", "max S", -23.0), ("3341-10", "max S", -23.0),
            ("3341-11", "max S", -19.0), ("3341-12", "max M", -23.0), ("3341-13", "max M", -23.0), ("3341-14", "max M", -19.0),
        ]
        for case, qty, expected in rows:
            for f in files_for(case):
                m = measure(f).loudness
                if qty == "I/S/M":
                    vals = [("I", m.integrated), ("max S", m.short_term_max), ("max M", m.momentary_max)]
                elif qty == "I":
                    vals = [("I", m.integrated)]
                elif qty == "max S":
                    vals = [("max S", m.short_term_max)]
                else:
                    vals = [("max M", m.momentary_max)]
                for name, v in vals:
                    ok = abs(v - expected) <= 0.1
                    total += 1
                    passed += ok
                    print(f"| {case} | {f.name} | {name} | {expected:.1f} | {v:.2f} | {mark(ok)} |")
        tp_rows = [("3341-15", -6.0), ("3341-16", -6.0), ("3341-17", -6.0), ("3341-18", -6.0), ("3341-19", 3.0), ("3341-20", 0.0), ("3341-21", 0.0), ("3341-22", 0.0), ("3341-23", 0.0)]
        for case, expected in tp_rows:
            for f in files_for(case):
                v = measure(f).peaks.true_peak_dbtp
                ok = expected - 0.4 <= v <= expected + 0.2
                total += 1
                passed += ok
                print(f"| {case} | {f.name} | true peak | {expected:+.1f} dBTP | {v:+.2f} | {mark(ok)} |")
        print(f"\n**{passed} of {total} readings inside tolerance.**\n")
        print("## EBU Tech 3342: loudness range\n")
        print("| case | file | expected LU | measured | ok |")
        print("|---|---|---|---|---|")
        t2 = p2 = 0
        for case, expected in [("3342-1", 10.0), ("3342-2", 5.0), ("3342-3", 20.0), ("3342-4", 15.0), ("3342-5", 5.0), ("3342-6", 15.0)]:
            for f in files_for(case):
                v = measure(f).loudness.lra
                ok = abs(v - expected) <= 1.0
                t2 += 1
                p2 += ok
                print(f"| {case} | {f.name} | {expected:.0f} | {v:.2f} | {mark(ok)} |")
        print(f"\n**{p2} of {t2} readings inside tolerance.**\n")

    print("## True-peak filter: the ITU table against an independent design\n")
    print("Full-scale tones with 50 ms fades, sampled so the peak falls between samples. The reference is the 48-tap polyphase filter printed in ITU-R BS.1770 Annex 2; the cross-check is a 512-tap Kaiser-windowed interpolator designed here.\n")
    print("| tone | sample peak dBFS | ITU filter dBTP | Kaiser-512 dBTP | ideal |")
    print("|---|---|---|---|---|")
    fs = 48000
    n = fs
    t = np.arange(n) / fs
    fade = int(fs * 0.05)
    ramp = 0.5 - 0.5 * np.cos(np.pi * np.arange(fade) / fade)
    for freq, phase in [(500, np.pi / 4), (1000, np.pi / 4), (2000, np.pi / 4), (8000, 0.0), (12000, np.pi / 4), (20000, np.pi / 3)]:
        x = np.sin(2 * np.pi * freq * t + phase)
        x[:fade] *= ramp
        x[-fade:] *= ramp[::-1]
        x = x[:, None]
        a = PeakMeter(fs, 1)
        a.feed(x)
        b = PeakMeter(fs, 1, phases=designed_phases(128))
        b.feed(x)
        sp = 20 * np.log10(np.abs(x).max())
        print(f"| {freq / 1000:g} kHz | {sp:+.2f} | {a.result().true_peak_dbtp:+.2f} | {b.result().true_peak_dbtp:+.2f} | 0.00 |")
    print()
    print("## Leq(m): M-weighting response against the TASA table\n")
    print("| Hz | TASA dB | tolerance | cumple dB | ok |")
    print("|---|---|---|---|---|")
    h = m_weighting_fir(fs)
    pts = [p for p in TASA_M_WEIGHTING if p[0] < fs / 2]
    _, resp = freqz(h, worN=[p[0] for p in pts], fs=fs)
    okc = 0
    for (f, target, tol), r in zip(pts, resp):
        got = 20 * np.log10(abs(r))
        ok = abs(got - target) <= max(tol, 0.15)
        okc += ok
        print(f"| {f} | {target:+.1f} | ±{tol:g} | {got:+.2f} | {mark(ok)} |")
    print(f"\n**{okc} of {len(pts)} points inside tolerance** (the 6.3 kHz point has a printed tolerance of ±0.0; cumple allows ±0.15 there).\n")


if __name__ == "__main__":
    main()
