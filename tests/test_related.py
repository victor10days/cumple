"""RELATED.md and ROADMAP.md keep their receipts: a source and a date per row, a status per item."""

from __future__ import annotations

import re
from pathlib import Path

from tests.test_site_numbers import _tables

ROOT = Path(__file__).resolve().parents[1]
RELATED = (ROOT / "docs" / "RELATED.md").read_text(encoding="utf-8")
ROADMAP = (ROOT / "docs" / "ROADMAP.md").read_text(encoding="utf-8")
PAGE = (ROOT / "site" / "index.html").read_text(encoding="utf-8")

DOCUMENTATION_SECTIONS = (
    "Open-source meters run here",
    "Commercial meters, from their documentation",
    "File-based QC platforms, from their documentation",
)
DATE = re.compile(
    r"\b(20\d\d-\d\d-\d\d|\d{1,2} (January|February|March|April|May|June|July|August|September|October|November|December) 20\d\d)\b"
)
STATUSES = ("queued", "proposed", "building", "merged", "accepted", "out of scope")


def _sections(text: str) -> dict[str, str]:
    """Body text under each '## ' heading."""
    out: dict[str, str] = {}
    name = None
    for line in text.splitlines():
        if line.startswith("## "):
            name = line[3:].strip()
            out[name] = ""
        elif name is not None:
            out[name] += line + "\n"
    return out


def test_every_tool_section_states_a_source_and_a_read_date():
    sections = _sections(RELATED)
    per_tool = [n for n in sections if n not in DOCUMENTATION_SECTIONS and n not in ("cumple", "Where cumple sits")]
    assert per_tool, "the per-tool sections the page's table rests on are gone"
    for name in per_tool:
        body = sections[name]
        assert "http" in body, name
        assert DATE.search(body), name


def test_every_documentation_row_carries_a_url_and_the_read_date():
    sections = _sections(RELATED)
    for name in DOCUMENTATION_SECTIONS:
        assert name in sections, name
        header = next(line for line in sections[name].splitlines() if line.startswith("|"))
        rows = _tables(sections[name], header)
        assert rows, name
        source_col = next(c for c in rows[0] if c.lower().startswith("source"))
        for r in rows:
            cell = r[source_col]
            assert "http" in cell or "not run here" in cell or "not read here" in cell, (name, r)
            assert DATE.search(cell) or DATE.search(source_col), (name, r)


def test_the_page_note_names_the_documentation_sections():
    note = re.search(r'<p class="note">(.*?)</p>', PAGE[PAGE.index('id="compare"') :], re.S)
    assert note is not None
    for name in DOCUMENTATION_SECTIONS:
        assert name in note.group(1), name


def test_roadmap_rows_carry_a_status_and_the_run_folder_exists():
    rows = _tables(ROADMAP, "| Id |")
    assert len(rows) >= 8
    for r in rows:
        assert re.fullmatch(r"R\d+", r["Id"]), r
        assert any(r["Status"].startswith(s) for s in STATUSES), r
    for folder in re.findall(r"`docs/graph-runs/([^`/]+)/`", ROADMAP):
        assert (ROOT / "docs" / "graph-runs" / folder / "01-frame.md").exists(), folder


def test_no_dashes_in_the_documents_a_reader_gets():
    for name in ("README.md", "docs/ROADMAP.md", "docs/RELATED.md", "AI_USAGE.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "—" not in text and "–" not in text, name
