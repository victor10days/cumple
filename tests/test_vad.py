"""Silero VAD as the second speech detector: same grid, same dilation, a different mask."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf
from typer.testing import CliRunner

from cumple.checks.engine import evaluate
from cumple.cli import app
from cumple.meters.dialogue import FRAME_S, SpeechDetector, SpeechResult, describe_backend, dilate_mask
from cumple.meters.measure import measure
from cumple.meters.vad import BACKENDS, SileroDetector, VadUnavailable, load_session, model_path
from cumple.report import render_html
from cumple.report.json_out import report_to_dict
from cumple.specs import load_all

FIXTURE = Path(__file__).parent / "fixtures" / "speech-librivox-3s.wav"
MODEL_SHA256 = "1a153a22f4509e292a94e67d6f9b85e8deb25b4988682b7e174c65279d8788e3"
needs_onnx = pytest.mark.skipif(importlib.util.find_spec("onnxruntime") is None, reason="onnxruntime is not installed")
runner = CliRunner()


@pytest.fixture(autouse=True)
def _no_model_override(monkeypatch):
    """A developer's CUMPLE_SILERO_MODEL must not redirect the hash test or the detector tests."""
    monkeypatch.delenv("CUMPLE_SILERO_MODEL", raising=False)


def test_dilate_mask_fills_a_pause_inside_dialogue_and_leaves_an_isolated_frame_alone():
    voiced = np.zeros(200, dtype=bool)
    voiced[50:70] = True
    voiced[75:95] = True  # a 100 ms pause between two phrases
    voiced[150] = True  # one frame on its own
    mask = dilate_mask(voiced)
    assert mask[70:75].all()
    assert mask[50:95].all()
    assert not mask[110:140].any()  # the rule dilates ten frames past a phrase, not forty
    assert mask[150] and not mask[130:149].any()


def test_describe_backend_names_both_and_refuses_others():
    assert describe_backend("heuristic") == "heuristic speech gate"
    assert describe_backend("silero").startswith("Silero VAD v6.2")
    with pytest.raises(ValueError):
        describe_backend("dolby")
    assert BACKENDS == ("heuristic", "silero")


def test_speech_result_defaults_to_the_heuristic_backend():
    r = SpeechResult(FRAME_S, np.zeros(0, bool), np.zeros(0, bool), np.zeros(0), None)
    assert r.backend == "heuristic"


def test_the_bundled_model_is_the_known_file():
    p = model_path()
    assert p.name == "silero_vad.onnx" and p.is_file()
    assert p.stat().st_size == 2327524
    assert hashlib.sha256(p.read_bytes()).hexdigest() == MODEL_SHA256
    assert (p.parent / "SILERO_LICENSE").read_text(encoding="utf-8").startswith("MIT License")


def test_model_path_honours_the_override(monkeypatch, tmp_path):
    monkeypatch.setenv("CUMPLE_SILERO_MODEL", str(tmp_path / "other.onnx"))
    assert model_path() == tmp_path / "other.onnx"


def test_without_onnxruntime_the_error_names_the_extra(monkeypatch):
    monkeypatch.setitem(sys.modules, "onnxruntime", None)  # import raises ImportError
    with pytest.raises(VadUnavailable) as e:
        load_session()
    assert "cumple[vad]" in str(e.value)


@needs_onnx
def test_a_missing_model_file_is_reported_not_swallowed(monkeypatch, tmp_path):
    monkeypatch.setenv("CUMPLE_SILERO_MODEL", str(tmp_path / "missing.onnx"))
    with pytest.raises(VadUnavailable) as e:
        load_session()
    assert "missing.onnx" in str(e.value)


def _feed(det, data: np.ndarray, block: int) -> SpeechResult:
    for i in range(0, len(data), block):
        det.feed(data[i : i + block])
    return det.result()


