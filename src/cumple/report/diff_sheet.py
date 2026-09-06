"""The diff sheet: what changed between two versions, or whether the stems still null, on one page.

The same document system as the QC sheet (design.md, tokens.css, the embedded faces): a verdict
stamp, the alignment numbers as a strip, both files' levels side by side, and the third-octave
band deltas drawn as bars with the gain change removed, so EQ shows as EQ.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import numpy as np

from .. import __version__
from ..diff.compare import DiffResult, Levels
from ..diff.render import describe
from .qc_sheet import _esc, _hz, plot_labels, to_pdf
from .style import document_css

OCTAVES = (31.5, 63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000)


def _num(x: float, digits: int = 1, signed: bool = False) -> str:
    if x is None or not np.isfinite(x):
        return "none"
    return f"{x:+.{digits}f}" if signed else f"{x:.{digits}f}"


def verdict(r: DiffResult) -> tuple[str, str]:
    """(stamp text, stamp class). Stems either null or they do not; a version pair is described, not judged."""
    nulls = r.identical or (np.isfinite(r.residual_dbfs) and r.residual_dbfs < -60)
    if r.stems:
        return ("NULLS", "pass") if nulls else ("NO NULL", "fail")
    if r.identical:
        return "IDENTICAL", "pass"
    if nulls:
        return "SAME MIX", "pass"
    if r.residual_rel_db < -12:
        return "SAME MATERIAL", "accent"
    return "DIFFERENT", "accent"


def _bands(r: DiffResult) -> str:
    gain = r.alignment.gain_db
    pts = [(c, d - gain) for c, d in r.band_deltas if np.isfinite(d)]
    if not pts:
        return ""
    w, h, left, right, top, bottom = 800, 220, 44, 12, 12, 26
    vmax = max(2.0, float(np.ceil(max(abs(v) for _, v in pts))))
    slot = (w - left - right) / len(pts)
    bw = slot * 0.62

    def Y(v: float) -> float:
        return top + (vmax - v) / (2 * vmax) * (h - top - bottom)

    step = 1.0 if vmax <= 3 else (2.0 if vmax <= 8 else 5.0)
    svg = [
        f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="Third-octave band level of B minus A with the gain change removed">'
    ]
    labels: list[tuple[str, float, float, str]] = []
    for g in np.arange(-vmax, vmax + 0.01, step):
        cls = "zero" if abs(g) < 1e-9 else "grid"
        svg.append(f'<line class="{cls}" x1="{left}" x2="{w - right}" y1="{Y(g):.1f}" y2="{Y(g):.1f}"/>')
        labels.append((f"{g:+g}" if g else "0", left - 6, Y(g), "y"))
    for i, (c, v) in enumerate(pts):
        x = left + slot * i + (slot - bw) / 2
        y0, y1 = Y(0), Y(v)
        cls = "bar-up" if v >= 0 else "bar-down"
        svg.append(
            f'<rect class="{cls}" x="{x:.1f}" y="{min(y0, y1):.1f}" width="{bw:.1f}" height="{abs(y1 - y0):.1f}"/>'
        )
        octave = next((k for k, o in enumerate(OCTAVES) if abs(c / o - 1) < 0.06), None)
        if octave is not None:  # every other octave label steps aside on a phone
            labels.append((_hz(c), left + slot * i + slot / 2, h - bottom + 6, "x" if octave % 2 == 0 else "x alt"))
    svg.append("</svg>")
    removed = f" with the {gain:+.1f} dB gain change removed" if abs(gain) >= 0.05 else ""
    return (
        "<h2>Spectral balance</h2><figure>"
        f'<div class="plot">{"".join(svg)}{plot_labels(labels, w, h)}</div>'
        '<div class="legend"><span><i class="up"></i>B louder than A</span><span><i class="down"></i>B quieter than A</span></div>'
        f"<figcaption>Third-octave band level of B minus A in dB{removed}, so an EQ change shows as EQ "
        "rather than being absorbed into the gain figure.</figcaption></figure>"
    )


def _levels_rows(a: Levels, b: Levels) -> str:
    rows = [
        ("integrated loudness", a.integrated, b.integrated, "LUFS"),
        ("true peak", a.true_peak, b.true_peak, "dBTP"),
        ("sample peak", a.sample_peak, b.sample_peak, "dBFS"),
        ("loudness range", a.lra, b.lra, "LU"),
        ("RMS", a.rms_dbfs, b.rms_dbfs, "dBFS"),
    ]
    out = []
    for what, va, vb, unit in rows:
        delta = _num(vb - va, 1, signed=True) if np.isfinite(va) and np.isfinite(vb) else "none"
        out.append(
            f'<tr><td>{what}</td><td class="num">{_num(va)} {unit}</td>'
            f'<td class="num">{_num(vb)} {unit}</td><td class="num">{delta}</td></tr>'
        )
    return "".join(out)


def render_diff_html(r: DiffResult) -> str:
    al = r.alignment
    now = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
    stamp, cls = verdict(r)
    a_name = r.a.name
    b_name = f"the sum of {len(r.stems)} stems" if r.stems else r.b.name
    ms = al.offset_samples / r.fs * 1000
    offset = _num(al.offset_samples, 0 if abs(al.offset_samples) >= 0.5 else 2, signed=True)
    strip = [
        ("Gain", _num(al.gain_db, 2, signed=True), "dB, B against A"),
        ("Offset", offset, f"samples · {ms:+.2f} ms"),
        ("Polarity", "inverted" if al.polarity_inverted else "same", f"correlation {al.correlation:+.2f}"),
        ("Residual", _num(r.residual_dbfs, 0), "dBFS RMS"),
        ("Relative", _num(r.residual_rel_db, 0, signed=True), "dB to A"),
        ("Residual peak", _num(r.residual_peak_dbfs, 0), "dBFS"),
    ]
    strip_html = "".join(
        f'<div><div class="k">{_esc(k)}</div><div class="v">{_esc(v)}</div><div class="u">{_esc(u)}</div></div>'
        for k, v, u in strip
    )
    said = "".join(f"<p>{_esc(line)}</p>" for line in describe(r).split("\n"))
    files = ""
    if r.stems:
        items = "".join(f"<li>{_esc(s.name)}</li>" for s in r.stems)
        files = (
            f'<h2>Stems</h2><ul class="files">{items}<li>against {_esc(a_name)}</li></ul>'
            '<p class="note">Level differences are kept, because stems must match the printmaster at level; '
            "only offset and polarity are corrected before the residual is taken.</p>"
        )
    notes = "".join(f"<li>{_esc(n)}</li>" for n in r.notes)
    notes_html = f'<h2>Notes</h2><ul class="fixes">{notes}</ul>' if notes else ""
    b_label = "sum" if r.stems else "B"
    b_meta = " + ".join(s.name for s in r.stems) if r.stems else r.b.name
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Diff sheet: {_esc(b_name)} against {_esc(a_name)}</title><style>{document_css()}</style></head>
<body><div class="sheet">
<header class="head">
  <div>
    <h1>Audio diff sheet</h1>
    <div class="file">{_esc(b_name)} against {_esc(a_name)}</div>
    <div class="meta">{r.channels}-channel, {r.fs / 1000:g} kHz, {r.duration_a_s:.1f} s and {r.duration_b_s:.1f} s</div>
    <div class="meta">A: <b>{_esc(a_name)}</b> · {b_label}: <b>{_esc(b_meta)}</b></div>
    <div class="meta">{now} · cumple {__version__}</div>
  </div>
  <div class="stamp {cls}">{stamp}</div>
</header>
<div class="strip">{strip_html}</div>
<h2>In words</h2>
{said}
<h2>Levels</h2>
<table class="levels"><thead><tr><th></th><th>A</th><th>{b_label}</th><th>{b_label} minus A</th></tr></thead><tbody>{_levels_rows(r.levels_a, r.levels_b)}</tbody></table>
{_bands(r)}
{files}
{notes_html}
<footer class="colophon">Offset from FFT cross-correlation with sub-sample refinement; polarity from its sign; gain as the median third-octave band delta, so EQ shows as EQ; the residual is what is left after all three are corrected. Levels per ITU-R BS.1770-5, true peak 4x oversampled per BS.1770 Annex 2. cumple {__version__}.</footer>
</div></body></html>
"""


def write_diff_sheet(r: DiffResult, out_html: Path, pdf: bool = False) -> tuple[Path, Path | None]:
    out_html = Path(out_html)
    out_html.write_text(render_diff_html(r), encoding="utf-8")
    pdf_path = None
    if pdf:
        pdf_path = out_html.with_suffix(".pdf")
        if not to_pdf(out_html, pdf_path):
            pdf_path = None
    return out_html, pdf_path
