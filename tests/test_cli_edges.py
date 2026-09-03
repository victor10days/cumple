"""Every command, every error path, and the awkward files."""

from __future__ import annotations

import json

import numpy as np
import pytest
import soundfile as sf
from typer.testing import CliRunner

from cumple.checks import Status, evaluate
from cumple.cli import app
from cumple.meters.measure import measure
from cumple.specs import load_all
from tests.test_dialogue_leqm_acx import music_like, speech_like, stereo
from tests.test_engine import tone_file

runner = CliRunner()
FS = 48000


def run(*args):
    return runner.invoke(app, [str(a) for a in args])


def test_specs_variants():
    assert "destinations" in run("specs").stdout
    assert "ebu-r128" in run("specs", "--ids").stdout.splitlines()
    rows = json.loads(run("specs", "--json").stdout)
    assert {"id", "grade", "loudness"} <= set(rows[0])
    md = run("specs", "--markdown").stdout
    assert md.startswith("# Destinations") and "| `netflix-2.0` |" in md
    assert run("specs", "--family", "cinema").stdout.count("Leq(m)") >= 2


def test_explain_and_unknown_profile():
    assert run("explain", "tasa-trailer").exit_code == 0
    r = run("explain", "netflx")
    assert r.exit_code == 2 and "Did you mean" in r.stdout and "netflix" in r.stdout


def test_version():
    r = run("--version")
    assert r.exit_code == 0 and "cumple" in r.stdout


def test_info_on_file_and_package(tmp_path):
    f = tone_file(tmp_path / "t.wav", seconds=1)
    assert "PCM_24" in run("info", f).stdout
    d = tmp_path / "pkg"
    d.mkdir()
    for role in ("L", "R"):
        tone_file(d / f"x_{role}.wav", channels=1, seconds=1)
    assert "stereo" in run("info", d).stdout


def test_unreadable_file_is_reported_not_a_traceback(tmp_path):
    bad = tmp_path / "garbage.wav"
    bad.write_bytes(b"RIFF" + b"\x00" * 100)
    for args in (
        ["check", bad, "--spec", "ebu-r128"],
        ["info", bad],
        ["diff", bad, bad],
        ["fix", bad, "--spec", "ebu-r128"],
    ):
        r = run(*args)
        assert r.exit_code == 2, args
        assert "cannot" in r.stdout and "Traceback" not in r.stdout


def test_diff_argument_errors(tmp_path):
    a = tone_file(tmp_path / "a.wav", seconds=2)
    b = tone_file(tmp_path / "b.wav", seconds=2, sr=44100)
    c = tone_file(tmp_path / "c.wav", seconds=2)
    r = run("diff", a, b)
    assert r.exit_code == 2 and "sample rates differ" in r.stdout
    r = run("diff", a, c, tmp_path / "a.wav")
    assert r.exit_code == 2 and "exactly two" in r.stdout


def test_package_with_mixed_rates_is_refused(tmp_path):
    d = tmp_path / "pkg"
    d.mkdir()
    tone_file(d / "x_L.wav", channels=1, seconds=1)
    tone_file(d / "x_R.wav", channels=1, seconds=1, sr=44100)
    r = run("check", d, "--spec", "amazon-5.1-package")
    assert r.exit_code == 2 and "not consistent" in r.stdout


def test_watch_once_reports_a_broken_file_and_continues(tmp_path):
    folder = tmp_path / "in"
    folder.mkdir()
    (folder / "broken.wav").write_bytes(b"RIFF" + b"\x00" * 64)
    tone_file(folder / "fine.wav", dbfs=-23.0, seconds=2)
    r = run("watch", folder, "--spec", "ebu-r128", "--once", "--stable", "0", "--interval", "0")
    assert r.exit_code == 0
    assert "could not measure broken.wav" in r.stdout and "PASS fine.wav" in r.stdout
    assert (folder / "fine.qc.html").exists() and not (folder / "broken.qc.html").exists()


