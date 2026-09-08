"""The figures the page quotes must match the reports they link to."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = (ROOT / "site" / "index.html").read_text(encoding="utf-8")


def _num(cell: str) -> float | None:
    cell = cell.replace("✓", "").replace("✗", "").replace("−", "-").strip()
    try:
        return float(cell)
    except ValueError:
        return None


def _tables(text: str, first_header: str) -> list[dict[str, str]]:
    """Every row of every table whose header line starts with first_header."""
    rows: list[dict[str, str]] = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if not line.startswith(first_header):
            continue
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        for body in lines[i + 2 :]:
            if not body.startswith("|"):
                break
            cells = [c.strip() for c in body.strip().strip("|").split("|")]
            if len(cells) == len(cols):
                rows.append(dict(zip(cols, cells, strict=True)))
    return rows


# The meters the strip's gap figure is measured against. loudcheck is left out: its
# integrated value is libebur128's algorithm run inside ffmpeg, not an independent reading.
GAP_METERS = ("libebur128", "pyloudnorm", "ffmpeg ebur128")


def test_benchmark_gap_on_the_strip():
    rows = _tables((ROOT / "docs" / "BENCHMARK.md").read_text(encoding="utf-8"), "| file | expected I |")
    gaps = []
    for r in rows:
        c = _num(r["cumple"])
        for other in GAP_METERS:
            o = _num(r[other])
            if c is not None and o is not None:
                gaps.append(abs(c - o))
    # Every file has a reading from every meter; a dropped cell must fail here, not shrink the figure.
    assert len(rows) == 22 and len(gaps) == len(GAP_METERS) * len(rows)
    largest = round(max(gaps), 2)
    assert f'<span class="big">{largest:.2f} LU</span>' in PAGE
    assert PAGE.count(f"within {largest:.2f} LU") == 2  # the FAQ answer and its JSON-LD twin


def test_conformance_totals_on_the_strip():
    text = (ROOT / "docs" / "CONFORMANCE.md").read_text(encoding="utf-8")
    m = re.search(r"\*\*(\d+) of (\d+) readings inside tolerance", text)
    assert m and m.group(1) == m.group(2)
    assert f'<span class="big">{m.group(1)} of {m.group(2)}</span>' in PAGE
    cases = {r["case"] for r in _tables(text, "| case |")}
    assert f'<span class="big">{len(cases)} of {len(cases)}</span>' in PAGE


def test_performance_figures_on_the_strip():
    rows = _tables((ROOT / "docs" / "PERF.md").read_text(encoding="utf-8"), "| file |")
    row = next(r for r in rows if r["file"] == "stereo-60min.wav")
    factor, wall, mem = row["real-time factor"], row["wall time"], row["peak memory"]
    assert f'<span class="big">{factor}</span>' in PAGE
    seconds = wall.replace(" s", " seconds")
    assert (
        f'aria-label="{factor[:-1]} times real time: 60 minutes of stereo measured in {seconds} at {mem} peak memory"'
        in PAGE
    )


def test_dialogue_gate_errors_in_the_note():
    text = (ROOT / "docs" / "DIALOGUE.md").read_text(encoding="utf-8")
    deltas = [abs(float(x)) for x in re.findall(r"\| (-?\d+\.\d+) LU \|", text)[:2]]
    assert len(deltas) == 2
    for d in deltas:
        assert f"{d:.1f} LU" in PAGE
