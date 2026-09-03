"""Say what changed between two renders, in the terms a mixer thinks in."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import welch

from ..meters.bs1770 import LoudnessMeter
from ..meters.truepeak import PeakMeter
from .align import Alignment, align, overlap_slice

THIRD_OCTAVE_CENTERS = [
    25,
    31.5,
    40,
    50,
    63,
    80,
    100,
    125,
    160,
    200,
    250,
    315,
    400,
    500,
    630,
    800,
    1000,
    1250,
    1600,
    2000,
    2500,
    3150,
    4000,
    5000,
    6300,
    8000,
    10000,
    12500,
    16000,
    20000,
]
MAX_SECONDS_IN_MEMORY = 40 * 60


@dataclass
class Levels:
    integrated: float
    lra: float
    true_peak: float
    sample_peak: float
    rms_dbfs: float


@dataclass
class DiffResult:
    a: Path
    b: Path
    fs: int
    channels: int
    duration_a_s: float
    duration_b_s: float
    alignment: Alignment
    identical: bool  # sample-exact
    residual_dbfs: float  # RMS of A minus corrected B
    residual_rel_db: float  # residual relative to the RMS of A
    residual_peak_dbfs: float
    levels_a: Levels
    levels_b: Levels
    band_deltas: list[tuple[float, float]] = field(default_factory=list)  # (centre Hz, B minus A in dB)
    stems: list[Path] = field(default_factory=list)  # in stem-sum mode, the files that were summed
    notes: list[str] = field(default_factory=list)

    @property
    def loudness_delta(self) -> float:
        return self.levels_b.integrated - self.levels_a.integrated

    @property
    def true_peak_delta(self) -> float:
        return self.levels_b.true_peak - self.levels_a.true_peak


def _db(x: float) -> float:
    return float(20 * np.log10(x)) if x > 0 else -np.inf


def levels(x: np.ndarray, fs: int) -> Levels:
    lm = LoudnessMeter(fs, x.shape[1])
    pm = PeakMeter(fs, x.shape[1])
    for i in range(0, len(x), 1 << 18):
        blk = x[i : i + (1 << 18)]
        lm.feed(blk)
        pm.feed(blk)
    lr, pr = lm.result(), pm.result()
    rms = float(np.sqrt(np.mean(x * x))) if x.size else 0.0
    return Levels(
        integrated=lr.integrated,
        lra=lr.lra,
        true_peak=pr.true_peak_dbtp,
        sample_peak=pr.sample_peak_dbfs,
        rms_dbfs=_db(rms),
    )


def band_levels(x: np.ndarray, fs: int) -> np.ndarray:
    """Third-octave band levels in dBFS (power in each band, mono fold)."""
    m = x.mean(axis=1) if x.ndim == 2 else x
    nper = min(8192, len(m))
    f, p = welch(m, fs=fs, nperseg=nper)
    out = []
    for c in THIRD_OCTAVE_CENTERS:
        lo, hi = c / 2 ** (1 / 6), c * 2 ** (1 / 6)
        if hi > fs / 2:
            out.append(-np.inf)
            continue
        sel = (f >= lo) & (f < hi)
        power = float(np.trapezoid(p[sel], f[sel])) if sel.sum() > 1 else float(p[sel].sum() * (f[1] - f[0]))
        out.append(10 * np.log10(power) if power > 0 else -np.inf)
    return np.array(out)


def load(path: Path) -> tuple[np.ndarray, int]:
    info = sf.info(str(path))
    if info.duration > MAX_SECONDS_IN_MEMORY:
        raise ValueError(
            f"{path.name} is {info.duration / 60:.0f} minutes long; diff loads whole files and stops at {MAX_SECONDS_IN_MEMORY // 60} minutes"
        )
    x, fs = sf.read(str(path), dtype="float64", always_2d=True)
    return x, fs


def diff_arrays(
    a: np.ndarray,
    b: np.ndarray,
    fs: int,
    a_name: str = "A",
    b_name: str = "B",
    max_offset_s: float = 10.0,
    fit_gain: bool = True,
) -> DiffResult:
    """Compare B with A. fit_gain=False reports the level difference but does not remove it
    from the residual (stems must match the printmaster at level, so a level change is a fault)."""
    if a.shape[1] != b.shape[1]:
        raise ValueError(f"channel counts differ: {a.shape[1]} vs {b.shape[1]}")
    identical = a.shape == b.shape and bool(np.array_equal(a, b))
    alignment, b_al = align(a, b, fs, max_offset_s=max_offset_s)
    n = min(len(a), len(b_al))
    region = overlap_slice(n, alignment.offset_samples)
    a_r, b_r = a[:n][region], b_al[:n][region]
    # Gain = the median band-level change: a broadband level change moves every band by the
    # same amount, while an EQ change moves a few. Least squares would confuse the two.
    ba, bb = band_levels(a_r, fs), band_levels(b_r, fs)
    valid = [
        (c, float(y - x))
        for c, x, y in zip(THIRD_OCTAVE_CENTERS, ba, bb, strict=True)
        if np.isfinite(x) and np.isfinite(y) and max(x, y) > -90
    ]
    gain_db = float(np.median([d for _, d in valid])) if valid else 0.0
    alignment.gain_db = gain_db
    b_corr = b_r / 10 ** (gain_db / 20) if fit_gain else b_r
    resid = a_r - b_corr
    a_rms = float(np.sqrt(np.mean(a_r**2))) if a_r.size else 0.0
    r_rms = float(np.sqrt(np.mean(resid**2))) if resid.size else 0.0
    la, lb = levels(a, fs), levels(b, fs)
    deltas = valid
    notes = []
    if len(a) != len(b):
        notes.append(f"lengths differ: {len(a) / fs:.3f} s vs {len(b) / fs:.3f} s; compared over the overlap")
    if alignment.correlation < 0.3:
        notes.append("the two files barely correlate; they may not be the same material")
    return DiffResult(
        a=Path(a_name),
        b=Path(b_name),
        fs=fs,
        channels=a.shape[1],
        duration_a_s=len(a) / fs,
        duration_b_s=len(b) / fs,
        alignment=alignment,
        identical=identical,
        residual_dbfs=_db(r_rms),
        residual_rel_db=(_db(r_rms) - _db(a_rms)) if a_rms > 0 and r_rms > 0 else -np.inf,
        residual_peak_dbfs=_db(float(np.abs(resid).max())) if resid.size else -np.inf,
        levels_a=la,
        levels_b=lb,
        band_deltas=deltas,
        notes=notes,
    )


def diff_files(a: Path, b: Path, max_offset_s: float = 10.0) -> DiffResult:
    xa, fa = load(Path(a))
    xb, fb = load(Path(b))
    if fa != fb:
        raise ValueError(f"sample rates differ: {fa} vs {fb}; resample one side first")
    r = diff_arrays(xa, xb, fa, a_name=str(a), b_name=str(b), max_offset_s=max_offset_s)
    r.a, r.b = Path(a), Path(b)
    return r


def sum_stems_against(stems: list[Path], printmaster: Path, max_offset_s: float = 2.0) -> DiffResult:
    """Sum the stems sample by sample and diff the sum against the printmaster."""
    xs, fss = zip(*(load(Path(s)) for s in stems), strict=True)
    fs = fss[0]
    if len(set(fss)) != 1:
        raise ValueError(f"stems have different sample rates: {sorted(set(fss))}")
    chans = {x.shape[1] for x in xs}
    if len(chans) != 1:
        raise ValueError(f"stems have different channel counts: {sorted(chans)}")
    n = min(len(x) for x in xs)
    total = sum(x[:n] for x in xs)
    pm, fpm = load(Path(printmaster))
    if fpm != fs:
        raise ValueError(f"printmaster sample rate {fpm} differs from the stems' {fs}")
    r = diff_arrays(
        pm, total, fs, a_name=str(printmaster), b_name="sum of stems", max_offset_s=max_offset_s, fit_gain=False
    )
    r.a = Path(printmaster)
    r.stems = [Path(s) for s in stems]
    return r
