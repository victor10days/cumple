"""Helpers for the repair-core tests: the chunk protocol, gap masks, and cathar's De-click detector in float32."""

from __future__ import annotations

import numpy as np


def chunked(module, x: np.ndarray, block: int) -> np.ndarray:
    """Run `module` over x (frames, channels) block by block, as `Chunker::run` in crates/cumple-dsp/src/module.rs does.

    Each call's centre is `block` samples, with up to `context_frames` of the module's own earlier output on the
    left and `context_frames` raw samples on the right. A tail shorter than the context is merged into the call
    before it, so no call's right context is cut short.
    """
    context = module.context_frames
    n = len(x)
    out = np.zeros_like(x, dtype=np.float64)
    start = 0
    while start < n:
        end = min(start + block, n)
        if n - end < context:
            end = n
        last = end == n
        lo = max(start - context, 0)
        hi = n if last else end + context
        y = module.process(np.concatenate([out[lo:start], x[start:hi]]), edge=(lo == 0, last, 0))
        out[start:end] = y[start - lo : end - lo]
        start = end
    return out


def gap_mask(n: int, positions, widths) -> np.ndarray:
    """True on every sample of the spans [position, position + width), clipped to n samples."""
    mask = np.zeros(n, dtype=bool)
    for p, w in zip(positions, widths, strict=True):
        mask[max(int(p), 0) : min(int(p) + int(w), n)] = True
    return mask


def cathar_local_rms(y: np.ndarray, window: int = 64) -> np.ndarray:
    """cathar's local RMS (restore.rs 171 to 194) in float32, its running sum's rounding included.

    The running sum adds the first window/2 squares, then for each sample i subtracts the square leaving the
    window (i >= window/2) and adds the one entering it (i + window/2 < n). A float32 cumsum of those terms,
    interleaved in that order with zeros where a step does nothing, is the same sequence of float32 additions.
    """
    y32 = np.asarray(y, dtype=np.float32)
    n = len(y32)
    half = window // 2
    sq = y32 * y32
    first = min(half, n)
    i = np.arange(n)
    zero = np.float32(0.0)
    leave = np.where(i >= half, -sq[np.maximum(i - half, 0)], zero)
    enter = np.where(i + half < n, sq[np.minimum(i + half, n - 1)], zero)
    terms = np.concatenate([sq[:first], np.column_stack([leave, enter]).ravel()]).astype(np.float32)
    sums = np.cumsum(terms, dtype=np.float32)[first + 1 :: 2]  # the sum after both of sample i's steps
    count = (np.minimum(i + half, n - 1) - np.maximum(i - half + 1, 0) + 1).astype(np.float32)
    # A drifted sum below zero gives NaN, which fmax turns into the floor, as Rust's f32::max does.
    with np.errstate(invalid="ignore"):
        return np.fmax(np.sqrt(sums / count), np.float32(1e-10))


def cathar_gaps(y: np.ndarray, threshold: float = 5.0, window: int = 64) -> list[tuple[int, int]]:
    """The spans cathar's `declick_with_method` hands to its filler (restore.rs 116 to 169), as (start, length).

    The detector runs in float32 as cathar's does: |y| > threshold * local RMS, a contiguous run grown both
    ways, a shoulder pad of window/2 clamped to 2..8 samples, then a jump of window/2 - 1 past the run. Each
    span includes its shoulders. Spans at a file end, which cathar fills with its cubic, are listed too.
    """
    y32 = np.asarray(y, dtype=np.float32)
    n = len(y32)
    half = window // 2
    if half == 0 or n <= window:
        return []
    flag = (np.abs(y32) > np.float32(threshold) * cathar_local_rms(y32, window)).tolist()
    pad = min(max(half, 2), 8)
    gaps: list[tuple[int, int]] = []
    i = half
    while i + half < n:
        if flag[i]:
            start = i
            while start > half and flag[start - 1]:
                start -= 1
            end = i + 1
            while end + half < n and flag[end]:
                end += 1
            gap_start = max(start - pad, 0)
            gap_end = min(end + pad, n)
            gap_len = max(gap_end - gap_start, 0)
            if (gap_len >= 2 and gap_start > 0 and gap_end < n) or gap_end > gap_start + 2:
                gaps.append((gap_start, gap_len))
            i = max(end, i + 1) + max(half - 1, 0)
            continue
        i += 1
    return gaps
