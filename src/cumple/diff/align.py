"""Find how B relates to A before comparing them: time offset, gain, polarity.

Two renders of the same mix rarely line up sample for sample. A one-sample shift makes a
naive subtraction look like a huge difference. So first estimate the shift by
cross-correlation (with sub-sample refinement), the gain by least squares, and the
polarity from the sign of the correlation peak; only then subtract.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import fftconvolve


@dataclass
class Alignment:
    offset_samples: float  # B relative to A: positive means B is late (B[n] ~ A[n - offset])
    gain_db: float  # B relative to A after alignment
    polarity_inverted: bool
    correlation: float  # normalised correlation coefficient after alignment, 0 to 1

    @property
    def offset_ms(self) -> float:
        return 0.0

    def offset_seconds(self, fs: int) -> float:
        return self.offset_samples / fs


def _mono(x: np.ndarray) -> np.ndarray:
    return x.mean(axis=1) if x.ndim == 2 else x


def estimate_offset(
    a: np.ndarray, b: np.ndarray, fs: int, max_offset_s: float = 10.0, analysis_s: float = 60.0
) -> tuple[float, float]:
    """(offset in samples, normalised peak correlation, sign included)."""
    am, bm = _mono(a), _mono(b)
    n = int(min(len(am), len(bm), analysis_s * fs))
    am, bm = am[:n], bm[:n]
    am = am - am.mean()
    bm = bm - bm.mean()
    if not am.any() or not bm.any():
        return 0.0, 0.0
    max_lag = int(min(max_offset_s * fs, n - 1))
    # cross-correlation via FFT: c[k] = sum_n am[n] * bm[n + k - (n-1)]
    c = fftconvolve(bm, am[::-1], mode="full")  # index k corresponds to lag = k - (n - 1)
    lags = np.arange(-(n - 1), n)
    keep = np.abs(lags) <= max_lag
    c, lags = c[keep], lags[keep]
    i = int(np.argmax(np.abs(c)))
    peak = c[i]
    norm = np.sqrt(np.sum(am * am) * np.sum(bm * bm))
    rho = float(peak / norm) if norm > 0 else 0.0
    lag = float(lags[i])
    if 0 < i < len(c) - 1:  # parabolic refinement on the magnitude
        y0, y1, y2 = np.abs(c[i - 1]), np.abs(c[i]), np.abs(c[i + 1])
        denom = y0 - 2 * y1 + y2
        if denom != 0:
            lag += 0.5 * (y0 - y2) / denom
    return lag, rho


def fractional_shift(x: np.ndarray, shift: float) -> np.ndarray:
    """Delay x by `shift` samples (may be fractional, may be negative) using an FFT phase ramp."""
    if abs(shift) < 1e-6:
        return x
    n = x.shape[0]
    nfft = int(2 ** np.ceil(np.log2(n + abs(int(shift)) + 2)))
    freqs = np.fft.rfftfreq(nfft)
    ramp = np.exp(-2j * np.pi * freqs * shift)
    out = np.empty_like(x, dtype=np.float64)
    for ch in range(x.shape[1]):
        spec = np.fft.rfft(x[:, ch], nfft)
        out[:, ch] = np.fft.irfft(spec * ramp, nfft)[:n]
    return out


def overlap_slice(n: int, lag: float, guard: int = 64) -> slice:
    """The sample range where A and the shifted B both carry real content."""
    margin = int(np.ceil(abs(lag))) + guard
    lo = margin if lag < 0 else guard
    hi = n - (margin if lag > 0 else guard)
    if hi - lo < 1024:
        return slice(0, n)
    return slice(lo, hi)


def align(a: np.ndarray, b: np.ndarray, fs: int, max_offset_s: float = 10.0) -> tuple[Alignment, np.ndarray]:
    """Return B's offset and polarity relative to A, and B shifted and polarity-fixed to sit on A.

    Gain is estimated later from band levels (see compare.py), so gain_db is filled there.
    """
    lag, rho = estimate_offset(a, b, fs, max_offset_s)
    inverted = rho < 0
    b_al = fractional_shift(b, -lag)  # undo B's lateness
    if inverted:
        b_al = -b_al
    return Alignment(
        offset_samples=float(lag), gain_db=0.0, polarity_inverted=bool(inverted), correlation=float(abs(rho))
    ), b_al
