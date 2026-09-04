"""A speech-activity gate, so dialogue-gated loudness can be approximated.

Netflix, Amazon, Disney and ATSC A/85 long-form all measure the loudness of dialogue,
using Dolby Dialogue Intelligence, which is proprietary. This module is an approximation
and every report says so. It is a heuristic, not a model, so cumple installs in seconds:

- 20 ms frames on the centre channel when there is one, otherwise the mono fold;
- a frame is active when its level is above an adaptive floor;
- speech-like when most of its energy sits between 150 Hz and 4 kHz and the level
  envelope carries the 2 to 8 Hz modulation of syllables.

The result is a per-frame mask and the share of active programme that is speech, which
drives the "under 15 % dialogue" switch in several profiles.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import butter, sosfiltfilt

FRAME_S = 0.02
BAND_LO, BAND_HI = 150.0, 4000.0
SILENCE_DBFS = -65.0
ACTIVE_ABOVE_FLOOR_DB = 3.0  # above the 5th-percentile level: excludes room tone, not quiet dialogue
SPEECH_BAND_RATIO = 0.6
MODULATION_MIN_DB = 2.5
MODULATION_BAND_HZ = (2.0, 8.0)
MODULATION_WINDOW_S = 1.0
CONTEXT_S = 1.0  # a pause inside dialogue is still dialogue: dilate over this context
CONTEXT_MIN_DENSITY = 0.3
MIN_FRAMES = 64  # 1.28 s: below this the 2 to 8 Hz modulation filter has nothing to judge


@dataclass
class SpeechResult:
    frame_s: float
    mask: np.ndarray  # bool per frame: speech-like
    active: np.ndarray  # bool per frame: above the floor
    level_db: np.ndarray  # per frame
    fraction: float | None  # share of active frames that are speech-like; None when the file is too short to tell

    def mask_at(self, step_s: float, n: int) -> np.ndarray:
        """The mask resampled onto another grid (e.g. the meter's 10 ms sub-hops)."""
        idx = np.minimum((np.arange(n) * step_s / self.frame_s).astype(int), max(len(self.mask) - 1, 0))
        return self.mask[idx] if len(self.mask) else np.zeros(n, dtype=bool)


class SpeechDetector:
    def __init__(self, samplerate: int, channels: int, roles: list[str] | None = None):
        self.fs = int(samplerate)
        self.channels = int(channels)
        self.frame = int(round(self.fs * FRAME_S))
        self._pick = roles.index("C") if roles and "C" in roles else None
        self._pending = np.empty(0)
        self._energy: list[float] = []
        self._band_ratio: list[float] = []
        freqs = np.fft.rfftfreq(self.frame, 1 / self.fs)
        self._band = (freqs >= BAND_LO) & (freqs <= BAND_HI)
        self._window = np.hanning(self.frame)

    def _channel(self, x: np.ndarray) -> np.ndarray:
        if x.ndim == 1:
            return x
        if self._pick is not None:
            return x[:, self._pick]
        return x.mean(axis=1)

    def feed(self, block: np.ndarray) -> None:
        x = self._channel(np.asarray(block, dtype=np.float64))
        x = np.concatenate([self._pending, x]) if self._pending.size else x
        n = len(x) // self.frame
        if n:
            frames = x[: n * self.frame].reshape(n, self.frame)
            self._energy.extend(np.mean(frames * frames, axis=1))
            spec = np.abs(np.fft.rfft(frames * self._window, axis=1)) ** 2
            total = spec.sum(axis=1)
            band = spec[:, self._band].sum(axis=1)
            with np.errstate(invalid="ignore", divide="ignore"):
                ratio = np.where(total > 0, band / total, 0.0)
            self._band_ratio.extend(ratio)
        self._pending = x[n * self.frame :]

    def result(self) -> SpeechResult:
        e = np.asarray(self._energy)
        if e.size == 0:
            return SpeechResult(FRAME_S, np.zeros(0, bool), np.zeros(0, bool), np.zeros(0), None)
        with np.errstate(divide="ignore"):
            level = np.where(e > 0, 10 * np.log10(np.maximum(e, 1e-30)), -np.inf)
        if e.size < MIN_FRAMES:
            # Shorter than the modulation filter can judge: the share is unknown, not zero.
            return SpeechResult(FRAME_S, np.zeros(e.size, bool), level > SILENCE_DBFS, level, None)
        finite = level[np.isfinite(level) & (level > SILENCE_DBFS)]
        floor = max(SILENCE_DBFS, float(np.percentile(finite, 5))) if finite.size else SILENCE_DBFS
        active = (level > SILENCE_DBFS) & (level > floor + ACTIVE_ABOVE_FLOOR_DB)
        ratio_ok = np.asarray(self._band_ratio) >= SPEECH_BAND_RATIO
        modulated = self._modulation(level) >= MODULATION_MIN_DB
        voiced = active & ratio_ok & modulated
        # Dialogue regions, not just voiced frames: a frame counts as speech when at least
        # CONTEXT_MIN_DENSITY of the frames within ±CONTEXT_S/2 around it are voiced.
        w = max(int(CONTEXT_S / FRAME_S), 1)
        c = np.concatenate([[0.0], np.cumsum(voiced.astype(float))])
        idx = np.arange(len(voiced))
        lo = np.maximum(idx - w // 2, 0)
        hi = np.minimum(idx + w // 2, len(voiced))
        density = (c[hi] - c[lo]) / np.maximum(hi - lo, 1)
        mask = voiced | (density >= CONTEXT_MIN_DENSITY)
        programme = level > SILENCE_DBFS
        programme |= mask  # pauses inside dialogue belong to the programme
        fraction = float(mask[programme].mean()) if programme.any() else 0.0
        return SpeechResult(FRAME_S, mask, active, level, fraction)

    @staticmethod
    def _modulation(level: np.ndarray) -> np.ndarray:
        """Depth of 2 to 8 Hz modulation of the level envelope, in dB, around each frame."""
        n = len(level)
        env = np.where(np.isfinite(level), level, SILENCE_DBFS)
        env = np.maximum(env, SILENCE_DBFS)
        if n < MIN_FRAMES:
            return np.zeros(n)
        fs_env = 1.0 / FRAME_S
        sos = butter(2, MODULATION_BAND_HZ, btype="bandpass", fs=fs_env, output="sos")
        band = sosfiltfilt(sos, env - env.mean())
        w = int(MODULATION_WINDOW_S * fs_env)
        c = np.concatenate([[0.0], np.cumsum(band * band)])
        idx = np.arange(n)
        lo = np.maximum(idx - w // 2, 0)
        hi = np.minimum(idx + w // 2, n)
        return np.sqrt((c[hi] - c[lo]) / np.maximum(hi - lo, 1))
