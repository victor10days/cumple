"""Channel-layout sanity: is the LFE really an LFE, and is the file in the order it claims?

A 5.1 file is six channels in a row; nothing in the header says which is which. Two
conventions exist: SMPTE/ITU order (L R C LFE Ls Rs), which every streaming spec asks
for, and Film order (L C R Ls Rs LFE), which older Pro Tools sessions default to. The
LFE channel gives the order away: it is the one with almost no energy above 120 Hz.
The same measurement answers Apple's rule that the LFE must not carry full-frequency
content.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import butter, sosfilt, sosfilt_zi

SILENT_DBFS = -60.0  # a channel quieter than this is treated as empty for layout guesses


@dataclass
class LayoutResult:
    corner_hz: float
    rms_dbfs: np.ndarray  # per channel
    hf_ratio_db: np.ndarray  # energy above the corner relative to total, per channel
    lfe_like: int | None  # index of the channel that looks like an LFE, if any

    def silent(self, ch: int) -> bool:
        return self.rms_dbfs[ch] < SILENT_DBFS


class LayoutMeter:
    """Streaming per-channel RMS and high-band energy ratio."""

    def __init__(self, samplerate: int, channels: int, corner_hz: float = 250.0, lfe_ratio_db: float = -15.0):
        self.fs = int(samplerate)
        self.channels = int(channels)
        self.corner_hz = float(corner_hz)
        self.lfe_ratio_db = float(lfe_ratio_db)
        self._sos = butter(6, corner_hz, btype="highpass", fs=self.fs, output="sos")
        zi = sosfilt_zi(self._sos)  # (sections, 2)
        self._zi = np.repeat(zi[:, :, None], self.channels, axis=2) * 0.0
        self._total = np.zeros(self.channels)
        self._high = np.zeros(self.channels)
        self._n = 0

    def feed(self, block: np.ndarray) -> None:
        x = np.asarray(block, dtype=np.float64)
        if x.ndim == 1:
            x = x[:, None]
        hi, self._zi = sosfilt(self._sos, x, axis=0, zi=self._zi)
        self._total += np.sum(x * x, axis=0)
        self._high += np.sum(hi * hi, axis=0)
        self._n += x.shape[0]

    def result(self) -> LayoutResult:
        n = max(self._n, 1)
        with np.errstate(divide="ignore", invalid="ignore"):
            rms = 10 * np.log10(np.where(self._total > 0, self._total / n, np.nan))
            ratio = 10 * np.log10(np.where(self._total > 0, self._high / self._total, np.nan))
        rms = np.where(np.isnan(rms), -np.inf, rms)
        ratio = np.where(np.isnan(ratio), -np.inf, ratio)
        lfe_like = None
        candidates = [i for i in range(self.channels) if rms[i] >= SILENT_DBFS and ratio[i] <= self.lfe_ratio_db]
        if candidates:
            lfe_like = int(min(candidates, key=lambda i: ratio[i]))
        return LayoutResult(corner_hz=self.corner_hz, rms_dbfs=rms, hf_ratio_db=ratio, lfe_like=lfe_like)
