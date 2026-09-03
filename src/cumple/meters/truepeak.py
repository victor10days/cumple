"""Sample peak and true peak (ITU-R BS.1770 Annex 2).

A sample peak only sees the samples. The waveform between them can go higher: a
full-scale sine at a quarter of the sample rate, sampled at 45 degrees, never has a
sample above -3.01 dBFS yet peaks at 0 dBTP between samples. True peak oversamples
by four with the polyphase interpolation filter printed in the standard and reads
the peak of that. The standard's own tolerance for this filter is +0.2/-0.4 dB.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import firwin, lfilter

OVERSAMPLE = 4

# BS.1770 Annex 2, Table 1: the 4x interpolation filter as four 12-tap phases.
# Phases 0/3 and 1/2 are mirror images, as they must be for a symmetric FIR.
BS1770_PHASES = np.array(
    [
        [0.0017089843750, 0.0109863281250, -0.0196533203125, 0.0332031250000, -0.0594482421875, 0.1373291015625,
         0.9721679687500, -0.1022949218750, 0.0476074218750, -0.0266113281250, 0.0148925781250, -0.0083007812500],
        [-0.0291748046875, 0.0292968750000, -0.0517578125000, 0.0891113281250, -0.1665039062500, 0.4650878906250,
         0.7797851562500, -0.2003173828125, 0.1015625000000, -0.0582275390625, 0.0330810546875, -0.0189208984375],
        [-0.0189208984375, 0.0330810546875, -0.0582275390625, 0.1015625000000, -0.2003173828125, 0.7797851562500,
         0.4650878906250, -0.1665039062500, 0.0891113281250, -0.0517578125000, 0.0292968750000, -0.0291748046875],
        [-0.0083007812500, 0.0148925781250, -0.0266113281250, 0.0476074218750, -0.1022949218750, 0.9721679687500,
         0.1373291015625, -0.0594482421875, 0.0332031250000, -0.0196533203125, 0.0109863281250, 0.0017089843750],
    ]
)


def designed_phases(taps_per_phase: int = 24, oversample: int = OVERSAMPLE) -> np.ndarray:
    """An independently designed windowed-sinc interpolator, used to cross-check the ITU table."""
    n = taps_per_phase * oversample
    h = oversample * firwin(n, 1.0 / oversample, window=("kaiser", 8.0))
    return h.reshape(taps_per_phase, oversample).T  # (phases, taps)


def to_db(x: np.ndarray | float) -> np.ndarray | float:
    x = np.asarray(x, dtype=np.float64)
    with np.errstate(divide="ignore"):
        out = 20.0 * np.log10(np.where(x > 0, x, np.nan))
    out = np.where(np.isnan(out), -np.inf, out)
    return float(out) if out.ndim == 0 else out


@dataclass
class PeakResult:
    true_peak_dbtp: float
    sample_peak_dbfs: float
    true_peak_per_channel: np.ndarray
    sample_peak_per_channel: np.ndarray
    clipped_runs: int = 0  # runs of 3+ consecutive samples at or above full scale


class PeakMeter:
    """Streaming sample-peak and true-peak meter."""

    def __init__(self, samplerate: int, channels: int, phases: np.ndarray | None = None, clip_threshold: float = 0.999):
        self.fs = int(samplerate)
        self.channels = int(channels)
        self.phases = BS1770_PHASES if phases is None else np.asarray(phases, dtype=np.float64)
        taps = self.phases.shape[1]
        self._zi = [np.zeros((taps - 1, self.channels)) for _ in self.phases]
        self._true = np.zeros(self.channels)
        self._sample = np.zeros(self.channels)
        self._clip_threshold = clip_threshold
        self._clip_runs = 0
        self._clip_run_open = np.zeros(self.channels, dtype=int)

    def feed(self, block: np.ndarray) -> None:
        x = np.asarray(block, dtype=np.float64)
        if x.ndim == 1:
            x = x[:, None]
        ax = np.abs(x)
        self._sample = np.maximum(self._sample, ax.max(axis=0))
        for p, h in enumerate(self.phases):
            y, self._zi[p] = lfilter(h, [1.0], x, axis=0, zi=self._zi[p])
            self._true = np.maximum(self._true, np.abs(y).max(axis=0))
        self._count_clipping(ax)

    def _count_clipping(self, ax: np.ndarray) -> None:
        """Count runs of 3+ consecutive samples at or above the clip threshold, across blocks."""
        over = ax >= self._clip_threshold
        n = over.shape[0]
        for ch in range(self.channels):
            col = over[:, ch]
            run = int(self._clip_run_open[ch])
            if run and (n == 0 or not col[0]):
                if run >= 3:
                    self._clip_runs += 1
                run = 0
            padded = np.concatenate([[0], col.astype(np.int8), [0]])
            edges = np.diff(padded)
            starts = np.flatnonzero(edges == 1)
            ends = np.flatnonzero(edges == -1)
            new_open = 0
            for s, e in zip(starts, ends):
                length = int(e - s) + (run if s == 0 else 0)
                if e == n:
                    new_open = length
                elif length >= 3:
                    self._clip_runs += 1
            self._clip_run_open[ch] = new_open

    def result(self) -> PeakResult:
        pending = int((self._clip_run_open >= 3).sum())
        return PeakResult(
            true_peak_dbtp=float(to_db(self._true.max())) if self.channels else -np.inf,
            sample_peak_dbfs=float(to_db(self._sample.max())) if self.channels else -np.inf,
            true_peak_per_channel=to_db(self._true),
            sample_peak_per_channel=to_db(self._sample),
            clipped_runs=self._clip_runs + pending,
        )
