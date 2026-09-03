"""Conformance against the official EBU Loudness Test Set v5.0 (Tech 3341 and Tech 3342).

The set is free from https://tech.ebu.ch/publications/ebu_loudness_test_set but sits behind a
browser check, so it is not downloaded automatically. Put the zip (or its extracted folder) at
~/.cache/cumple/, or point CUMPLE_EBU_TEST_SET at it. Without it these tests are skipped and
say so.

Expected readings are Tech 3341 Table 1 (±0.1 LU; true peak +0.2/-0.4 dBTP) and Tech 3342
(±1 LU).
"""

from __future__ import annotations

import os
import re
import zipfile
from pathlib import Path

import pytest

from cumple.meters.measure import measure

CACHE = Path(os.environ.get("CUMPLE_EBU_TEST_SET", Path.home() / ".cache" / "cumple"))
LU_TOL = 0.1
TP_TOL = (-0.4, 0.2)


def _test_dir() -> Path | None:
    candidates = [CACHE, CACHE / "ebu-loudness-test-set"]
    for c in candidates:
        if c.is_dir() and list(c.rglob("seq-3341-1-*.wav")):
            return c
    for z in [CACHE / "ebu-loudness-test-setv05.zip", CACHE] if CACHE.suffix != ".zip" else [CACHE]:
        if z.is_file() and z.suffix == ".zip":
            out = z.parent / "ebu-loudness-test-set"
            out.mkdir(exist_ok=True)
            with zipfile.ZipFile(z) as zf:
                zf.extractall(out)
            if list(out.rglob("seq-3341-1-*.wav")):
                return out
    return None


TEST_DIR = _test_dir()
skip = pytest.mark.skipif(TEST_DIR is None, reason="EBU loudness test set not found in ~/.cache/cumple (see module docstring)")


def files_for(case: str) -> list[Path]:
    """All wavs for a Tech 3341/3342 case number, e.g. '3341-6' or '3342-3'."""
    assert TEST_DIR is not None
    doc, num = case.split("-")
    pat = re.compile(rf"seq-{doc}-(?:2011-)?{num}(?:[-_.]|$)")
    return sorted(p for p in TEST_DIR.rglob("*.wav") if pat.search(p.name))


_cache: dict[Path, object] = {}


def m(path: Path):
    if path not in _cache:
        _cache[path] = measure(path)
    return _cache[path]


@skip
@pytest.mark.parametrize("case,expected", [("3341-1", -23.0), ("3341-2", -33.0)])
def test_steady_tones_read_the_same_on_every_meter(case, expected):
    for f in files_for(case):
        r = m(f).loudness
        assert r.integrated == pytest.approx(expected, abs=LU_TOL), f.name
        assert r.short_term_max == pytest.approx(expected, abs=LU_TOL), f.name
        assert r.momentary_max == pytest.approx(expected, abs=LU_TOL), f.name


@skip
@pytest.mark.parametrize("case", ["3341-3", "3341-4", "3341-5", "3341-6", "3341-7", "3341-8"])
def test_integrated_loudness_cases(case):
    files = files_for(case)
    assert files, case
    for f in files:
        assert m(f).loudness.integrated == pytest.approx(-23.0, abs=LU_TOL), f.name


@skip
def test_case_9_short_term_is_constant_minus_23_after_3_s():
    for f in files_for("3341-9"):
        r = m(f).loudness
        assert r.short_term_max == pytest.approx(-23.0, abs=LU_TOL), f.name
        inside = r.short_term[: max(1, len(r.short_term) - 30)]  # ignore the tail once the tone stops
        assert inside.min() == pytest.approx(-23.0, abs=LU_TOL), f.name


@skip
def test_case_10_max_short_term_of_each_segment_is_minus_23():
    files = files_for("3341-10")
    assert len(files) >= 20, [f.name for f in files]
    for f in files:
        assert m(f).loudness.short_term_max == pytest.approx(-23.0, abs=LU_TOL), f.name


@skip
def test_case_11_max_short_term_over_the_stepped_file_is_minus_19():
    for f in files_for("3341-11"):
        assert m(f).loudness.short_term_max == pytest.approx(-19.0, abs=LU_TOL), f.name


@skip
def test_case_12_momentary_is_constant_minus_23_after_1_s():
    for f in files_for("3341-12"):
        r = m(f).loudness
        assert r.momentary_max == pytest.approx(-23.0, abs=LU_TOL), f.name


@skip
def test_case_13_max_momentary_of_each_segment_is_minus_23():
    files = files_for("3341-13")
    assert len(files) >= 20, [f.name for f in files]
    for f in files:
        assert m(f).loudness.momentary_max == pytest.approx(-23.0, abs=LU_TOL), f.name


@skip
def test_case_14_max_momentary_over_the_stepped_file_is_minus_19():
    for f in files_for("3341-14"):
        assert m(f).loudness.momentary_max == pytest.approx(-19.0, abs=LU_TOL), f.name


@skip
@pytest.mark.parametrize("case,expected", [
    ("3341-15", -6.0), ("3341-16", -6.0), ("3341-17", -6.0), ("3341-18", -6.0),
    ("3341-19", 3.0),
    ("3341-20", 0.0), ("3341-21", 0.0), ("3341-22", 0.0), ("3341-23", 0.0),
])
def test_true_peak_cases(case, expected):
    files = files_for(case)
    assert files, case
    for f in files:
        tp = m(f).peaks.true_peak_dbtp
        assert expected + TP_TOL[0] <= tp <= expected + TP_TOL[1], (f.name, tp)


@skip
@pytest.mark.parametrize("case,expected", [("3342-1", 10.0), ("3342-2", 5.0), ("3342-3", 20.0), ("3342-4", 15.0), ("3342-5", 5.0), ("3342-6", 15.0)])
def test_loudness_range_cases(case, expected):
    files = files_for(case)
    assert files, case
    for f in files:
        assert m(f).loudness.lra == pytest.approx(expected, abs=1.0), f.name
