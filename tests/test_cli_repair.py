"""`cumple repair`: exit codes, what it prints, and the paths and hints it must print intact."""

from __future__ import annotations

import json

import numpy as np
import pytest
import soundfile as sf
from typer.testing import CliRunner

import cumple.repair
from cumple.cli import app
from tests.test_repair_baselines import FIXTURE
from tests.test_repair_core import needs_core
from tests.test_repair_runner import clicked_fixture, tone

runner = CliRunner()


@pytest.fixture(autouse=True)
def wide_and_isolated(tmp_path, monkeypatch):
    """Wide enough that rich never folds a temporary path, and no preset of the machine running the tests."""
    monkeypatch.setenv("COLUMNS", "500")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))


def run(*args):
    return runner.invoke(app, [str(a) for a in args])


def flat(text: str) -> str:
    return " ".join(text.split())


def clicks_in_receipt(out) -> int:
    receipt = json.loads(out.with_name(out.name + ".cumple-repair.json").read_text(encoding="utf-8"))
    return receipt["reports"][0]["clicks"]


@needs_core
def test_repair_writes_the_copy_and_prints_it_the_receipt_and_the_clicks(tmp_path):
    src, *_ = clicked_fixture(tmp_path)
    out = tmp_path / "out.wav"
    r = run("repair", src, "--chain", "declick()", "--out", out)
    assert r.exit_code == 0, r.stdout
    assert str(out) in r.stdout and str(out.with_name("out.wav.cumple-repair.json")) in r.stdout
    n = clicks_in_receipt(out)
    assert n > 0 and f"{n} clicks repaired" in r.stdout
    assert "bext/iXML" in r.stdout  # the copy carries no metadata, as fix says

    again = tmp_path / "again.wav"
    r = run("repair", src, "--preset", "declick", "--out", again)
    assert r.exit_code == 0, r.stdout
    assert f"{n} clicks repaired" in r.stdout and clicks_in_receipt(again) == n


@needs_core
def test_repair_exits_2_on_a_bad_chain_the_source_as_out_and_a_missing_choice(tmp_path):
    src, *_ = clicked_fixture(tmp_path)
    before = src.read_bytes()
    r = run("repair", src, "--chain", "declick(),dehum()", "--out", tmp_path / "out.wav")
    assert r.exit_code == 2 and "dehum" in r.stdout
    r = run("repair", src, "--chain", "declick()", "--out", src)
    assert r.exit_code == 2 and "source" in r.stdout
    assert src.read_bytes() == before
    assert run("repair", src, "--out", tmp_path / "out.wav").exit_code == 2  # neither --chain nor --preset
    assert run("repair", src, "--chain", "declick()", "--preset", "declick", "--out", tmp_path / "o.wav").exit_code == 2
    assert run("repair", src, "--chain", "declick()").exit_code == 2  # no --out
    assert run("repair", src, "--preset", "declik", "--out", tmp_path / "out.wav").exit_code == 2
    assert sorted(p.name for p in tmp_path.iterdir()) == ["clicks.wav"]


def case_insensitive(folder) -> bool:
    """Whether the folder's volume treats names that differ only in case as one file (macOS's default, Windows)."""
    probe = folder / "case-probe.txt"
    probe.write_text("")
    try:
        return (folder / "CASE-PROBE.TXT").exists()
    finally:
        probe.unlink()


@needs_core
def test_a_case_variant_of_the_source_never_replaces_it(tmp_path):
    """On a case-insensitive volume (macOS's default, Windows) CLICKS.WAV is clicks.wav, so writing it as any target
    would replace the source: refused. On a case-sensitive volume (Linux) it is another file: written, and the
    source stays as it was. Either way the test runs, so the CI counts in README stay exact."""
    one_file = case_insensitive(tmp_path)
    src, *_ = clicked_fixture(tmp_path)
    before = src.read_bytes()
    variant = tmp_path / "CLICKS.WAV"
    for option in ("--out", "--residual", "--receipt"):
        also = [] if option == "--out" else ["--out", tmp_path / "out.wav"]
        r = run("repair", src, "--chain", "declick()", option, variant, *also)
        if one_file:
            assert r.exit_code == 2 and "source" in r.stdout, f"{option}: {r.stdout}"
        else:
            assert r.exit_code == 0, f"{option}: {r.stdout}"
        assert src.read_bytes() == before, option
    if one_file:
        assert sorted(p.name for p in tmp_path.iterdir()) == ["clicks.wav"]