@needs_onnx
def test_silero_finds_speech_on_the_librivox_excerpt():
    x, fs = sf.read(str(FIXTURE), dtype="float64", always_2d=True)
    assert fs == 16000 and x.shape[1] == 1
    r = _feed(SileroDetector(fs, 1), x, 4096)
    assert r.backend == "silero"
    assert r.fraction is not None and r.fraction > 0.6
    assert len(r.mask) == len(r.level_db) == int(len(x) / fs / FRAME_S)


@needs_onnx
def test_silero_reads_no_speech_on_white_noise_at_48k():
    rng = np.random.default_rng(1)
    x = (0.05 * rng.standard_normal((48000 * 3, 2))).astype(np.float64)
    r = _feed(SileroDetector(48000, 2), x, 8192)
    assert r.fraction is not None and r.fraction < 0.05
    assert len(r.mask) == int(3 / FRAME_S)


@needs_onnx
def test_chunked_resampling_gives_the_unchunked_decisions(monkeypatch):
    """Three 10 s chunks with the carried tail must decide like one resample of the whole signal.

    The signal is 3 s of speech then 1 s of silence, seven times over, so the mask has fourteen
    edges that a shifted or repeated resampler tail would move; a fixture without pauses is all
    speech after dilation whatever the resampler does, and could not fail.
    """
    from scipy.signal import resample_poly

    import cumple.meters.vad as mod

    x16, fs = sf.read(str(FIXTURE), dtype="float64", always_2d=True)
    assert fs == 16000 and len(x16) == 3 * fs
    x16 = np.concatenate([x16[:, 0], np.zeros(fs)])  # 3 s of speech, 1 s of silence
    x441 = resample_poly(np.tile(x16, 7), 441, 160)[:, None]  # 28 s at 44.1 kHz
    chunked = _feed(SileroDetector(44100, 1), x441, 1024).mask  # CHUNK_S 10: three resample calls, the tail path runs
    monkeypatch.setattr(mod, "CHUNK_S", 1000.0)  # one resample of everything at result(): the reference
    whole = _feed(SileroDetector(44100, 1), x441, 1024).mask
    assert len(chunked) == len(whole) == int(28 / FRAME_S)
    assert chunked.any() and not chunked.all()  # the mask has edges to move
    assert (
        int((chunked != whole).sum()) <= 2
    )  # a tail resampled twice or skipped twice shifts every later window: 33 to 35 frames differ


@needs_onnx
def test_silero_uses_the_centre_channel_when_there_is_one():
    x16, _ = sf.read(str(FIXTURE), dtype="float64", always_2d=True)
    rng = np.random.default_rng(2)
    noise = 0.05 * rng.standard_normal((len(x16), 6))
    six = noise.copy()
    six[:, 2] = x16[:, 0]  # speech on C only, roles L R C LFE Ls Rs
    r = _feed(SileroDetector(16000, 6, roles=["L", "R", "C", "LFE", "Ls", "Rs"]), six, 4096)
    assert r.fraction is not None and r.fraction > 0.6


@needs_onnx
def test_silero_on_a_signal_shorter_than_one_window_reports_no_fraction():
    """Shorter than the model's 32 ms window: the share is unknown, not zero, like the heuristic."""
    rng = np.random.default_rng(3)
    x = (0.05 * rng.standard_normal((int(16000 * 0.025), 1))).astype(np.float64)
    r = _feed(SileroDetector(16000, 1), x, 4096)
    assert r.fraction is None
    assert len(r.mask) == 1


def test_the_heuristic_still_uses_dilate_mask(monkeypatch):
    """The refactor must leave the heuristic's result on the shared rule."""
    called = {"n": 0}
    import cumple.meters.dialogue as mod

    real = mod.dilate_mask

    def spy(v):
        called["n"] += 1
        return real(v)

    monkeypatch.setattr(mod, "dilate_mask", spy)
    x, fs = sf.read(str(FIXTURE), dtype="float64", always_2d=True)
    _feed(SpeechDetector(fs, 1), x, 4096)
    assert called["n"] == 1


