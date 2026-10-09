"""ffmpeg and cathar as subprocess baselines: when they are on the machine, they repair; when not, nothing here runs."""

from pathlib import Path

import numpy as np
import pytest
import soundfile as sf
from scripts.benchmark_repair import find_cathar, run_cathar, run_ffmpeg

from cumple.io.ffmpeg import find_ffmpeg
from cumple.repair import damage, metrics

TOOLS = find_ffmpeg()
CATHAR = find_cathar()
needs_ffmpeg = pytest.mark.skipif(TOOLS is None, reason="ffmpeg is not on PATH")
needs_cathar = pytest.mark.skipif(CATHAR is None, reason="cathar is not on PATH and CUMPLE_CATHAR is unset")
FIXTURE = Path(__file__).parent / "fixtures" / "speech-librivox-3s.wav"


@pytest.fixture
def clipped(tmp_path):
    x, fs = sf.read(FIXTURE, dtype="float64")
    y, thr, mask = damage.clip_to_sdr(x, 5.0)  # lands near 0.036, 16 dB under the fixture's own peak
    p = tmp_path / "clipped.wav"
    sf.write(p, y, fs, subtype="FLOAT")
    return p, x, y, thr, mask


@needs_ffmpeg
def test_ffmpeg_adeclip_improves_sdr_on_a_clipped_voice(clipped, tmp_path):
    p, x, y, thr, mask = clipped
    est, _ = sf.read(run_ffmpeg(TOOLS, p, tmp_path / "out.wav", "adeclip"), dtype="float64")
    assert metrics.delta_sdr(x, y, est) > 0.5  # 03c measured +2.57 dB with ffmpeg 6.1.1 at defaults


@needs_cathar
def test_cathar_declip_improves_sdr_at_the_manifest_threshold(clipped, tmp_path):
    p, x, y, thr, mask = clipped
    est, _ = sf.read(run_cathar(CATHAR, p, tmp_path / "out.wav", "declip", threshold=thr), dtype="float64")
    assert (
        metrics.delta_sdr(x, y, est) > 0.5
    )  # 03c measured +7.71 dB; at cathar's default 0.95 it is exactly 0, which this test must never be allowed to pass
    assert np.array_equal(est[~mask], y[~mask])  # A-SPADE returns every unclipped sample unchanged
