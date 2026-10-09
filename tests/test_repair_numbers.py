"""The figures in docs/REPAIR.md must be the ones its tables carry, and the bounds the spec sets must hold in them."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import soundfile as sf

from cumple.repair import chain as chains
from cumple.repair import damage, metrics
from tests.test_repair_baselines import FIXTURE
from tests.test_repair_core import needs_core
from tests.test_site_numbers import _tables

ROOT = Path(__file__).resolve().parents[1]
REPORT = (ROOT / "docs" / "REPAIR.md").read_text(encoding="utf-8")

# damage kind: the column after Reference in its per-file tables
KINDS = {
    "clip": "Input SDR (dB)",
    "impulse": "Seed",
    "burst": "Seed",
}
TITLES = {"clip": "De-clip", "impulse": "Impulse De-click", "burst": "Burst De-click"}
NOT_SHORT = "not run (shorter than one block)"
# A mean over rounded cells and then rounded itself can sit one rounding step from the exact mean.
MEAN_TOLERANCE = {"all": 0.011, "dmg": 0.011, "peak": 0.11}


def _section(title: str) -> str:
    m = re.search(rf"^## {re.escape(title)}\n(.*?)(?=^## |\Z)", REPORT, re.S | re.M)
    assert m, f"no section {title!r} in docs/REPAIR.md"
    return m.group(1)


def _score_rows(kind: str) -> list[dict[str, str]]:
    return _tables(_section(TITLES[kind]), f"| Reference | {KINDS[kind]} | ffmpeg")


def _detail_rows(kind: str) -> list[dict[str, str]]:
    return _tables(_section(TITLES[kind]), f"| Reference | {KINDS[kind]} | Fidelity")


def _tool_column(row: dict[str, str], tool: str) -> str:
    key = next(k for k in row if k.startswith(tool))
    return row[key]


def _floats(cell: str) -> list[float]:
    return [float(x) for x in re.findall(r"[+-]?(?:\d+\.\d+|\d+|inf)(?:e[+-]?\d+)?", cell.replace("−", "-"))]


def _ran(cell: str) -> bool:
    return not cell.startswith("not run")


def _clicks(cell: str) -> tuple[int, int, int]:
    """(missed, of, false) from a De-click cell 'dSDR / m of n / f'."""
    m = re.fullmatch(r"\S+ / (\d+) of (\d+) / (\d+)", cell)
    assert m, cell
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def _cell_values(kind: str, cell: str) -> dict[str, float]:
    """The numbers a score cell carries, by the summary column they feed."""
    if kind == "clip":
        a, d, p = (float(x) for x in cell.split(" / "))
        return {"all": a, "dmg": d, "peak": p}
    return {"all": float(cell.split(" / ")[0])}


def _mean(values: list[float]) -> float:
    finite = [v for v in values if np.isfinite(v)]
    return float(np.mean(finite))


def _summary(section: str) -> list[dict[str, str]]:
    return _tables(_section(section), "| Damage | Tool |")


def _check_summary_row(kind: str, row: dict[str, str], rows: list[dict[str, str]], names: set[str] | None) -> None:
    """One summary row equals the means of its tool's column over the files it ran on (and `names`, when paired)."""
    tool = row["Tool"]
    cells = [
        (r["Reference"], _tool_column(r, tool))
        for r in rows
        if _ran(_tool_column(r, tool)) and (names is None or r["Reference"] + "|" + _level(r) in names)
    ]
    assert row["Files ran"] == f"{len(cells)} of {len(rows)}", (kind, tool, row["Files ran"], len(cells))
    values = [_cell_values(kind, c) for _, c in cells]
    got = float(row["Mean ΔSDR all (dB)"])
    assert abs(got - _mean([v["all"] for v in values])) <= MEAN_TOLERANCE["all"], (kind, tool)
    if kind == "clip":
        assert abs(float(row["Mean ΔSDR damaged (dB)"]) - _mean([v["dmg"] for v in values])) <= MEAN_TOLERANCE["dmg"]
        assert abs(float(row["Mean peak error (dB)"]) - _mean([v["peak"] for v in values])) <= MEAN_TOLERANCE["peak"]
    else:
        clicks = [_clicks(c) for _, c in cells]
        total = sum(n for _, n, _ in clicks)  # the click counts of the files this tool ran on
        assert row["Clicks missed"] == f"{sum(m for m, _, _ in clicks)} of {total}", (kind, tool)
        assert row["False detections"] == str(sum(f for _, _, f in clicks)), (kind, tool)