@pytest.fixture
def speech_wav(tmp_path):
    """The excerpt as a 48 kHz stereo WAV, eight seconds long, so the meters have enough programme."""
    from scipy.signal import resample_poly

    x16, _ = sf.read(str(FIXTURE), dtype="float64", always_2d=True)
    x48 = resample_poly(x16[:, 0], 3, 1)
    x48 = np.tile(x48, 3)[: 48000 * 8]
    path = tmp_path / "speech.wav"
    sf.write(str(path), np.repeat(x48[:, None], 2, axis=1), 48000, subtype="PCM_24")
    return path


def test_measure_defaults_to_the_heuristic_and_refuses_an_unknown_backend(speech_wav):
    m = measure(speech_wav)
    assert m.speech is not None and m.speech.backend == "heuristic"
    with pytest.raises(ValueError, match="heuristic, silero"):
        measure(speech_wav, vad="dolby")


@needs_onnx
def test_measure_with_silero_reports_the_backend_everywhere(speech_wav):
    profiles = load_all()
    m = measure(speech_wav, vad="silero")
    assert m.speech is not None and m.speech.backend == "silero"
    report = evaluate(profiles["netflix-2.0"], m)
    doc = report_to_dict(report)
    assert doc["measurement"]["speech_backend"] == "silero"
    notes = " ".join(f.note or "" for f in report.findings)
    assert "Silero VAD v6.2" in notes and "heuristic" not in notes
    html = render_html(report)
    assert "Silero VAD v6.2" in html and "heuristic speech" not in html


def test_the_heuristic_report_still_says_heuristic(speech_wav):
    profiles = load_all()
    report = evaluate(profiles["netflix-2.0"], measure(speech_wav))
    notes = " ".join(f.note or "" for f in report.findings)
    assert "heuristic speech gate" in notes and "Silero" not in notes
    assert report_to_dict(report)["measurement"]["speech_backend"] == "heuristic"
    assert "heuristic speech gate" in render_html(report)


@needs_onnx
def test_check_takes_vad_from_the_flag_and_from_the_environment(speech_wav, monkeypatch):
    result = runner.invoke(app, ["check", str(speech_wav), "--spec", "netflix-2.0", "--vad", "silero", "--json"])
    assert result.exit_code in (0, 1), result.output
    assert json.loads(result.output)["measurement"]["speech_backend"] == "silero"
    monkeypatch.setenv("CUMPLE_VAD", "silero")
    result = runner.invoke(app, ["check", str(speech_wav), "--spec", "netflix-2.0", "--json"])
    assert json.loads(result.output)["measurement"]["speech_backend"] == "silero"
    monkeypatch.delenv("CUMPLE_VAD")
    result = runner.invoke(app, ["check", str(speech_wav), "--spec", "netflix-2.0", "--json"])
    assert json.loads(result.output)["measurement"]["speech_backend"] == "heuristic"


def test_check_without_onnxruntime_exits_two_and_names_the_extra(speech_wav, monkeypatch):
    import cumple.meters.vad as vad_mod

    def refuse():
        raise VadUnavailable(
            'the silero backend needs onnxruntime: uv tool install "cumple[vad] @ git+https://github.com/victor10days/cumple"'
        )

    monkeypatch.setattr(vad_mod, "load_session", refuse)
    result = runner.invoke(app, ["check", str(speech_wav), "--spec", "netflix-2.0", "--vad", "silero"])
    assert result.exit_code == 2
    assert "cumple[vad]" in result.output


def test_check_refuses_an_unknown_vad_name(speech_wav):
    result = runner.invoke(app, ["check", str(speech_wav), "--spec", "netflix-2.0", "--vad", "dolby"])
    assert result.exit_code == 2 and "heuristic" in result.output and "silero" in result.output
