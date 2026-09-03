"""Leq(m): the cinema trailer loudness measure (ISO 21727, TASA, SAWA).

The M-weighting curve is the ITU-R 468 noise-weighting curve offset so that 2 kHz reads
0 dB, with RMS integration instead of a quasi-peak detector. The TASA Standard prints the
response and its tolerances (section 1.4.2), and that table is what the filter here is
designed from, so the response can be checked against the same tolerances.

Method, as TASA describes it: each channel gets its own weighting and detector, the
detector outputs are summed in proportion to the room calibration (surrounds 3 dB below
screen channels), and the result is averaged over the whole duration.

Calibration convention (cumple's stated choice, printed in the profile): an M-weighted RMS
level of -20 dBFS on one screen channel corresponds to 85 dB. TASA's own example calibrates
-20 dBFS to 85 dBC SPL per channel with pink noise; a single number is needed to turn a
file into dB, and this is it.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import fftconvolve, firwin2

# TASA Standard §1.4.2: frequency (Hz), response (dB), tolerance (dB).
TASA_M_WEIGHTING = [
    (31, -35.5, 2.0),
    (63, -29.5, 1.4),
    (100, -25.4, 1.0),
    (200, -19.4, 0.85),
    (400, -13.4, 0.7),
    (800, -7.5, 0.55),
    (1000, -5.6, 0.5),
    (2000, 0.0, 0.5),
    (3150, 3.4, 0.5),
    (4000, 4.9, 0.5),
    (5000, 6.1, 0.5),
    (6300, 6.6, 0.0),
    (7100, 6.4, 0.2),
    (8000, 5.8, 0.4),
    (9000, 4.5, 0.6),
    (10000, 2.5, 0.8),
    (12500, -5.6, 1.2),
    (14000, -10.9, 1.4),
    (16000, -17.3, 1.65),
    (20000, -27.8, 2.0),
    (31500, -48.3, 2.8),
]
CALIBRATION_DBFS = -20.0
CALIBRATION_DB = 85.0
SURROUND_OFFSET_DB = -3.0
LFE_OFFSET_DB = 10.0  # cinema LFE is reproduced 10 dB hotter in band; the curve removes most of it anyway
INTERVAL_S = 1.0

SCREEN = {"L", "R", "C", "Lc", "Rc", "M", "Lt", "Rt"}
SURROUND = {"Ls", "Rs", "Lss", "Rss", "Lrs", "Rrs"}


def m_weighting_fir(fs: int, numtaps: int = 8191) -> np.ndarray:
    """Linear-phase FIR whose magnitude follows the TASA table (log-frequency interpolation)."""
    pts = np.array([(f, g) for f, g, _ in TASA_M_WEIGHTING], dtype=float)
    nyq = fs / 2
    grid = np.concatenate([[0.0], np.geomspace(10.0, nyq, 512)])
    # dB response: extrapolate below 31 Hz at 12 dB/octave, above 31.5 kHz keep falling
    logf = np.log10(np.maximum(grid, 1e-3))
    gains_db = np.interp(logf, np.log10(pts[:, 0]), pts[:, 1])
    low = grid < pts[0, 0]
    gains_db[low] = pts[0, 1] - 40 * np.log10(pts[0, 0] / np.maximum(grid[low], 1.0))
    gains_db[0] = -120.0
    high = grid > pts[-1, 0]
    gains_db[high] = pts[-1, 1] - 40 * np.log10(grid[high] / pts[-1, 0])
    gains = 10 ** (gains_db / 20)
    freqs = grid / nyq
    freqs[-1] = 1.0
    return firwin2(numtaps, freqs, gains)


@dataclass
class LeqmResult:
    leqm_db: float
    per_second_db: np.ndarray
    calibration_dbfs: float
    calibration_db: float
    channel_weights_db: dict[str, float]


class LeqmMeter:
    """Streaming Leq(m) with per-channel overlap-save FIR filtering."""

    def __init__(
        self,
        samplerate: int,
        channels: int,
        roles: list[str] | None = None,
        calibration_dbfs: float = CALIBRATION_DBFS,
        calibration_db: float = CALIBRATION_DB,
        surround_offset_db: float = SURROUND_OFFSET_DB,
    ):
        self.fs = int(samplerate)
        self.channels = int(channels)
        self.roles = roles or ["L"] * channels
        self.h = m_weighting_fir(self.fs)
        self._tail = np.zeros((len(self.h) - 1, self.channels))
        self.interval = int(self.fs * INTERVAL_S)
        self._pending = np.empty((0, self.channels))
        self._interval_energy: list[float] = []
        self.offset_db = calibration_db - calibration_dbfs  # dB per dBFS of M-weighted RMS
        self.channel_weights_db = {}
        w = np.ones(self.channels)
        for i, r in enumerate(self.roles):
            if r in SURROUND:
                w[i] = 10 ** (surround_offset_db / 10)
                self.channel_weights_db[r] = surround_offset_db
            elif r == "LFE":
                w[i] = 10 ** (LFE_OFFSET_DB / 10)
                self.channel_weights_db[r] = LFE_OFFSET_DB
            else:
                self.channel_weights_db[r] = 0.0
        self.weights = w

    def feed(self, block: np.ndarray) -> None:
        x = np.asarray(block, dtype=np.float64)
        if x.ndim == 1:
            x = x[:, None]
        xx = np.concatenate([self._tail, x])
        y = fftconvolve(xx, self.h[:, None], mode="full", axes=0)[len(self._tail) : len(self._tail) + len(x)]
        self._tail = xx[-(len(self.h) - 1) :]
        y = np.concatenate([self._pending, y]) if self._pending.size else y
        n = len(y) // self.interval
        if n:
            whole = y[: n * self.interval].reshape(n, self.interval, self.channels)
            e = np.mean(whole * whole, axis=1) @ self.weights  # summed detector outputs, per second
            self._interval_energy.extend(e)
        self._pending = y[n * self.interval :]

    def result(self) -> LeqmResult:
        energies = list(self._interval_energy)
        if self._pending.size:
            energies.append(float(np.mean(self._pending * self._pending, axis=0) @ self.weights))
        e = np.asarray(energies)
        with np.errstate(divide="ignore"):
            per_second = np.where(e > 0, 10 * np.log10(np.maximum(e, 1e-30)) + self.offset_db, -np.inf)
        mean_e = float(e.mean()) if e.size else 0.0
        leqm = 10 * np.log10(mean_e) + self.offset_db if mean_e > 0 else -np.inf
        return LeqmResult(float(leqm), per_second, CALIBRATION_DBFS, CALIBRATION_DB, self.channel_weights_db)
