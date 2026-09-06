"""The QC sheet: one page that travels with the deliverable.

Plain HTML with the style and the fonts inline, so it opens anywhere, offline, and prints to A4.
PDF export uses the Chrome already on the machine (headless print), never a web service. The
design system it follows is design.md at the repository root; the tokens are in tokens.css.
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
from .style import document_css

STATUS_LABEL = {Status.PASS: "PASS", Status.FAIL: "FAIL", Status.WARN: "WARN", Status.INFO: "info", Status.SKIP: "n/a"}


def _esc(x) -> str:
    return html.escape("" if x is None else str(x))


def _fmt(x: float | None, unit: str, signed: bool = False) -> str:
    if x is None or not np.isfinite(x):
        return "n/a"
    return (f"{x:+.1f}" if signed else f"{x:.1f}") + (f" {unit}" if unit else "")


def _mmss(seconds: float) -> str:
    """m:ss.s with the rounding done first, so 59.97 s reads 1:00.0 and never 0:60.0."""
    tenths = int(round(max(seconds, 0.0) * 10))
    return f"{tenths // 600}:{(tenths % 600) / 10:04.1f}"


def _pct(v: float, total: float) -> str:
    return f"{v / total * 100:.2f}%"


def _hz(c: float) -> str:
    return f"{c / 1000:g} kHz" if c >= 1000 else f"{c:g} Hz"


def plot_labels(labels: list[tuple[str, float, float, str]], w: float, h: float) -> str:
    """HTML labels over a scaling SVG: (text, x, y, classes) in viewBox units become percentages.

    The SVG keeps its aspect ratio as it scales, so a label at top: y/h and left: x/w sits exactly
    where the drawn mark is at any page width, while its type stays a real 10 to 11 px.
    """
    return "".join(
        f'<span class="lab {cls}" style="left:{_pct(x, w)};top:{_pct(y, h)}">{_esc(text)}</span>'
        for text, x, y, cls in labels
    )


def _timeline(report: Report) -> str:
    m = report.measurement
    st = m.loudness.short_term
    if st.size < 2:
        return ""
    t = m.loudness.short_term_times()
    w, h, left, right, top, bottom = 800, 200, 44, 12, 12, 24
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

    band = None
    if report.profile.loudness:
        for r in report.profile.loudness.rules:
            if r.role == "primary" and r.min is not None and r.max is not None:
                band = (r.min, r.max)
                break
    svg = [
        f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="Short-term loudness over time with the destination’s window">'
    ]
    if band:
        svg.append(
            f'<rect class="band" x="{left}" y="{Y(band[1]):.1f}" width="{w - left - right}" height="{Y(band[0]) - Y(band[1]):.1f}"/>'
        )
    labels: list[tuple[str, float, float, str]] = []
    for g in np.arange(lo, hi + 0.1, 10):
        svg.append(f'<line class="grid" x1="{left}" x2="{w - right}" y1="{Y(g):.1f}" y2="{Y(g):.1f}"/>')
        labels.append((f"{g:g}", left - 6, Y(g), "y"))
    pts = " ".join(f"{X(a):.1f},{Y(b if np.isfinite(b) else lo):.1f}" for a, b in zip(t, st, strict=True))
    svg.append(f'<polyline class="curve" points="{pts}"/>')
    legend = ["<span><i></i>3 s short-term</span>"]
    if np.isfinite(m.loudness.integrated):
        yi = Y(m.loudness.integrated)
        svg.append(f'<line class="ref" x1="{left}" x2="{w - right}" y1="{yi:.1f}" y2="{yi:.1f}"/>')
        legend.append(f'<span><i class="dash"></i>integrated {m.loudness.integrated:.1f} LUFS</span>')
    if band:
        legend.append(f'<span><i class="band"></i>window {band[0]:g} to {band[1]:g}</span>')
    if finite.size:
        i = int(np.nanargmax(np.where(np.isfinite(st), st, -np.inf)))
        svg.append(f'<circle class="dot" cx="{X(t[i]):.1f}" cy="{Y(st[i]):.1f}" r="3.5"/>')
        legend.append(f'<span><i class="dot"></i>loudest 3 s: {st[i]:.1f} LUFS at {t[i]:.0f} s</span>')
    for sec in np.linspace(x0, x1, 6):
        labels.append((f"{sec:.0f} s", X(sec), h - bottom + 6, "x"))
    svg.append("</svg>")
    return (
        "<h2>Short-term loudness</h2><figure>"
        f'<div class="plot">{"".join(svg)}{plot_labels(labels, w, h)}</div>'
        f'<div class="legend">{"".join(legend)}</div>'
        "<figcaption>3 s short-term loudness (EBU Tech 3341) every 100 ms in LUFS; the dashed line is the "
        "integrated value, the shaded band the destination’s window, the dot the loudest 3 s.</figcaption>"
        "</figure>"
    )


def render_html(report: Report) -> str:
    m, p = report.measurement, report.profile
    now = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
    kind = "package" if m.is_package else "file"
    strip = [
        ("Integrated", _fmt(m.loudness.integrated, ""), "LUFS"),
        ("True peak", _fmt(m.peaks.true_peak_dbtp, "", signed=True), "dBTP"),
        ("Loudness range", _fmt(m.loudness.lra, ""), "LU"),
        ("Max short-term", _fmt(m.loudness.short_term_max, ""), "LUFS"),
        ("Duration", _mmss(m.duration_s), "min:s"),
        (
            "Format",
            f"{m.samplerate / 1000:g} kHz",
            (f"{m.info.bit_depth}-bit · " if m.info and m.info.bit_depth else "") + m.layout,
        ),
    ]
    rows = []
    for f in report.findings:
        note = f'<td class="note" data-h="Note">{_esc(f.note)}</td>' if f.note else '<td class="note"></td>'
        rows.append(
            f'<tr><td class="lead"><span class="st {f.status.value}">{STATUS_LABEL[f.status]}</span></td>'
            f"<td>{_esc(f.what)}</td>"
            f'<td class="num" data-h="Measured">{_esc(f.measured)}</td>'
            f'<td class="num" data-h="Limit">{_esc(f.limit)}</td>{note}</tr>'
        )
    fixes = "".join(f"<li>{_esc(x)}</li>" for x in report.fixes())
    clause_rows = "".join(f"<tr><td>{_esc(code)}</td><td>{_esc(text)}</td></tr>" for code, text in p.clauses.items())
    sources = "".join(
        f"<li><b>{_esc(s.grade.value)}</b> {_esc(s.title)}"
        + (f", {_esc(s.version)}" if s.version else "")
        + (f" ({_esc(s.published)})" if s.published else "")
        + f" · {_esc(s.publisher)}"
        + (f' <a href="{_esc(s.url)}">{_esc(s.url)}</a>' if s.url else "")
        + f" · retrieved {s.retrieved.isoformat()}"
        + (f" <em>{_esc(s.notes)}</em>" if s.notes else "")
        + "</li>"
        for s in p.provenance
    )
    verbatim = "verbatim" if p.clauses_verbatim else "paraphrased pending verbatim quotes"
    depth = (", " + str(m.info.bit_depth) + "-bit " + _esc(m.info.container)) if m.info and m.info.bit_depth else ""
    defaults = " · includes tool defaults" if p.has_defaults else ""
    strip_html = "".join(
        f'<div><div class="k">{_esc(k)}</div><div class="v">{_esc(v)}</div><div class="u">{_esc(u)}</div></div>'
        for k, v, u in strip
    )
    fixes_html = f'<h2>What would fix it</h2><ul class="fixes">{fixes}</ul>' if fixes else ""
    grades = "; ".join(f"{g.value} = {_esc(label)}" for g, label in GRADE_LABEL.items())
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>QC sheet: {_esc(m.path.name)}</title><style>{document_css()}</style></head>
<body><div class="sheet">
<header class="head">
  <div>
    <h1>Audio delivery QC sheet</h1>
    <div class="file">{_esc(m.path.name)}</div>
    <div class="meta">{kind}, {_esc(m.layout)}, {m.samplerate / 1000:g} kHz{depth}, {m.duration_s:.1f} s</div>
    <div class="meta">Destination: <b>{_esc(p.name)}</b> ({_esc(p.id)}) · sources graded <b>{_esc(p.grade.value)}</b>{defaults}</div>
    <div class="meta">{now} · cumple {__version__}</div>
  </div>
  <div class="stamp {"pass" if report.passed else "fail"}">{_esc(report.verdict)}</div>
</header>
<div class="strip">{strip_html}</div>
<h2>Findings</h2>
<table class="findings stack"><thead><tr><th></th><th>Check</th><th>Measured</th><th>Limit</th><th>Note</th></tr></thead><tbody>{"".join(rows)}</tbody></table>
{fixes_html}
{_timeline(report)}
<h2>In the source’s words <span class="note">({verbatim})</span></h2>
<table class="clauses"><tbody>{clause_rows}</tbody></table>
<h2>Sources</h2>
<ul class="sources">{sources}</ul>
<footer class="colophon">Grades: {grades}.<br>
Measured with cumple {__version__}: ITU-R BS.1770-5 K-weighting and gating, EBU Tech 3341/3342 short-term and loudness range, 4x oversampled true peak per BS.1770 Annex 2. Dialogue-gated rules use a heuristic speech detector, an approximation of Dolby Dialogue Intelligence, and say so above.</footer>
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
    cmd = [
        chrome,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        html_path.resolve().as_uri(),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=60)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return False
    return pdf_path.exists() and pdf_path.stat().st_size > 0