def _level(row: dict[str, str]) -> str:
    return next(v for k, v in row.items() if k in KINDS.values())


def _kind_of(title: str) -> str:
    return next(k for k, t in TITLES.items() if t == title)


def _runs_of_all_three(kind: str) -> set[str]:
    rows = _score_rows(kind)
    ok = set()
    for r in rows:
        if all(_ran(_tool_column(r, t)) for t in ("ffmpeg", "cathar", "cumple")):
            ok.add(r["Reference"] + "|" + _level(r))
    return ok


def test_summary_means_equal_the_table_columns():
    for row in _summary("Summary"):
        if row["Tool"] == "RX 8":
            continue
        kind = _kind_of(row["Damage"])
        _check_summary_row(kind, row, _score_rows(kind), None)


def test_paired_summary_covers_the_same_files_for_every_tool_it_compares():
    rows = _summary("Summary, paired")
    assert {r["Tool"] for r in rows} == {"ffmpeg", "cathar", "cumple"}  # RX 8 joins when its outputs exist
    for title in TITLES.values():
        kind = _kind_of(title)
        paired = [r for r in rows if r["Damage"] == title]
        assert len({r["Files ran"] for r in paired}) == 1, title  # the rows of a damage type cover the same files
        names = _runs_of_all_three(kind)
        assert paired[0]["Files ran"] == f"{len(names)} of {len(_score_rows(kind))}", title
        for row in paired:
            _check_summary_row(kind, row, _score_rows(kind), names)


# The summary columns that do not apply to a damage kind, the only cells of a summary that may read "n/a".
NOT_APPLICABLE = {
    "clip": {"Clicks missed", "False detections"},
    "impulse": {"Mean ΔSDR damaged (dB)", "Mean peak error (dB)"},
    "burst": {"Mean ΔSDR damaged (dB)", "Mean peak error (dB)"},
}


def test_every_table_cell_is_a_number_or_not_run_and_nothing_says_not_checked():
    assert ("not " + "checked") not in REPORT.lower()  # spec rule 4
    for kind in KINDS:
        for row in _score_rows(kind):
            for key, cell in row.items():
                if key.startswith(("ffmpeg", "cathar", "cumple", "RX 8")):
                    assert cell.startswith("not run") or _floats(cell), (kind, key, cell)
        for row in _detail_rows(kind):
            for key, cell in row.items():
                if key not in ("Reference", KINDS[kind]):
                    assert cell.startswith("not run") or _floats(cell) or cell in ("equal", "differ"), (kind, key, cell)
    for section in ("Summary", "Summary, paired"):
        rows = _summary(section)
        assert {r["Damage"] for r in rows} == set(TITLES.values()), section
        for row in rows:
            kind = _kind_of(row["Damage"])
            for key, cell in row.items():
                if key in ("Damage", "Tool"):
                    continue
                figure = _floats(cell) if key not in NOT_APPLICABLE[kind] else cell == "n/a"
                assert cell.startswith("not run") or figure, (section, row["Damage"], row["Tool"], key, cell)


def test_cumple_is_scored_on_every_file_and_the_precision_effect_is_reported():
    for kind in KINDS:
        rows = _score_rows(kind)
        assert rows and all(_ran(_tool_column(r, "cumple")) for r in rows), kind
        detail = _detail_rows(kind)
        assert len(detail) == len(rows), kind
        assert all("Precision ΔSDR diff (dB)" in d and "Precision max sample" in d for d in detail), kind
        assert all(_floats(d["Precision ΔSDR diff (dB)"]) and _floats(d["Precision max sample"]) for d in detail)
    for title in ("Impulse De-click", "Burst De-click"):
        assert all("Precision gaps differing" in d for d in _detail_rows(_kind_of(title)))


def test_port_fidelity_holds_on_every_row():
    """Spec rule 1: 1e-6 per sample and 0.01 dB, and for De-click the same gaps. These bounds are never widened."""
    for kind in KINDS:
        assert len(_detail_rows(kind)) == len(_score_rows(kind)) > 0, kind  # a missing table must not pass vacuously
        for d in _detail_rows(kind):
            label = f"{kind} {d['Reference']} {_level(d)}"
            (worst,) = _floats(d["Fidelity max sample"])
            (gap,) = _floats(d["Fidelity ΔSDR diff (dB)"])
            assert worst < 1e-6, label
            assert abs(gap) < 0.01, label
            if kind != "clip":
                assert d["Fidelity gaps"] == "equal", label


