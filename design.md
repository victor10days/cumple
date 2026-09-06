# Design: cumple

A locked design system for every surface cumple puts in front of a person:
the QC sheet, the diff sheet, and the one-page infographic about the tool.
Each surface reads this file before it is changed. Extend or amend this file
when the system needs to grow; do not restyle a surface on its own.

## Genre

modern-minimal, in its instrument-panel register: a document a post
supervisor reads in ten seconds, prints, and sends with the deliverables.
Tone: utilitarian.

## Macrostructure family

- Sheets (the QC sheet, the diff sheet): a spec-sheet document. Header with
  the verdict as a stamp, a numbered stat strip, tabular findings with
  hairline rules, a figure with its labels in HTML, the source's words, the
  sources, a dense colophon. No nav. Footer archetype Ft4 dense colophon.
- The infographic: Split Studio. Each claim on one side, its proof on the
  other, alternating direction down the page; one full-bleed dark band as the
  single bold move. No nav. Footer archetype Ft2 inline single line.

## Theme

Custom, tuned to the product's own teal. The tokens live in
`src/cumple/report/tokens.css` and are the single source; `report/style.py`
inlines them into every sheet, and the infographic copies the block verbatim.

- `--color-paper`  oklch(98% 0.005 225)
- `--color-paper-2` oklch(95.5% 0.007 225)
- `--color-ink`    oklch(20% 0.012 230)
- `--color-ink-2`  oklch(34% 0.012 230)
- `--color-muted`  oklch(46% 0.015 230)
- `--color-rule`   oklch(86% 0.010 225)
- `--color-accent` oklch(47% 0.10 225)
- `--color-focus`  oklch(50% 0.16 225)
- Verdicts: pass oklch(46% 0.11 150), fail oklch(50% 0.16 28), warn
  oklch(56% 0.13 70), each with a tint fill and a dark ink for small pills.
- A dark set with the same hue exists for the infographic's dark theme.

Axes: light / display-condensed-bold / cool.

## Typography

- Display: Barlow Condensed, weights 600 and 700, roman. Verdicts, the big
  numbers in the stat strip, section headings on the infographic.
- Body: IBM Plex Sans, weights 400 and 600. Everything read.
- Mono: IBM Plex Mono, weight 400. File names, rule codes, code, terminal
  output, numeric columns. Never labels or headings.
- Display tracking: -0.01em; label tracking 0.08em with uppercase.
- Scale: 1.25 from the root (13 px on the sheets, 16 px on the infographic).
- The sheets embed woff2 subsets of the five faces from
  `src/cumple/report/fonts/` (SIL Open Font License), so a sheet renders the
  same offline and in PDF on any machine. The infographic links Google Fonts.

## Spacing

4-point named scale in `tokens.css` (`--space-3xs` to `--space-3xl`), in
px so print and screen agree. Surfaces use the names, never raw values.

## Motion

- Easings: `--ease-out` cubic-bezier(0.16, 1, 0.3, 1), `--ease-in`
  cubic-bezier(0.7, 0, 0.84, 0).
- Reveal pattern: none. The sheets are still; the infographic is composed.
- Reduced-motion fallback: not needed while nothing moves.

## Microinteractions stance

- The sheets have no interactive elements beyond source links.
- Links: accent colour, underline on hover, an instant 2 px focus ring.

## CTA voice

None. A QC sheet asks for nothing; the fixes list is the only imperative.

## Per-page allowances

- Sheets: typography, tables and one data figure each. No enrichment, no
  imagery, no motion.
- Infographic: real figures (the sheet screenshot, the pipeline diagram,
  charts drawn from repository numbers). No illustration, no stock.

## What surfaces MUST share

- The tokens: paper, ink, rules, accent, verdict colours.
- The three faces and their roles.
- Square corners on documents; 4 px radius on code blocks only.
- Verdict language: PASS, FAIL, WARN, info, n/a, and the stamp treatment.
- The colophon: measurement note plus the grade key.

## What surfaces MAY differ on

- Root size (13 px sheets, 16 px infographic).
- The dark theme (infographic only).
- Section rhythm (the infographic alternates halves; the sheets read top to
  bottom).

## Exports

`src/cumple/report/tokens.css` is the export. Copy the `:root` block.
