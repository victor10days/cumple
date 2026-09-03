"""The QC sheet: one page that travels with the deliverable.

Plain HTML with inline CSS and an inline SVG timeline, so it opens anywhere and prints to
one page. PDF export uses the Chrome already on the machine (headless print), never a
web service.
"""

from __future__ import annotations

import html
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import numpy as np

from .. import __version__
from ..checks.engine import Report, Status
from ..specs.schema import GRADE_LABEL

STATUS_LABEL = {Status.PASS: "PASS", Status.FAIL: "FAIL", Status.WARN: "WARN", Status.INFO: "info", Status.SKIP: "n/a"}

CSS = """
:root { --ink:#1E2321; --muted:#5C6663; --line:#D7DBD8; --ground:#F7F8F7; --panel:#FFFFFF;
        --accent:#0F6E8C; --pass:#2E7D4F; --fail:#C03F2B; --warn:#B26E15; --info:#6B7470; }
* { box-sizing: border-box; }
body { margin:0; background:var(--ground); color:var(--ink); font: 13px/1.45 "IBM Plex Sans","Helvetica Neue",Helvetica,Arial,sans-serif; }
.sheet { max-width: 860px; margin: 0 auto; padding: 28px 32px 40px; background: var(--panel); }
header { display:flex; justify-content:space-between; align-items:flex-start; gap:24px; border-bottom:2px solid var(--ink); padding-bottom:14px; }
h1 { font-size: 20px; margin:0 0 4px; letter-spacing:-0.01em; }
h2 { font-size: 12px; text-transform: uppercase; letter-spacing:0.08em; color:var(--muted); margin: 26px 0 8px; }
.file { font-family: "IBM Plex Mono", Menlo, monospace; font-size: 13px; }
.meta { color: var(--muted); font-size: 12px; margin-top: 4px; }
.verdict { font-size: 28px; font-weight: 700; padding: 6px 16px; border-radius: 6px; color:#fff; letter-spacing:0.02em; }
.verdict.pass { background: var(--pass); } .verdict.fail { background: var(--fail); }
.tiles { display:grid; grid-template-columns: repeat(6, 1fr); gap: 10px; margin-top: 18px; }
.tile { border:1px solid var(--line); border-radius: 6px; padding: 8px 10px; }
.tile .k { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing:0.06em; }
.tile .v { font-size: 18px; font-variant-numeric: tabular-nums; margin-top: 2px; }
.tile .u { font-size: 11px; color: var(--muted); }
table { width:100%; border-collapse: collapse; font-size: 12.5px; }
th { text-align:left; font-weight:600; color:var(--muted); font-size:11px; text-transform:uppercase; letter-spacing:0.06em; padding: 6px 8px; border-bottom:1px solid var(--line); }
td { padding: 6px 8px; border-bottom: 1px solid var(--line); vertical-align: top; }
td.num { font-variant-numeric: tabular-nums; white-space: nowrap; }
.st { display:inline-block; min-width: 44px; text-align:center; font-weight:700; font-size: 11px; padding: 2px 6px; border-radius: 4px; color:#fff; }
.st.pass { background: var(--pass); } .st.fail { background: var(--fail); } .st.warn { background: var(--warn); } .st.info, .st.skip { background: var(--info); }
.note { color: var(--muted); }
.fixes li { margin: 4px 0; }
figure { margin: 8px 0 0; }
figcaption { font-size: 11.5px; color: var(--muted); margin-top: 4px; }
.clauses td:first-child { font-family: "IBM Plex Mono", Menlo, monospace; font-size: 11.5px; white-space: nowrap; }
.sources { font-size: 11.5px; color: var(--muted); }
.sources li { margin: 3px 0; }
footer { margin-top: 26px; padding-top: 10px; border-top: 1px solid var(--line); font-size: 11px; color: var(--muted); }
@media print { body { background:#fff; } .sheet { max-width:none; padding: 0; } @page { size: A4; margin: 14mm 14mm; } h2 { break-after: avoid; } tr { break-inside: avoid; } }
"""


def _esc(x) -> str:
    return html.escape("" if x is None else str(x))


def _fmt(x: float | None, unit: str, signed: bool = False) -> str:
    if x is None or not np.isfinite(x):
        return "n/a"
    return (f"{x:+.1f}" if signed else f"{x:.1f}") + (f" {unit}" if unit else "")


