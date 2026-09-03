from __future__ import annotations

import numpy as np
import pytest

from cumple.meters import PeakMeter
from cumple.meters.truepeak import BS1770_PHASES, designed_phases


def test_itu_table_is_a_sane_interpolator():
    # Symmetric FIR: phase 0 mirrors phase 3, phase 1 mirrors phase 2; each phase passes DC near unity.
    np.testing.assert_allclose(BS1770_PHASES[0], BS1770_PHASES[3][::-1])
    np.testing.assert_allclose(BS1770_PHASES[1], BS1770_PHASES[2][::-1])
    sums = BS1770_PHASES.sum(axis=1)
    assert np.all(np.abs(sums - 1.0) < 0.04), sums


def tone(freq: float, fs: int = 48000, seconds: float = 1.0, phase: float = 0.0, fade_s: float = 0.05) -> np.ndarray:
    """A full-scale sine with raised-cosine fades. A tone that starts abruptly at full scale has a
    real inter-sample overshoot at its onset, which is not what these tests are about."""
    n = int(fs * seconds)
    t = np.arange(n) / fs
    x = np.sin(2 * np.pi * freq * t + phase)
    m = int(fs * fade_s)
    ramp = 0.5 - 0.5 * np.cos(np.pi * np.arange(m) / m)
    x[:m] *= ramp
    x[-m:] *= ramp[::-1]
    return x[:, None]


def run(x: np.ndarray, fs: int = 48000, block: int | None = None, **kw):
    m = PeakMeter(fs, x.shape[1], **kw)
    if block is None:
        m.feed(x)
    else:
        for i in range(0, len(x), block):
            m.feed(x[i : i + block])
    return m.result()


def test_quarter_rate_sine_at_45_degrees_hides_its_peak_between_samples():
    fs = 48000
    x = tone(fs / 4, phase=np.pi / 4)
    r = run(x)
    assert r.sample_peak_dbfs == pytest.approx(-3.01, abs=0.01)
    assert -0.4 <= r.true_peak_dbtp <= 0.2  # the standard's own tolerance for the filter


@pytest.mark.parametrize("freq", [500, 1000, 1500, 2000])
def test_low_frequency_tones_read_their_true_level(freq):
    # Shaped like EBU Tech 3341 cases 15 to 18: full-scale tones must read 0 dBTP (+0.2/-0.4).
    x = tone(freq, phase=np.pi / 4)
    r = run(x)
    assert -0.4 <= r.true_peak_dbtp <= 0.2


def test_samples_at_full_scale_can_hide_a_plus_3_db_true_peak():
    # Shaped like EBU Tech 3341 case 19: a quarter-rate sine whose samples touch 0 dBFS at 45 degrees
    # peaks at +3.01 dBTP between them.
    fs = 48000
    x = tone(fs / 4, phase=np.pi / 4)
    x = x / np.abs(x).max()
    r = run(x)
    assert r.sample_peak_dbfs == pytest.approx(0.0, abs=0.01)
    assert 3.01 - 0.4 <= r.true_peak_dbtp <= 3.01 + 0.2


def test_8_khz_tone_reads_its_level_once_faded():
    # Samples of an fs/6 tone fall at 0, 60 and 120 degrees, so the sample peak is -1.25 dBFS
    # while the waveform reaches 0 dBTP. The reference filter's small passband droop at 8 kHz
    # keeps the reading inside the standard's +0.2/-0.4 window.
    fs = 48000
    x = tone(fs / 6)
    r = run(x)
    assert r.sample_peak_dbfs == pytest.approx(20 * np.log10(np.sin(np.pi / 3)), abs=0.01)
    assert -0.4 <= r.true_peak_dbtp <= 0.2


def test_an_abrupt_onset_has_a_real_inter_sample_overshoot():
    # No fade: the tone starts at full scale on sample 1. The band-limited waveform that passes
    # through those samples overshoots at the onset, and the meter must report it.
    fs = 48000
    t = np.arange(fs) / fs
    x = np.sin(2 * np.pi * 8000 * t)[:, None]
    r = run(x)
    assert r.true_peak_dbtp > 0.15
    assert run(tone(8000)).true_peak_dbtp < r.true_peak_dbtp


def test_true_peak_never_reads_below_sample_peak_by_much():
    rng = np.random.default_rng(3)
    x = np.clip(rng.normal(0, 0.2, size=(48000 * 3, 2)), -0.9, 0.9)
    r = run(x)
    assert r.true_peak_dbtp >= r.sample_peak_dbfs - 0.05
    assert r.true_peak_per_channel.shape == (2,)


def test_itu_table_and_independent_design_agree():
    rng = np.random.default_rng(11)
    x = sum(0.2 * tone(f, phase=rng.uniform(0, 2 * np.pi)) for f in (997, 5000, 11000, 17000))
    a = run(x).true_peak_dbtp
    b = run(x, phases=designed_phases()).true_peak_dbtp
    assert a == pytest.approx(b, abs=0.15)


def test_streaming_in_odd_blocks_gives_identical_peaks():
    rng = np.random.default_rng(5)
    x = rng.normal(0, 0.1, size=(48000 * 2, 2))
    assert run(x).true_peak_dbtp == pytest.approx(run(x, block=3331).true_peak_dbtp, abs=1e-12)


def test_clipping_runs_are_counted_across_block_boundaries():
    x = np.zeros((10000, 1))
    x[1000:1010, 0] = 1.0  # one run of 10 full-scale samples
    x[5000:5002, 0] = 1.0  # two samples: not a run
    assert run(x).clipped_runs == 1
    assert run(x, block=1005).clipped_runs == 1  # the run straddles a block boundary
