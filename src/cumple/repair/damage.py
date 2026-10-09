"""Synthetic damage on a clean reference, so a repair has a known answer to be scored against."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict
from scipy.ndimage import maximum_filter1d

from .metrics import click_span, local_rms, sdr_db

# Widths 1 to 3 at 32 times the local RMS, recalibrated at the detector of record's threshold of 5
# (03d Concern 2): cathar's detector cannot exceed sqrt(window) = 8, and these clear 5 at the peak.
IMPULSE = dict(widths=(1, 3), gains=(32,))
# Widths 4 to 64 at 8 and 16 times the local RMS. Most are invisible to the detector of record by its
# arithmetic bound; the BURST table reports that as the detector's weakness.
BURST = dict(widths=(4, 64), gains=(8, 16))

MIN_SPACING = 2048  # samples between click positions
EDGE_MARGIN = 64  # clicks keep a full analysis window on each side
SILENCE_FLOOR = 2.0**-15  # one 16-bit LSB: a click in digital silence still gets an amplitude


@dataclass(frozen=True)
class Click:
    position: int  # the peak sample; for an even width, the first of the two central samples
    width: int
    gain: int  # peak amplitude in multiples of the clean signal's local RMS


def clip_to_sdr(x: np.ndarray, target_sdr_db: float) -> tuple[np.ndarray, float, np.ndarray]:
    """Hard-clip x so its SDR against x is target_sdr_db, within 0.05 dB.

    Returns the clipped signal, the threshold (rounded to float32 so |v| >= threshold holds on the
    samples once they are stored as float32) and the mask |x| >= threshold.
    """
    x = np.asarray(x, dtype=np.float64)
    lo, hi = 0.0, float(np.max(np.abs(x)))
    thr = hi
    for _ in range(60):
        thr = 0.5 * (lo + hi)
        gap = sdr_db(x, np.clip(x, -thr, thr)) - target_sdr_db
        if abs(gap) < 0.05:
            break
        if gap > 0:  # clipped too little: lower the threshold
            hi = thr
        else:
            lo = thr
    thr = float(np.float32(thr))
    return np.clip(x, -thr, thr), thr, np.abs(x) >= thr


def _shape(width: int) -> np.ndarray:
    """A half-cosine burst over `width` samples, scaled so its largest sample is 1."""
    d = np.arange(width) - (width - 1) / 2
    s = np.cos(np.pi * d / width)
    return s / s.max()


def add_clicks(
    x: np.ndarray, samplerate: int, seed: int, per_minute: float, widths: tuple[int, int], gains: tuple[int, ...]
) -> tuple[np.ndarray, list[Click], np.ndarray]:
    """Add seeded clicks to x. Returns the damaged copy, the clicks, and the mask of the samples they touch.

    per_minute * seconds positions, at least 2,048 samples apart, widths uniform in the closed range
    `widths`, each click a half-cosine burst whose peak is gain * the clean signal's local RMS, added
    with a random sign.
    """
    x = np.asarray(x, dtype=np.float64)
    n = len(x)
    count = int(round(per_minute * n / samplerate / 60.0))
    room = n - 2 * EDGE_MARGIN - (count - 1) * MIN_SPACING
    if count < 1 or room < 1:
        raise ValueError(f"{n} samples hold no clicks at {per_minute} per minute, {MIN_SPACING} samples apart")
    rng = np.random.default_rng(seed)
    # Sorted draws plus i * spacing keep every pair at least `spacing` apart, whatever the draws.
    positions = np.sort(rng.integers(0, room, size=count)) + np.arange(count) * MIN_SPACING + EDGE_MARGIN
    size = rng.integers(widths[0], widths[1] + 1, size=count)
    gain = rng.choice(np.asarray(gains), size=count)
    sign = rng.choice(np.asarray([-1.0, 1.0]), size=count)
    rms = local_rms(x)
    y = x.copy()
    mask = np.zeros(n, dtype=bool)
    clicks: list[Click] = []
    for p, w, g, s in zip(positions, size, gain, sign, strict=True):
        p, w, g = int(p), int(w), int(g)
        first, last = click_span(p, w)
        y[first : last + 1] += s * g * max(rms[p], SILENCE_FLOOR) * _shape(w)
        mask[first : last + 1] = True
        clicks.append(Click(p, w, g))
    return y, clicks, mask


def dilate(mask: np.ndarray, n: int) -> np.ndarray:
    """The mask widened by n samples on each side."""
    if n <= 0:
        return mask.copy()
    return maximum_filter1d(mask.astype(np.uint8), size=2 * n + 1, mode="constant") > 0


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Reference(_Model):
    name: str
    file: str  # path relative to the repair set's root
    sha256: str
    samplerate: int
    source: str  # where it came from, for the report's header


class ClickRecord(_Model):
    position: int
    width: int
    gain: int


class Damaged(_Model):
    name: str  # "<reference>.clip5", "<reference>.impulse7"
    reference: str
    kind: Literal["clip", "impulse", "burst"]
    file: str
    sha256: str
    sdr_db: float | None = None  # the clip level asked for
    threshold: float | None = None  # clip: the float32 repr of the stored threshold
    seed: int | None = None
    per_minute: float | None = None
    clicks: list[ClickRecord] | None = None


class RxInput(_Model):
    name: str  # the Damaged.name this file is made from
    file: str
    sha256: str
    scale: float  # RX sees the clip plateau at 0.95; divide RX's output by this to compare


class Manifest(_Model):
    version: int = 1
    references: list[Reference]
    damaged: list[Damaged]
    rx_input: list[RxInput]
