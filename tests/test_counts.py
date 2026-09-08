"""The documented test count must match what pytest collects, so the number cannot drift."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EBU_CASES = 29  # skipped without the test set; still collected
COUNTS = {
    "README.md": r"\*\*Tests\*\*: (\d+),",
    "CONTRIBUTING.md": r"# (\d+) tests;",
    "docs/QA.md": r"`uv run pytest`, (\d+) tests",
    "AI_USAGE.md": r"(\d+) tests, including",
    "site/index.html": r"(\d+) tests with 91",
}


def test_documented_test_count_matches_the_collected_suite(request):
    n = len(request.session.items)
    if n < 100:  # a subset was collected; the documented number describes the whole suite
        pytest.skip("run the whole suite to check the documented count")
    for name, pattern in COUNTS.items():
        m = re.search(pattern, (ROOT / name).read_text(encoding="utf-8"))
        assert m, f"{name}: no test count found"
        assert int(m.group(1)) == n, f"{name} says {m.group(1)} tests, pytest collected {n}"
    ci = re.search(r"runs (\d+) of them on Ubuntu", (ROOT / "README.md").read_text(encoding="utf-8"))
    assert ci and int(ci.group(1)) == n - EBU_CASES, "README's CI count must be the suite minus the EBU cases"
