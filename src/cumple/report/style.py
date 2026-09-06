"""The shared style of cumple's documents: the tokens, the embedded fonts, the common CSS.

Every document (the QC sheet, the diff sheet) is one self-contained HTML file that opens offline and
prints to A4, so the five font faces travel inside it as base64 woff2 subsets (SIL Open Font License,
see fonts/OFL-*.txt). The colour, type and spacing tokens live in tokens.css, the single source that
the infographic copies too; nothing in the document CSS names a colour or a font directly.
"""

from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).parent

# (family, weight, file). Barlow Condensed for verdicts, big numbers and headings; Plex Sans for
# everything read; Plex Mono for file names, rule codes and numeric columns.
FONTS: list[tuple[str, int, str]] = [
    ("Barlow Condensed", 600, "BarlowCondensed-SemiBold.woff2"),
    ("Barlow Condensed", 700, "BarlowCondensed-Bold.woff2"),
    ("IBM Plex Sans", 400, "IBMPlexSans-Regular.woff2"),
    ("IBM Plex Sans", 600, "IBMPlexSans-SemiBold.woff2"),
    ("IBM Plex Mono", 400, "IBMPlexMono-Regular.woff2"),
]


@lru_cache(maxsize=1)
def tokens_css() -> str:
    """The token block, verbatim from tokens.css."""
    return (HERE / "tokens.css").read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def font_faces_css() -> str:
    """One @font-face per embedded face; a missing file is skipped and the fallback stack takes over."""
    faces = []
    for family, weight, name in FONTS:
        path = HERE / "fonts" / name
        if not path.exists():
            continue
        b64 = base64.b64encode(path.read_bytes()).decode("ascii")
        faces.append(
            f'@font-face {{ font-family: "{family}"; font-style: normal; font-weight: {weight}; '
            f'font-display: swap; src: url(data:font/woff2;base64,{b64}) format("woff2"); }}'
        )
    return "\n".join(faces)