def _timeline_svg(report: Report) -> str:
    m = report.measurement
    st = m.loudness.short_term
    if st.size < 2:
        return ""
    t = m.loudness.short_term_times()
    w, h, left, right, top, bottom = 800, 200, 46, 12, 14, 26
    x0, x1 = t[0], t[-1]
    finite = st[np.isfinite(st)]
    lo = float(min(finite.min() if finite.size else -50, -50))
    hi = float(max(finite.max() if finite.size else -5, -5))
    lo, hi = np.floor(lo / 5) * 5 - 5, np.ceil(hi / 5) * 5

    def X(v):
        return left + (v - x0) / max(x1 - x0, 1e-9) * (w - left - right)

    def Y(v):
        v = max(min(v, hi), lo)
        return top + (hi - v) / (hi - lo) * (h - top - bottom)

    parts = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="Short-term loudness over time with the target window" style="width:100%;height:auto;font-family:inherit">']
    # target window from the first primary loudness rule
    band = None
    if report.profile.loudness:
        for r in report.profile.loudness.rules:
            if r.role == "primary" and r.min is not None and r.max is not None:
                band = (r.min, r.max)
                break
    if band:
        parts.append(f'<rect x="{left}" y="{Y(band[1]):.1f}" width="{w-left-right}" height="{Y(band[0])-Y(band[1]):.1f}" fill="#0F6E8C" fill-opacity="0.10"/>')
        parts.append(f'<text x="{w-right-4}" y="{Y(band[1])-3:.1f}" text-anchor="end" font-size="10" fill="#0F6E8C">target {band[0]:g} to {band[1]:g}</text>')
    for g in np.arange(lo, hi + 0.1, 10):
        parts.append(f'<line x1="{left}" x2="{w-right}" y1="{Y(g):.1f}" y2="{Y(g):.1f}" stroke="#D7DBD8" stroke-width="1"/>')
        parts.append(f'<text x="{left-6}" y="{Y(g)+3.5:.1f}" text-anchor="end" font-size="10" fill="#5C6663">{g:g}</text>')
    pts = " ".join(f"{X(a):.1f},{Y(b if np.isfinite(b) else lo):.1f}" for a, b in zip(t, st))
    parts.append(f'<polyline points="{pts}" fill="none" stroke="#1E2321" stroke-width="1.6"/>')
    if np.isfinite(m.loudness.integrated):
        yi = Y(m.loudness.integrated)
        parts.append(f'<line x1="{left}" x2="{w-right}" y1="{yi:.1f}" y2="{yi:.1f}" stroke="#0F6E8C" stroke-width="1.4" stroke-dasharray="5 4"/>')
        parts.append(f'<text x="{left+4}" y="{max(yi-4, top+10):.1f}" font-size="10" fill="#0F6E8C">integrated {m.loudness.integrated:.1f}</text>')
    if finite.size:
        i = int(np.nanargmax(np.where(np.isfinite(st), st, -np.inf)))
        ys = Y(st[i])
        parts.append(f'<circle cx="{X(t[i]):.1f}" cy="{ys:.1f}" r="3.5" fill="#B26E15"/>')
        label_y = ys + 14 if ys < top + 24 else ys - 6
        parts.append(f'<text x="{min(X(t[i])+6, w-right-120):.1f}" y="{label_y:.1f}" font-size="10" fill="#B26E15">max S {st[i]:.1f} at {t[i]:.0f}s</text>')
    for sec in np.linspace(x0, x1, 6):
        parts.append(f'<text x="{X(sec):.1f}" y="{h-8}" text-anchor="middle" font-size="10" fill="#5C6663">{sec:.0f}s</text>')
    parts.append("</svg>")
    return "".join(parts)


