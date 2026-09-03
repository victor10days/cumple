"""Turn a DiffResult into a sentence a mixer would say, plus JSON."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from .. import __version__
from .compare import DiffResult


def _num(x):
    return None if x is None or not math.isfinite(float(x)) else float(x)


def residual_meaning(residual_dbfs: float, residual_rel_db: float) -> str:
    if not np.isfinite(residual_dbfs) or residual_dbfs < -100:
        return "nothing is left: the files are the same audio"
    if residual_dbfs < -80:
        return "what is left is below -80 dBFS: identical for any practical purpose"
    if residual_dbfs < -60:
        return "what is left is at dither and encoder level: a different bounce of the same mix"
    if residual_rel_db < -30:
        return "a small processing difference: the same mix with a light touch of EQ, compression or limiting"
    if residual_rel_db < -12:
        return "a clear processing difference: the same material, treated differently"
    return "substantially different audio"


def describe(r: DiffResult) -> str:
    al = r.alignment
    a, b = r.a.name, (r.b.name if not r.stems else "the sum of the stems")
    if r.identical:
        return f"{b} is sample-for-sample identical to {a}."
    parts = []
    if abs(al.gain_db) >= 0.05:
        parts.append(f"at {al.gain_db:+.1f} dB")
    if abs(al.offset_samples) >= 0.5:
        ms = al.offset_samples / r.fs * 1000
        parts.append(
            f"{abs(al.offset_samples):.0f} samples ({abs(ms):.2f} ms) {'late' if al.offset_samples > 0 else 'early'}"
        )
    elif abs(al.offset_samples) >= 0.05:
        parts.append(f"{al.offset_samples:+.2f} samples off")
    if al.polarity_inverted:
        parts.append("polarity inverted")
    head = f"{b} is {a}" + ((" " + ", ".join(parts)) if parts else " with no gain, offset or polarity change")
    tail = residual_meaning(r.residual_dbfs, r.residual_rel_db)
    corrected = (
        "After correcting for offset and polarity (level differences are kept, because stems must match the printmaster at level)"
        if r.stems
        else "After correcting for that"
    )
    resid = (
        f"{corrected}, the residual is {r.residual_dbfs:.0f} dBFS RMS ({r.residual_rel_db:+.0f} dB relative to the original; peak {r.residual_peak_dbfs:.0f} dBFS)."
        if np.isfinite(r.residual_dbfs)
        else f"{corrected}, nothing is left."
    )
    lines = [f"{head}. {resid} {tail.capitalize()}."]
    lines.append(
        f"Loudness {r.levels_a.integrated:.1f} to {r.levels_b.integrated:.1f} LUFS ({r.loudness_delta:+.1f} LU); true peak {r.levels_a.true_peak:+.1f} to {r.levels_b.true_peak:+.1f} dBTP ({r.true_peak_delta:+.1f} dB); loudness range {r.levels_a.lra:.1f} to {r.levels_b.lra:.1f} LU."
    )
    notable = [(c, d) for c, d in r.band_deltas if abs(d - al.gain_db) >= 1.0]
    if notable:
        notable.sort(key=lambda cd: -abs(cd[1] - al.gain_db))
        shown = ", ".join(f"{d - al.gain_db:+.1f} dB at {_hz(c)}" for c, d in notable[:4])
        lines.append(f"Spectral balance beyond the gain change: {shown}.")
    else:
        lines.append("Spectral balance: no third-octave band moved by 1 dB or more beyond the gain change.")
    for n in r.notes:
        lines.append(f"Note: {n}")
    return "\n".join(lines)


def _hz(c: float) -> str:
    return f"{c / 1000:g} kHz" if c >= 1000 else f"{c:g} Hz"


def diff_to_dict(r: DiffResult) -> dict[str, Any]:
    al = r.alignment
    return {
        "cumple": __version__,
        "a": str(r.a),
        "b": str(r.b),
        "stems": [str(s) for s in r.stems],
        "samplerate": r.fs,
        "channels": r.channels,
        "duration_a_s": r.duration_a_s,
        "duration_b_s": r.duration_b_s,
        "identical": r.identical,
        "alignment": {
            "offset_samples": al.offset_samples,
            "offset_ms": al.offset_samples / r.fs * 1000,
            "gain_db": _num(al.gain_db),
            "polarity_inverted": al.polarity_inverted,
            "correlation": al.correlation,
        },
        "residual": {
            "rms_dbfs": _num(r.residual_dbfs),
            "relative_db": _num(r.residual_rel_db),
            "peak_dbfs": _num(r.residual_peak_dbfs),
            "meaning": residual_meaning(r.residual_dbfs, r.residual_rel_db),
        },
        "levels": {
            "a": {
                "integrated_lufs": _num(r.levels_a.integrated),
                "lra_lu": _num(r.levels_a.lra),
                "true_peak_dbtp": _num(r.levels_a.true_peak),
                "rms_dbfs": _num(r.levels_a.rms_dbfs),
            },
            "b": {
                "integrated_lufs": _num(r.levels_b.integrated),
                "lra_lu": _num(r.levels_b.lra),
                "true_peak_dbtp": _num(r.levels_b.true_peak),
                "rms_dbfs": _num(r.levels_b.rms_dbfs),
            },
        },
        "band_deltas_db": [{"hz": c, "delta_db": _num(d)} for c, d in r.band_deltas],
        "notes": r.notes,
        "summary": describe(r),
    }
