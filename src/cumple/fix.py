"""Gain-only fix: write a copy whose gain alone makes it comply. Never limits.

A limiter changes the sound; that is the mixer's decision. Gain does not. So the fix looks
for a single gain that puts loudness inside the destination's window without pushing the
true peak (or sample peak) over its cap. If no such gain exists it says so and writes
nothing.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import soundfile as sf

from .checks.engine import SPEECH_ASSUMED_FRACTION
from .meters.measure import Measurement, measure, measure_args
from .specs.schema import LoudnessRule, Profile


@dataclass
class FixPlan:
    gain_db: float | None
    reason: str
    loudness_before: float
    loudness_after: float | None
    true_peak_before: float
    true_peak_after: float | None
    rule: LoudnessRule | None


def _applicable_rule(p: Profile, m: Measurement) -> LoudnessRule | None:
    if not p.loudness:
        return None
    speech = m.speech_fraction if m.speech_fraction is not None else SPEECH_ASSUMED_FRACTION
    for r in p.loudness.rules:
        if r.role != "primary":
            continue
        if r.when == "speech_below_15pct" and speech >= 0.15:
            continue
        if r.when == "speech_at_or_above_15pct" and speech < 0.15:
            continue
        return r
    return None


def _value_for(rule: LoudnessRule, m: Measurement) -> float:
    if rule.method == "dialogue_gated" and m.loudness.dialogue_blocks > 0 and np.isfinite(m.loudness.dialogue_gated):
        return m.loudness.dialogue_gated
    return m.loudness.integrated if rule.gated_relative else m.loudness.integrated_ungated


def plan(p: Profile, m: Measurement) -> FixPlan:
    rule = _applicable_rule(p, m)
    tp = m.peaks.true_peak_dbtp
    sp = m.peaks.sample_peak_dbfs
    lo, hi = -np.inf, np.inf  # allowed gain interval
    level = _value_for(rule, m) if rule else np.nan
    if rule is not None and np.isfinite(level):
        if rule.min is not None:
            lo = max(lo, rule.min - level)
        if rule.max is not None:
            hi = min(hi, rule.max - level)
    if p.peaks.true_peak_max is not None and np.isfinite(tp):
        hi = min(hi, p.peaks.true_peak_max - tp)
    if p.peaks.sample_peak_max is not None and np.isfinite(sp):
        hi = min(hi, p.peaks.sample_peak_max - sp)
    if rule is None and p.peaks.true_peak_max is None and p.peaks.sample_peak_max is None:
        return FixPlan(
            None, "this destination has no loudness or peak rule that gain could satisfy", level, None, tp, None, rule
        )
    if lo > hi:
        need = lo
        return FixPlan(
            None,
            f"gain alone cannot do it: loudness needs at least {need:+.1f} dB but the peak allows at most {hi:+.1f} dB; the mix needs headroom (limiting or a mix change is a creative decision, so cumple does not do it)",
            level,
            None,
            tp,
            None,
            rule,
        )
    if rule is not None and rule.target is not None:
        want = rule.target - level
    elif rule is not None and rule.min is not None and rule.max is not None:
        want = (rule.min + rule.max) / 2 - level
    else:
        want = 0.0
    gain = float(min(max(want, lo), hi))
    if abs(gain) < 0.05 and lo <= 0.0 <= hi:
        return FixPlan(0.0, "already complies; nothing to change", level, level, tp, tp, rule)
    return FixPlan(
        gain, f"apply {gain:+.2f} dB", level, level + gain if np.isfinite(level) else None, tp, tp + gain, rule
    )


def apply(src: Path, dst: Path, gain_db: float, block: int = 1 << 18) -> None:
    """Write dst as src times the gain, same sample rate, channels and subtype, streaming."""
    with sf.SoundFile(str(src)) as fin:
        with sf.SoundFile(
            str(dst), "w", samplerate=fin.samplerate, channels=fin.channels, subtype=fin.subtype, format=fin.format
        ) as fout:
            g = 10 ** (gain_db / 20)
            while True:
                x = fin.read(block, dtype="float64", always_2d=True)
                if not len(x):
                    break
                fout.write(np.clip(x * g, -1.0, 1.0))


def fix_file(src: Path, profile: Profile, dst: Path | None = None) -> tuple[FixPlan, Path | None, Measurement | None]:
    m = measure(src, **measure_args(profile))
    fp = plan(profile, m)
    if fp.gain_db is None or fp.gain_db == 0.0:
        return fp, None, None
    dst = dst or src.with_name(f"{src.stem}.{profile.id}{src.suffix}")
    if dst.exists() and dst.resolve() == src.resolve():
        raise ValueError(f"refusing to overwrite the source file {src}; give --out a different path")
    if dst.is_dir():
        raise ValueError(f"{dst} is a directory; give --out a file path")
    # Write next to the destination under a temporary name and move it into place only once the
    # whole copy succeeded, so a failure half-way never leaves a truncated deliverable behind.
    tmp = dst.with_name(f".{dst.name}.cumple-tmp")
    try:
        apply(src, tmp, fp.gain_db)
        os.replace(tmp, dst)
    finally:
        if tmp.exists():
            tmp.unlink()
    return fp, dst, measure(dst, **measure_args(profile))
