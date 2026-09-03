from __future__ import annotations

import numpy as np
import soundfile as sf
from scipy.signal import iirpeak, lfilter

from cumple.diff import describe, diff_arrays, diff_files, sum_stems_against
from cumple.diff.align import fractional_shift
from tests.test_layout import band_noise

FS = 48000


def stereo_noise(seconds=5.0, seed=1, level=-20.0):
    l = band_noise(seconds, 30, 16000, level, seed)
    r = band_noise(seconds, 30, 16000, level, seed + 100)
    return np.stack([l, r], 1)


def test_identical_files_are_identical(tmp_path):
    a = stereo_noise()
    sf.write(str(tmp_path / "a.wav"), a, FS, subtype="PCM_24")
    sf.write(str(tmp_path / "b.wav"), a, FS, subtype="PCM_24")
    r = diff_files(tmp_path / "a.wav", tmp_path / "b.wav")
    assert r.identical
    assert "identical" in describe(r)


def test_shift_gain_and_polarity_are_recovered_exactly():
    a = stereo_noise()
    b = np.concatenate([np.zeros((23, 2)), a[:-23]]) * 10 ** (-1.5 / 20) * -1
    r = diff_arrays(a, b, FS)
    al = r.alignment
    assert abs(al.offset_samples - 23) < 0.05
    assert abs(al.gain_db + 1.5) < 0.02
    assert al.polarity_inverted
    assert r.residual_dbfs < -80
    text = describe(r)
    assert "-1.5 dB" in text and "23 samples" in text and "late" in text and "polarity inverted" in text


def test_sub_sample_offset_is_found():
    a = stereo_noise()
    b = fractional_shift(a, 10.5)
    r = diff_arrays(a, b, FS)
    assert abs(r.alignment.offset_samples - 10.5) < 0.1
    assert r.residual_dbfs < -60


def test_eq_change_shows_in_band_deltas_not_in_gain():
    a = stereo_noise()
    b_num, b_den = iirpeak(3150, Q=2, fs=FS)
    # +6 dB peak at 3.15 kHz: mix the peaked band back in
    peaked = lfilter(b_num, b_den, a, axis=0)
    b = a + peaked * (10 ** (6 / 20) - 1)
    r = diff_arrays(a, b, FS)
    assert abs(r.alignment.gain_db) < 0.6
    deltas = dict(r.band_deltas)
    assert deltas[3150] > 3.0
    assert abs(deltas[200]) < 0.5
    assert -45 < r.residual_rel_db < -5
    assert "3.15 kHz" in describe(r)


def test_stems_that_sum_null_and_a_half_db_music_change_is_reported(tmp_path):
    dx, mx, fx = (band_noise(4, 100, 8000, -26, s)[:, None] * np.ones((1, 2)) for s in (11, 12, 13))
    pm = dx + mx + fx
    for name, x in [("DX", dx), ("MX", mx), ("FX", fx), ("PM", pm)]:
        sf.write(str(tmp_path / f"{name}.wav"), x, FS, subtype="FLOAT")
    r = sum_stems_against([tmp_path / "DX.wav", tmp_path / "MX.wav", tmp_path / "FX.wav"], tmp_path / "PM.wav")
    assert r.residual_dbfs < -100
    sf.write(str(tmp_path / "MX2.wav"), mx * 10 ** (0.5 / 20), FS, subtype="FLOAT")
    r2 = sum_stems_against([tmp_path / "DX.wav", tmp_path / "MX2.wav", tmp_path / "FX.wav"], tmp_path / "PM.wav")
    assert -56 < r2.residual_dbfs < -45  # the 0.5 dB on one stem is left in, not fitted away
    assert not r2.identical
    assert "stems must match" in describe(r2)
