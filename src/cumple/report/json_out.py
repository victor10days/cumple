"""Machine-readable output. -inf becomes null so the JSON stays valid."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

from .. import __version__
from ..checks.engine import Report


def _num(x: float | None) -> float | None:
    if x is None:
        return None
    x = float(x)
    return x if math.isfinite(x) else None


def report_to_dict(report: Report) -> dict[str, Any]:
    m, p = report.measurement, report.profile
    return {
        "cumple": __version__,
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "path": str(m.path),
        "profile": {"id": p.id, "name": p.name, "grade": p.grade.value, "has_defaults": p.has_defaults},
        "verdict": report.verdict,
        "measurement": {
            "samplerate": m.samplerate,
            "channels": m.channels,
            "roles": m.roles,
            "layout": m.layout,
            "duration_s": m.duration_s,
            "integrated_lufs": _num(m.loudness.integrated),
            "integrated_ungated_lufs": _num(m.loudness.integrated_ungated),
            "momentary_max_lufs": _num(m.loudness.momentary_max),
            "short_term_max_lufs": _num(m.loudness.short_term_max),
            "lra_lu": _num(m.loudness.lra),
            "true_peak_dbtp": _num(m.peaks.true_peak_dbtp),
            "sample_peak_dbfs": _num(m.peaks.sample_peak_dbfs),
            "true_peak_per_channel_dbtp": [_num(v) for v in m.peaks.true_peak_per_channel],
            "clipped_runs": m.peaks.clipped_runs,
            "dc_offset": [float(v) for v in m.dc_offset],
            "head_silence_s": m.head_silence_s,
            "tail_silence_s": m.tail_silence_s,
            "phase_correlation": _num(m.phase_correlation),
            "mono_fold_lufs": _num(m.mono_fold_loudness),
            "speech_fraction": _num(m.speech_fraction),
            "bext": (m.info.bext if m.info else {}),
        },
        "findings": [
            {
                "code": f.code,
                "status": f.status.value,
                "what": f.what,
                "measured": f.measured,
                "limit": f.limit,
                "value": _num(f.value),
                "note": f.note,
                "clause": f.clause,
                "fix": f.fix,
            }
            for f in report.findings
        ],
    }