def render_html(report: Report) -> str:
    m, p = report.measurement, report.profile
    now = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
    kind = "package" if m.is_package else "file"
    tiles = [
        ("Integrated", _fmt(m.loudness.integrated, ""), "LUFS"),
        ("True peak", _fmt(m.peaks.true_peak_dbtp, "", signed=True), "dBTP"),
        ("Loudness range", _fmt(m.loudness.lra, ""), "LU"),
        ("Max short-term", _fmt(m.loudness.short_term_max, ""), "LUFS"),
        ("Duration", f"{int(m.duration_s // 60)}:{m.duration_s % 60:04.1f}", "min:s"),
        ("Format", f"{m.samplerate/1000:g} kHz" + (f" / {m.info.bit_depth}-bit" if m.info and m.info.bit_depth else ""), m.layout),
    ]
    rows = []
    for f in report.findings:
        note = _esc(f.note)
        rows.append(f'<tr><td><span class="st {f.status.value}">{STATUS_LABEL[f.status]}</span></td><td>{_esc(f.what)}</td><td class="num">{_esc(f.measured)}</td><td class="num">{_esc(f.limit)}</td><td class="note">{note}</td></tr>')
    fixes = "".join(f"<li>{_esc(x)}</li>" for x in report.fixes())
    clause_rows = "".join(f"<tr><td>{_esc(code)}</td><td>{_esc(text)}</td></tr>" for code, text in p.clauses.items())
    sources = "".join(
        f"<li><strong>{_esc(s.grade.value)}</strong> {_esc(s.title)}" + (f", {_esc(s.version)}" if s.version else "") + (f" ({_esc(s.published)})" if s.published else "") + f" — {_esc(s.publisher)}" + (f' <a href="{_esc(s.url)}">{_esc(s.url)}</a>' if s.url else "") + f" · retrieved {s.retrieved.isoformat()}" + (f" <em>{_esc(s.notes)}</em>" if s.notes else "") + "</li>"
        for s in p.provenance
    )
    verbatim = "verbatim" if p.clauses_verbatim else "paraphrased pending verbatim quotes"
    svg = _timeline_svg(report)
    timeline = f'<h2>Short-term loudness</h2><figure>{svg}<figcaption>3 s short-term loudness (EBU Tech 3341) every 100 ms; dashed line is the integrated value; shaded band is the destination\'s window; the dot marks the loudest 3 s.</figcaption></figure>' if svg else ""
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>QC sheet: {_esc(m.path.name)}</title><style>{CSS}</style></head>
<body><div class="sheet">
<header>
  <div>
    <h1>Audio delivery QC sheet</h1>
    <div class="file">{_esc(m.path.name)}</div>
    <div class="meta">{kind}, {_esc(m.layout)}, {m.samplerate/1000:g} kHz{(', ' + str(m.info.bit_depth) + '-bit ' + _esc(m.info.container)) if m.info and m.info.bit_depth else ''}, {m.duration_s:.1f} s</div>
    <div class="meta">Destination: <strong>{_esc(p.name)}</strong> ({_esc(p.id)}) · sources graded <strong>{_esc(p.grade.value)}</strong>{' · includes tool defaults' if p.has_defaults else ''}</div>
    <div class="meta">{now} · cumple {__version__}</div>
  </div>
  <div class="verdict {'pass' if report.passed else 'fail'}">{report.verdict}</div>
</header>
<div class="tiles">{"".join(f'<div class="tile"><div class="k">{_esc(k)}</div><div class="v">{_esc(v)}</div><div class="u">{_esc(u)}</div></div>' for k, v, u in tiles)}</div>
<h2>Findings</h2>
<table><thead><tr><th></th><th>Check</th><th>Measured</th><th>Limit</th><th>Note</th></tr></thead><tbody>{"".join(rows)}</tbody></table>
{('<h2>What would fix it</h2><ul class="fixes">' + fixes + '</ul>') if fixes else ''}
{timeline}
<h2>In the source's words <span class="note">({verbatim})</span></h2>
<table class="clauses"><tbody>{clause_rows}</tbody></table>
<h2>Sources</h2>
<ul class="sources">{sources}</ul>
<footer>Grades: {"; ".join(f"{g.value} = {_esc(label)}" for g, label in GRADE_LABEL.items())}.<br>
Measured with cumple {__version__}: ITU-R BS.1770-5 K-weighting and gating, EBU Tech 3341/3342 short-term and loudness range, 4x oversampled true peak per BS.1770 Annex 2. Dialogue-gated rules are approximated as full-programme BS.1770-1 until the speech gate lands, and say so above.</footer>
</div></body></html>
"""


def write_sheet(report: Report, out_html: Path, pdf: bool = False) -> tuple[Path, Path | None]:
    out_html = Path(out_html)
    out_html.write_text(render_html(report), encoding="utf-8")
    pdf_path = None
    if pdf:
        pdf_path = out_html.with_suffix(".pdf")
        if not to_pdf(out_html, pdf_path):
            pdf_path = None
    return out_html, pdf_path


CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
]


def find_chrome() -> str | None:
    for c in CHROME_CANDIDATES:
        if Path(c).exists():
            return c
    for name in ("google-chrome", "chromium", "chromium-browser", "chrome"):
        found = shutil.which(name)
        if found:
            return found
    return None


def to_pdf(html_path: Path, pdf_path: Path) -> bool:
    chrome = find_chrome()
    if chrome is None:
        return False
    cmd = [chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={pdf_path}", html_path.resolve().as_uri()]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=60)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return False
    return pdf_path.exists() and pdf_path.stat().st_size > 0