def test_chunking_cost_is_held_and_only_references_longer_than_a_block_are_chunked():
    cost = "Chunking ΔSDR cost (dB)"
    for kind in KINDS:
        detail = _detail_rows(kind)
        short = [d for d in detail if d[cost] == NOT_SHORT]
        long = [d for d in detail if d[cost] != NOT_SHORT]
        assert short and all(d["Reference"] == "fixture" for d in short), kind  # 3 s is shorter than one block
        assert long, kind
        for d in short:
            assert d["Chunking max sample"] == NOT_SHORT
        for d in long:
            assert d["Reference"] != "fixture"
            (c,) = _floats(d[cost])
            assert abs(c) < 0.5, (kind, d["Reference"], _level(d), c)
            (worst,) = _floats(d["Chunking max sample"])
            if kind != "clip":  # spec rule 2: De-click's context covers the AR reach, so blocks match one call
                assert worst <= 1e-9, (kind, d["Reference"], _level(d), worst)


def test_false_detections_are_the_tools_own_gaps_and_rule_3_is_reported():
    """Spec rule 3: detections that are not injected clicks are counted, not masked; the header says whose gaps they are."""
    assert "**False detections**" in REPORT and "the f32 build stands in" in REPORT
    m = re.search(r"\*\*Rule 3, [^\n]*: \*\*met on all (\d+) of (\d+) files\*\*", REPORT)
    assert m and m.group(1) == m.group(2)
    total = len(_score_rows("clip")) + len(_score_rows("impulse")) + len(_score_rows("burst"))
    assert int(m.group(1)) == total
    for row in _summary("Summary"):
        if row["Tool"] in ("cumple", "cathar") and row["Damage"] != "De-clip":
            kind = _kind_of(row["Damage"])
            counted = sum(_clicks(_tool_column(r, row["Tool"]))[2] for r in _score_rows(kind))
            assert row["False detections"] == str(counted)


def test_the_clicks_missed_note_names_its_detector_and_the_burst_share_it_sees():
    """Clicks missed is counted by the f64 build's own formula, so cumple's count is not a second opinion, and on the
    burst table that detector sees little: the note says both, with the share the visibility table gives."""
    assert "That detector is the f64 build's own formula" in REPORT and "holds by construction" in REPORT
    rows = _tables(_section("Burst clicks the detector of record can see"), "| Width (samples) |")
    shares = [int(r["Visible"].removesuffix(" %")) for r in rows if r["Visible"] != "n/a"]
    m = re.search(r"the detector sees only (\d+) to (\d+) % of the clicks in each width band", REPORT)
    assert shares and m and (int(m.group(1)), int(m.group(2))) == (min(shares), max(shares))
    missed = [_clicks(_tool_column(r, "cumple"))[0] for kind in ("impulse", "burst") for r in _score_rows(kind)]
    assert f"cumple's Clicks missed ({sum(missed)} over both De-click tables)" in REPORT


def test_the_rx_columns_say_not_run_or_carry_numbers():
    for kind in KINDS:
        for row in _score_rows(kind):
            cell = _tool_column(row, "RX 8")
            assert cell.startswith("not run (") or _floats(cell), (kind, cell)
    assert all(
        r["Files ran"].startswith("0 of") == r["Mean ΔSDR all (dB)"].startswith("not run")
        for r in _summary("Summary")
        if r["Tool"] == "RX 8"
    )


@needs_core
def test_the_fixture_row_matches_a_fresh_run_of_the_core(tmp_path):
    """The pinned fixture row is re-run here: the harness's impulse damage and seed on the fixture, through the runner."""
    from scripts.make_repair_set import CLICKS_PER_MINUTE, IMPULSE_SEED

    from cumple.repair.runner import repair_file

    x, fs = sf.read(FIXTURE, dtype="float64")
    x = x.astype(np.float32).astype(np.float64)
    y, _clicks_added, _ = damage.add_clicks(x, fs, IMPULSE_SEED, CLICKS_PER_MINUTE, **damage.IMPULSE)
    src, dst = tmp_path / "fixture.impulse.wav", tmp_path / "fixed.wav"
    sf.write(src, y, fs, subtype="FLOAT")
    y, _ = sf.read(src, dtype="float64")  # the stored float32 values, as the harness reads them
    result = repair_file(src, chains.parse("declick(threshold=5)"), dst)
    assert result.changed
    est, _ = sf.read(dst, dtype="float64")
    pinned = next(r for r in _score_rows("impulse") if r["Reference"] == "fixture" and r["Seed"] == str(IMPULSE_SEED))
    assert abs(metrics.delta_sdr(x, y, est) - _cell_values("impulse", _tool_column(pinned, "cumple"))["all"]) < 0.05
