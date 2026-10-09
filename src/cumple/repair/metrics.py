"""Scores for repair: SDR, change in SDR, residual clicks and peak error. Pure numpy, no extension."""

from __future__ import annotations

import numpy as np

RMS_FLOOR = 1e-10  # cathar floors its local RMS here


def sdr_db(ref: np.ndarray, est: np.ndarray) -> float:
    """10 log10(sum(ref^2) / sum((ref - est)^2)); inf when the estimate equals the reference."""
    ref = np.asarray(ref, dtype=np.float64)
    err = float(np.sum((ref - np.asarray(est, dtype=np.float64)) ** 2))
    if err == 0.0:
        return float("inf")
    sig = float(np.sum(ref**2))
    if sig == 0.0:
        return float("-inf")
    return 10.0 * float(np.log10(sig / err))


def delta_sdr(ref: np.ndarray, damaged: np.ndarray, est: np.ndarray, mask: np.ndarray | None = None) -> float:
    """SDR of the estimate minus SDR of the damaged signal, over the masked samples only when a mask is given."""
    if mask is not None:
        ref, damaged, est = ref[mask], damaged[mask], est[mask]
    before, after = sdr_db(ref, damaged), sdr_db(ref, est)
    if before == after:  # both infinite, or identical
        return 0.0
    return after - before


def local_rms(x: np.ndarray, window: int = 64) -> np.ndarray:
    """cathar's local RMS: for sample i the samples i - window/2 + 1 to i + window/2, clipped to the file.

    The window includes sample i itself, so a lone sample in silence has ratio sqrt(window) to its own
    RMS. Computed in float64, floored at 1e-10 as cathar does (restore.rs, local_rms).
    """
    x = np.asarray(x, dtype=np.float64)
    n = len(x)
    half = window // 2
    csum = np.concatenate(([0.0], np.cumsum(x * x)))
    idx = np.arange(n)
    lo = np.maximum(idx - half + 1, 0)
    hi = np.minimum(idx + half, n - 1)
    count = hi - lo + 1
    return np.maximum(np.sqrt(np.maximum(csum[hi + 1] - csum[lo], 0.0) / count), RMS_FLOOR)


def local_rms_ratio(x: np.ndarray, window: int = 64) -> np.ndarray:
    """|x| divided by its local RMS: the quantity cathar's De-click compares to its threshold."""
    return np.abs(np.asarray(x, dtype=np.float64)) / local_rms(x, window)


def click_span(position: int, width: int) -> tuple[int, int]:
    """First and last sample of a click; `position` is the peak, the first of two central samples for an even width."""
    first = position - (width - 1) // 2
    return first, first + width - 1


def _runs(flags: np.ndarray) -> list[tuple[int, int]]:
    """(first, last) of each run of True."""
    edges = np.diff(np.concatenate(([0], flags.astype(np.int8), [0])))
    return list(zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1) - 1, strict=True))


def residual_clicks(
    ref: np.ndarray, est: np.ndarray, positions, widths, threshold: float, window: int = 64
) -> tuple[int, int]:
    """(missed, false): injected clicks the detector still sees in the estimate, and detections elsewhere.

    The detector is local_rms_ratio at `threshold`. A click is missed when any sample of its span is
    detected. A false detection is a run of detected samples that touches no click span (each widened
    by half the window) and that the detector also finds in the clean reference: a natural transient of
    the reference is not the tool's doing.
    """
    n = len(est)
    hit = local_rms_ratio(est, window) > threshold
    natural = local_rms_ratio(ref, window) > threshold
    near = np.zeros(n, dtype=bool)
    missed = 0
    for position, width in zip(positions, widths, strict=True):
        first, last = click_span(int(position), int(width))
        first, last = max(first, 0), min(last, n - 1)
        if hit[first : last + 1].any():
            missed += 1
        near[max(first - window // 2, 0) : min(last + window // 2, n - 1) + 1] = True
    false = sum(1 for first, last in _runs(hit & ~near) if not natural[first : last + 1].any())
    return missed, false


def peak_error_db(ref: np.ndarray, est: np.ndarray, mask: np.ndarray) -> float:
    """20 log10(max|est[mask]| / max|ref[mask]|): how far the repaired peaks sit from the true ones."""
    return 20.0 * float(np.log10(np.max(np.abs(est[mask])) / np.max(np.abs(ref[mask]))))