@needs_core
def test_two_targets_that_differ_only_in_case_are_refused(tmp_path):
    """x.wav and X.WAV are one file on a case-insensitive volume, where two writes would interleave in it. Refused
    on every volume: a name that differs only in case is no way to name a second file."""
    src, *_ = clicked_fixture(tmp_path)
    for option in ("--residual", "--receipt"):
        r = run("repair", src, "--chain", "declick()", "--out", tmp_path / "x.wav", option, tmp_path / "X.WAV")
        assert r.exit_code == 2 and "same file" in flat(r.stdout), f"{option}: {r.stdout}"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["clicks.wav"]


@needs_core
def test_a_clean_file_exits_1_with_nothing_to_change(tmp_path):
    src = tmp_path / "clean.wav"
    sf.write(src, np.column_stack([tone(), tone()]), 48000, subtype="PCM_24")
    r = run("repair", src, "--preset", "declick-declip", "--out", tmp_path / "out.wav")
    assert r.exit_code == 1 and "nothing to change" in r.stdout
    assert not (tmp_path / "out.wav").exists()


@needs_core
def test_peaks_rebuilt_past_full_scale_in_an_integer_copy_get_a_note(tmp_path):
    """Speech pushed 3 dB past full scale and clipped at 0.99: A-SPADE rebuilds peaks above 1, which 24 bits clip."""
    x, fs = sf.read(FIXTURE, dtype="float64")
    src = tmp_path / "hot.wav"
    sf.write(src, np.clip(x * 1.4 / np.max(np.abs(x)), -0.99, 0.99), fs, subtype="PCM_24")
    r = run("repair", src, "--chain", "declip()", "--out", tmp_path / "out.wav")
    assert r.exit_code == 0, r.stdout
    assert "pass full scale" in r.stdout
    out = sf.read(tmp_path / "out.wav")[0]
    assert out.max() == 1 - 2.0**-23 and out.min() == -1.0  # held at the 24-bit rails, never wrapped around


def test_without_the_core_repair_exits_2_with_the_install_route(tmp_path, monkeypatch):
    src = tmp_path / "clean.wav"
    sf.write(src, tone(), 48000, subtype="PCM_24")
    monkeypatch.setattr(cumple.repair, "available", lambda: False)
    r = run("repair", src, "--chain", "declick()", "--out", tmp_path / "out.wav")
    assert r.exit_code == 2
    hint = flat(r.stdout)
    assert "uv tool install" in hint and "[repair]" in hint and "compiles the Rust core" in hint


@needs_core
def test_paths_and_errors_with_brackets_are_printed_intact(tmp_path):
    src, *_ = clicked_fixture(tmp_path)
    take = src.rename(tmp_path / "take[1].wav")
    out = tmp_path / "take[1] fixed.wav"
    r = run("repair", take, "--chain", "declick()", "--out", out)
    assert r.exit_code == 0, r.stdout
    assert str(out) in r.stdout and str(out.with_name(out.name + ".cumple-repair.json")) in r.stdout
    folder = tmp_path / "[bounces]"
    folder.mkdir()
    r = run("repair", take, "--chain", "declick()", "--out", folder)
    assert r.exit_code == 2 and str(folder) in r.stdout


def test_list_presets_names_the_built_ins_and_help_names_the_detector_limits():
    r = run("repair", "--list-presets")
    assert r.exit_code == 0
    for preset in ("declick", "declip", "declick-declip"):
        assert preset in r.stdout.split()
    text = flat(run("repair", "--help").stdout)
    assert "narrow clicks" in text and "digital silence" in text and "nothing to change" in text
