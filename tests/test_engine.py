from __future__ import annotations

import json

import numpy as np
import soundfile as sf
from typer.testing import CliRunner

from cumple.checks import Status, evaluate
from cumple.cli import app
from cumple.meters.measure import measure
from cumple.specs import get

runner = CliRunner()


def tone_file(
    path,
    dbfs=-23.0,
    sr=48000,
    channels=2,
    seconds=8.0,
    subtype="PCM_24",
    freq=1000.0,
    head_silence=0.0,
    tail_silence=0.0,
    invert_right=False,
):
    n = int(sr * seconds)
    t = np.arange(n) / sr
    x = 10 ** (dbfs / 20) * np.sin(2 * np.pi * freq * t)
    m = int(sr * 0.02)
    ramp = 0.5 - 0.5 * np.cos(np.pi * np.arange(m) / m)
    x[:m] *= ramp
    x[-m:] *= ramp[::-1]
    data = np.repeat(x[:, None], channels, axis=1)
    if invert_right and channels == 2:
        data[:, 1] *= -1
    data = np.concatenate(
        [np.zeros((int(sr * head_silence), channels)), data, np.zeros((int(sr * tail_silence), channels))]
    )
    sf.write(str(path), data, sr, subtype=subtype)
    return path


def codes(report, status=None):
    return {f.code: f.status for f in report.findings if status is None or f.status is status}


def test_compliant_stereo_tone_passes_ebu_r128(tmp_path):
    p = tone_file(tmp_path / "ok.wav", dbfs=-23.0)
    r = evaluate(get("ebu-r128"), measure(p))
    assert r.passed, codes(r)
    assert codes(r)["loudness.integrated"] is Status.PASS
    assert codes(r)["peak.true"] is Status.PASS


def test_hot_true_peak_fails_netflix_and_suggests_a_fix(tmp_path):
    # -0.4 dBFS tone: loudness is far too loud for Netflix and the true peak is above -2 dBTP.
    p = tone_file(tmp_path / "hot.wav", dbfs=-0.4)
    r = evaluate(get("netflix-2.0"), measure(p))
    assert not r.passed
    f = {x.code: x for x in r.findings}
    assert f["peak.true"].status is Status.FAIL
    assert "lower by" in f["peak.true"].fix
    assert f["loudness.integrated"].status is Status.FAIL or f["loudness.dialogue_gated"].status is Status.FAIL


def test_gain_only_fix_is_offered_when_headroom_allows(tmp_path):
    p = tone_file(tmp_path / "quiet.wav", dbfs=-30.0)  # -30 LUFS: 7 LU below the R128 target
    r = evaluate(get("ebu-r128"), measure(p))
    f = {x.code: x for x in r.findings}
    assert f["loudness.integrated"].status is Status.FAIL
    assert f["loudness.integrated"].fix.startswith("raise the whole file by 7.0 dB")


def test_wrong_sample_rate_and_depth_fail_format_rules(tmp_path):
    p = tone_file(tmp_path / "cd.wav", dbfs=-23.0, sr=44100, subtype="PCM_16")
    r = evaluate(get("netflix-2.0"), measure(p))
    c = codes(r)
    assert c["format.sample_rate"] is Status.FAIL
    assert c["format.bit_depth"] is Status.FAIL


def test_padding_rules_wbd(tmp_path):
    p = tone_file(tmp_path / "padded.wav", dbfs=-24.0, head_silence=7.0, tail_silence=2.0)
    r = evaluate(get("max-wbd"), measure(p))
    c = codes(r)
    assert c["padding.head"] is Status.FAIL
    assert c["padding.tail"] is Status.FAIL
    ok = tone_file(tmp_path / "fine.wav", dbfs=-24.0, head_silence=1.0, tail_silence=0.1)
    r = evaluate(get("max-wbd"), measure(ok))
    c = codes(r)
    assert c["padding.head"] is Status.PASS and c["padding.tail"] is Status.PASS


def test_either_or_policy_lets_one_measurement_carry(tmp_path):
    p = tone_file(tmp_path / "wbd.wav", dbfs=-24.0)
    r = evaluate(get("max-wbd"), measure(p))
    failed = codes(r, Status.FAIL)
    # WBD wants MBWF/RF64 or MXF; a plain WAV with no bext chunk is rightly not a BWF.
    assert set(failed) == {"format.container"}, failed
    assert codes(r)["loudness.integrated"] is Status.PASS


def test_anti_phase_stereo_is_flagged(tmp_path):
    p = tone_file(tmp_path / "flip.wav", dbfs=-23.0, invert_right=True)
    m = measure(p)
    assert m.phase_correlation < -0.99
    assert m.mono_fold_loudness == -np.inf  # cancels completely
    r = evaluate(get("ebu-r128"), m)
    assert codes(r)["mono.compat"] is Status.WARN


def test_cli_check_exit_codes_and_json(tmp_path):
    good = tone_file(tmp_path / "good.wav", dbfs=-23.0)
    bad = tone_file(tmp_path / "bad.wav", dbfs=-0.4)
    assert runner.invoke(app, ["check", str(good), "--spec", "ebu-r128"]).exit_code == 0
    res = runner.invoke(app, ["check", str(bad), "--spec", "ebu-r128", "--json"])
    assert res.exit_code == 1
    data = json.loads(res.stdout)
    assert data["verdict"] == "FAIL"
    assert any(f["code"] == "peak.true" and f["status"] == "fail" for f in data["findings"])
    assert data["measurement"]["true_peak_dbtp"] > -1.0


def test_package_of_mono_files_is_measured_as_one_deliverable(tmp_path):
    d = tmp_path / "pkg"
    d.mkdir()
    for role in ("L", "R", "C", "LFE", "Ls", "Rs"):
        tone_file(d / f"Show_5.1_{role}.wav", dbfs=-40.0 if role == "LFE" else -30.0, channels=1, seconds=4.0)
    m = measure(d)
    assert m.is_package and m.layout == "5.1" and m.roles == ["L", "R", "C", "LFE", "Ls", "Rs"]
    # five weighted channels at -30 dBFS: L, R, C at 1.0 and Ls, Rs at 1.41; LFE excluded
    expected = -0.691 + 10 * np.log10((3 + 2 * 1.41) * 10 ** (-3.0) / 2) + 0.691
    assert abs(m.loudness.integrated - expected) < 0.15
