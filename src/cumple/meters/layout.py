"""Channel-layout sanity: is the LFE really an LFE, and is the file in the order it claims?

A 5.1 file is six channels in a row; nothing in the header says which is which. Two
conventions exist: SMPTE/ITU order (L R C LFE Ls Rs), which every streaming spec asks
for, and Film order (L C R Ls Rs LFE), which older Pro Tools sessions default to. The
LFE channel gives the order away: it is the one with almost no energy above 120 Hz.
The same measurement answers Apple's rule that the LFE must not carry full-frequency
content.

Eight channels raise a second question: are channels 7 and 8 rear surrounds (7.1) or a
stereo fold-down of the 5.1 in front of them, the "5.1 + 2.0" layout that Fox, CBS, Hulu,
Paramount and Disney trailers ask for? The header cannot say. A fold-down correlates
strongly with the Lo/Ro mix of channels 1 to 6; independent rear surrounds do not. The
meter keeps a Gram matrix of the channels and reports that correlation.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import butter, sosfilt, sosfilt_zi

SILENT_DBFS = -60.0  # a channel quieter than this is treated as empty for layout guesses
DOWNMIX_CORR_MIN = 0.7  # tool default: above this, channels 7 and 8 are a fold-down of the 5.1
FOLD_SIDE = 0.7071  # -3 dB, the usual centre and surround contribution to Lo/Ro


@dataclass
class LayoutResult:
    corner_hz: float
    rms_dbfs: np.ndarray  # per channel
    hf_ratio_db: np.ndarray  # energy above the corner relative to total, per channel
    lfe_like: int | None  # index of the channel that looks like an LFE, if any
    downmix_corr: float | None = None  # eight channels: how well 7 and 8 match a fold-down of 1 to 6

    def silent(self, ch: int) -> bool:
        return self.rms_dbfs[ch] < SILENT_DBFS


class LayoutMeter:
    """Streaming per-channel RMS, high-band energy ratio, and the channel Gram matrix."""

    def __init__(
        self,
        samplerate: int,
        channels: int,
        corner_hz: float = 250.0,
        lfe_ratio_db: float = -15.0,
        roles: list[str] | None = None,
    ):
        self.fs = int(samplerate)
        self.channels = int(channels)
        self.corner_hz = float(corner_hz)
        self.lfe_ratio_db = float(lfe_ratio_db)
        self.roles = list(roles) if roles else None
        self._sos = butter(6, corner_hz, btype="highpass", fs=self.fs, output="sos")
        zi = sosfilt_zi(self._sos)  # (sections, 2)
        self._zi = np.repeat(zi[:, :, None], self.channels, axis=2) * 0.0
        self._total = np.zeros(self.channels)
        self._high = np.zeros(self.channels)
        self._gram = np.zeros((self.channels, self.channels))
        self._n = 0

    def feed(self, block: np.ndarray) -> None:
        x = np.asarray(block, dtype=np.float64)
        if x.ndim == 1:
            x = x[:, None]
        hi, self._zi = sosfilt(self._sos, x, axis=0, zi=self._zi)
        self._total += np.sum(x * x, axis=0)
        self._high += np.sum(hi * hi, axis=0)
        self._gram += x.T @ x
        self._n += x.shape[0]

    def _corr(self, a: np.ndarray, b: np.ndarray) -> float:
        """Correlation of two mixes given as coefficient vectors over the channels."""
        num = float(a @ self._gram @ b)
        den = float(np.sqrt((a @ self._gram @ a) * (b @ self._gram @ b)))
        return num / den if den > 0 else 0.0

    def _downmix_corr(self, rms: np.ndarray) -> float | None:
        """For an 8-channel bed with a pair on top: how well the pair matches a fold-down of the 5.1.

        Each side is compared with the fold that includes its surround and with the front-only
        fold, and the better match is kept, so an Lt/Rt whose surrounds are phase-shifted still
        reads as a fold-down. The result is the weaker of the two sides."""
        if self.channels != 8 or not self.roles:
            return None
        idx = {r: i for i, r in enumerate(self.roles)}
        if any(r not in idx for r in ("L", "R", "C", "Ls", "Rs")):
            return None
        left = next((idx[r] for r in ("Lt", "Lrs") if r in idx), None)
        right = next((idx[r] for r in ("Rt", "Rrs") if r in idx), None)
        if left is None or right is None or rms[left] < SILENT_DBFS or rms[right] < SILENT_DBFS:
            return None

        def unit(i: int) -> np.ndarray:
            e = np.zeros(self.channels)
            e[i] = 1.0
            return e

        def side(pair: int, front: str, surround: str) -> float:
            fold = unit(idx[front]) + FOLD_SIDE * unit(idx["C"])
            with_surround = fold + FOLD_SIDE * unit(idx[surround])
            return max(self._corr(unit(pair), with_surround), self._corr(unit(pair), fold))

        return min(side(left, "L", "Ls"), side(right, "R", "Rs"))

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
        return LayoutResult(
            corner_hz=self.corner_hz,
            rms_dbfs=rms,
            hf_ratio_db=ratio,
            lfe_like=lfe_like,
            downmix_corr=self._downmix_corr(rms),
        )