# Hallmark · genre: modern-minimal · macrostructure: spec-sheet document · theme: custom (cumple)
# design-system: design.md · designed-as-app · nav: none · footer: Ft4 dense colophon · enrichment: none
DOCUMENT_CSS = """
/* Hallmark · genre: modern-minimal · macrostructure: spec-sheet document · theme: custom (cumple) · design-system: design.md · designed-as-app
 * nav: none · footer: Ft4 dense colophon · enrichment: none · T4 strip knobs: layout=auto-fit, number=display, qualifier=under
 * contrast: pass (40-41) · honest: pass (46) · chrome: pass (47) · tokens: pass (48) · mobile: pass (34, 49, 50-57)
 * pre-emit critique: P4 H5 E4 S5 R5 V4 */
html { font-size: 13px; overflow-x: clip; }
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--color-paper); color: var(--color-ink);
  font-family: var(--font-body); font-size: var(--text-base); line-height: var(--lh-body);
  overflow-x: clip; -webkit-font-smoothing: antialiased;
}
.sheet { max-width: 860px; margin: 0 auto; padding: var(--space-lg) var(--space-md) var(--space-xl); }
@media (min-width: 60rem) { .sheet { padding: var(--space-xl) var(--space-xl) var(--space-2xl); } }
a { color: var(--color-accent); text-decoration: none; overflow-wrap: anywhere; }
a:hover { text-decoration: underline; text-underline-offset: 2px; }
a:focus-visible { outline: 2px solid var(--color-focus); outline-offset: 2px; }

/* Header: the title block left, the verdict as a stamp right, a thick rule beneath. */
.head {
  display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: var(--space-md) var(--space-lg);
  align-items: start; padding-bottom: var(--space-md); border-bottom: var(--rule-thick) solid var(--color-ink);
}
.head h1 {
  font-family: var(--font-display); font-weight: 600; font-size: var(--text-xl); line-height: var(--lh-tight);
  letter-spacing: -0.01em; margin: 0 0 var(--space-2xs); overflow-wrap: anywhere; min-width: 0;
}
.file { font-family: var(--font-mono); font-size: var(--text-base); overflow-wrap: anywhere; }
.meta { color: var(--color-muted); font-size: var(--text-sm); margin-top: var(--space-2xs); }
.meta b { color: var(--color-ink-2); font-weight: 600; }
.stamp {
  font-family: var(--font-display); font-weight: 700; font-size: var(--text-3xl); line-height: 1;
  letter-spacing: 0.02em; padding: var(--space-xs) var(--space-md) var(--space-sm);
  color: var(--color-accent-ink); background: var(--color-accent); border-radius: var(--radius-none); align-self: start;
}
.stamp.pass { background: var(--color-pass); }
.stamp.fail { background: var(--color-fail); }
@media (max-width: 40rem) {
  .head { grid-template-columns: minmax(0, 1fr); }
  .stamp { justify-self: start; font-size: var(--text-2xl); }
}

/* The stat strip: numbers in the display face, hairline rules between cells, no boxes. */
.strip {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(7.5rem, 1fr)); gap: 0;
  margin: var(--space-lg) 0 0;
}
.strip > div { padding: var(--space-sm) var(--space-md) var(--space-sm) 0; border-top: var(--rule-hair) solid var(--color-rule); min-width: 0; }
.strip .k { font-size: var(--text-xs); color: var(--color-muted); text-transform: uppercase; letter-spacing: var(--track-label); }
.strip .v {
  font-family: var(--font-display); font-weight: 600; font-size: var(--text-2xl); line-height: 1.05;
  font-variant-numeric: tabular-nums; margin-top: var(--space-2xs); overflow-wrap: anywhere;
}
.strip .u { font-size: var(--text-xs); color: var(--color-muted); }
@media (max-width: 24rem) { .strip { grid-template-columns: repeat(2, minmax(0, 1fr)); } }

h2 {
  font-family: var(--font-body); font-weight: 600; font-size: var(--text-md); line-height: 1.25;
  margin: var(--space-xl) 0 var(--space-xs); padding-top: var(--space-sm); border-top: var(--rule-hair) solid var(--color-rule);
}
h2 .note { font-weight: 400; color: var(--color-muted); font-size: var(--text-sm); }
p { max-width: 75ch; }

table { width: 100%; border-collapse: collapse; font-size: var(--text-base); }
th {
  text-align: left; font-weight: 600; color: var(--color-muted); font-size: var(--text-xs);
  text-transform: uppercase; letter-spacing: var(--track-label); padding: var(--space-xs);
  border-bottom: var(--rule-hair) solid var(--color-rule);
}
td { padding: var(--space-xs); border-bottom: var(--rule-hair) solid var(--color-rule-2); vertical-align: top; }
td.num { font-variant-numeric: tabular-nums; white-space: nowrap; }
td.note, .note { color: var(--color-muted); }
td.code { font-family: var(--font-mono); font-size: var(--text-sm); white-space: nowrap; }
tr.sum td { font-weight: 600; border-top: var(--rule-hair) solid var(--color-rule); }
table.findings th:nth-child(2) { width: 19%; }
table.findings th:nth-child(3) { width: 26%; }
table.findings th:nth-child(4) { width: 23%; }
table.findings td.num { white-space: normal; }
.st {
  display: inline-block; min-width: 3.4em; text-align: center; font-weight: 600; font-size: var(--text-xs);
  letter-spacing: 0.04em; padding: var(--space-3xs) var(--space-xs); border-radius: var(--radius-none);
}
.st.pass { background: var(--color-pass-tint); color: var(--color-pass-ink); }
.st.fail { background: var(--color-fail-tint); color: var(--color-fail-ink); }
.st.warn { background: var(--color-warn-tint); color: var(--color-warn-ink); }
.st.info, .st.skip { background: var(--color-info-tint); color: var(--color-info-ink); }

/* Under 40 rem a row stacks: the pill and the name on one line, the rest labelled by data-h. */
@media (max-width: 40rem) {
  table.stack thead { display: none; }
  table.stack tr { display: block; padding: var(--space-xs) 0; border-bottom: var(--rule-hair) solid var(--color-rule); }
  table.stack td { display: block; border: 0; padding: var(--space-3xs) 0; }
  table.stack td.num, table.stack td.code { white-space: normal; }
  table.stack td.lead { display: inline-block; padding-right: var(--space-xs); }
  table.stack td.lead + td { display: inline-block; font-weight: 600; }
  table.stack td[data-h]::before {
    content: attr(data-h) ": "; color: var(--color-muted); font-size: var(--text-xs);
    text-transform: uppercase; letter-spacing: var(--track-label);
  }
  table.stack tr.sum td { border-top: 0; }
}

.fixes { margin: var(--space-xs) 0 0; padding-left: 1.2em; max-width: 75ch; }
.fixes li { margin: var(--space-2xs) 0; }

/* A figure: the SVG scales with the page, the labels stay a readable size in HTML. */
figure { margin: var(--space-xs) 0 0; }
.plot { position: relative; width: 100%; }
.plot svg { display: block; width: 100%; height: auto; }
.plot .lab {
  position: absolute; font-size: var(--text-xs); line-height: 1; color: var(--color-muted);
  white-space: nowrap; font-variant-numeric: tabular-nums;
}
.plot .lab.y { transform: translate(-100%, -50%); }
.plot .lab.x { transform: translate(-50%, 0); }
.plot .lab.acc { color: var(--color-accent); }
.plot .band { fill: var(--color-accent-soft); }
.plot .grid { stroke: var(--color-rule); stroke-width: 1; }
.plot .zero { stroke: var(--color-ink-2); stroke-width: 1; }
.plot .curve { fill: none; stroke: var(--color-ink); stroke-width: 1.6; }
.plot .ref { stroke: var(--color-accent); stroke-width: 1.4; stroke-dasharray: 5 4; }
.plot .dot { fill: var(--color-warn); }
.plot .bar-up { fill: var(--color-accent); }
.plot .bar-down { fill: var(--color-ink-2); }
.legend { display: flex; flex-wrap: wrap; gap: var(--space-2xs) var(--space-md); font-size: var(--text-sm); color: var(--color-ink-2); margin-top: var(--space-xs); }
.legend i { display: inline-block; width: 14px; height: 0; border-top: 2px solid var(--color-ink); vertical-align: middle; margin-right: 6px; }
.legend i.dash { border-top: 2px dashed var(--color-accent); }
.legend i.band { height: 10px; border: 0; background: var(--color-accent-soft); }
.legend i.dot { width: 8px; height: 8px; border: 0; border-radius: 50%; background: var(--color-warn); }
.legend i.up { border-top: 6px solid var(--color-accent); }
.legend i.down { border-top: 6px solid var(--color-ink-2); }
figcaption { font-size: var(--text-sm); color: var(--color-muted); margin-top: var(--space-xs); max-width: 75ch; }

.clauses td:first-child { font-family: var(--font-mono); font-size: var(--text-sm); white-space: nowrap; }
@media (max-width: 40rem) { .clauses td:first-child { white-space: normal; } }
.sources { font-size: var(--text-sm); color: var(--color-ink-2); padding-left: 1.2em; margin: var(--space-xs) 0 0; }
.sources li { margin: var(--space-2xs) 0; }
.sources b { color: var(--color-ink); }
.files { font-family: var(--font-mono); font-size: var(--text-sm); padding-left: 1.2em; margin: var(--space-xs) 0 0; }
.files li { margin: var(--space-3xs) 0; }
footer.colophon {
  margin-top: var(--space-xl); padding-top: var(--space-sm); border-top: var(--rule-hair) solid var(--color-rule);
  font-family: var(--font-mono); font-size: var(--text-xs); line-height: 1.5; color: var(--color-muted);
}

@media print {
  html { font-size: 12px; }
  body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .sheet { max-width: none; padding: 0; }
  @page { size: A4; margin: 14mm 14mm; }
  h2 { break-after: avoid; }
  tr, .strip > div, figure, .fixes li { break-inside: avoid; }
  a { color: inherit; }
}
"""


def document_css() -> str:
    """Tokens, then the embedded faces, then the document rules: one <style> block per document."""
    return "\n".join([tokens_css(), font_faces_css(), DOCUMENT_CSS])