def test_fix_refuses_and_exits_1(tmp_path):
    sr = FS
    t = np.arange(sr * 8) / sr
    x = 0.02 * np.sin(2 * np.pi * 1000 * t)
    x[sr : sr + 480] = 0.99
    sf.write(str(tmp_path / "spiky.wav"), np.repeat(x[:, None], 2, axis=1), sr, subtype="PCM_24")
    r = run("fix", tmp_path / "spiky.wav", "--spec", "ebu-r128")
    assert r.exit_code == 1 and "no fix written" in r.stdout


def test_digital_silence_does_not_crash(tmp_path):
    p = tmp_path / "silence.wav"
    sf.write(str(p), np.zeros((FS * 4, 2)), FS, subtype="PCM_24")
    m = measure(p)
    assert m.loudness.integrated == -np.inf
    r = run("check", p, "--spec", "ebu-r128", "--sheet", "--out", tmp_path / "out")
    assert r.exit_code == 1 and "silence" in r.stdout
    assert (tmp_path / "out" / "silence.qc.html").exists()


def test_one_second_file_has_no_short_term_window(tmp_path):
    p = tone_file(tmp_path / "short.wav", seconds=1.0)
    m = measure(p)
    assert m.loudness.short_term.size == 0 and m.loudness.short_term_max == -np.inf
    assert run("check", p, "--spec", "ebu-r128", "--sheet", "--out", tmp_path / "o").exit_code in (0, 1)


@pytest.mark.parametrize("kind", ["mono", "44k", "96k", "float", "aiff", "flac"])
def test_awkward_files_measure_and_evaluate(tmp_path, kind):
    sr = {"44k": 44100, "96k": 96000}.get(kind, FS)
    subtype = {"float": "FLOAT", "flac": "PCM_24", "aiff": "PCM_24"}.get(kind, "PCM_24")
    ext = {"aiff": "aiff", "flac": "flac"}.get(kind, "wav")
    channels = 1 if kind == "mono" else 2
    p = tone_file(tmp_path / f"f.{ext}", dbfs=-23.0, sr=sr, channels=channels, subtype=subtype, seconds=4)
    m = measure(p)
    assert abs(m.loudness.integrated - (-23.0 - (3.01 if channels == 1 else 0))) < 0.2
    r = evaluate(load_all()["ebu-r128"], m)
    codes = {f.code: f for f in r.findings}
    if kind == "float":
        assert codes["format.bit_depth"].status is Status.FAIL and "float" in codes["format.bit_depth"].measured
    if kind in ("44k", "96k"):
        assert codes["format.sample_rate"].status is Status.FAIL


def test_every_profile_evaluates_a_real_programme_without_error(tmp_path):
    x = np.concatenate(
        [
            stereo(speech_like(8, -30)),
            np.zeros((FS * 2, 2)),
            stereo(music_like(8, -22)),
            stereo(speech_like(6, -30, seed=7)),
        ]
    )
    p = tmp_path / "programme.wav"
    sf.write(str(p), x, FS, subtype="PCM_24")
    m = measure(p, leqm=True)
    known = {
        "loudness.speech",
        "loudness.integrated",
        "loudness.dialogue_gated",
        "loudness.fallback",
        "peak.true",
        "peak.sample",
        "peak.clipping",
        "dynamics.lra",
        "dynamics.short_term_max",
        "format.sample_rate",
        "format.bit_depth",
        "format.channels",
        "format.layout",
        "format.packaging",
        "format.container",
        "format.lfe_band",
        "format.channel_order",
        "padding.head",
        "padding.tail",
        "padding.head_min",
        "padding.tail_min",
        "signal.dc_offset",
        "signal.silent_channels",
        "mono.compat",
        "metadata.bext_loudness",
        "leqm.level",
        "rms.level",
        "rms.noise_floor",
        "duration.max",
    }
    for profile in load_all().values():
        report = evaluate(profile, m)
        assert report.findings, profile.id
        unknown = {f.code for f in report.findings} - known
        assert not unknown, (profile.id, unknown)
        for f in report.findings:
            assert f.status in Status and f.measured and f.limit, (profile.id, f.code)
