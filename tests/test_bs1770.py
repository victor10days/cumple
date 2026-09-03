"""Synthetic signals whose loudness is known from the standard itself."""

from __future__ import annotations

import numpy as np
import pytest

from cumple.meters import LoudnessMeter, channel_weights, k_weighting
from cumple.meters.bs1770 import BS1770_48K_HIGHPASS, BS1770_48K_SHELF


def sine(fs: int, seconds: float, freq: float, dbfs: float, phase: float = 0.0) -> np.ndarray:
    n = int(round(fs * seconds))
    t = np.arange(n) / fs
    return 10 ** (dbfs / 20) * np.sin(2 * np.pi * freq * t + phase)


def measure(x: np.ndarray, fs: int = 48000, block: int | None = None, **kw):
    m = LoudnessMeter(fs, x.shape[1], **kw)
    if block is None:
        m.feed(x)
    else:
        for i in range(0, len(x), block):
            m.feed(x[i : i + block])
    return m.result()


def test_k_weighting_matches_the_printed_48k_coefficients():
    (b1, a1), (b2, a2) = k_weighting(48000)
    assert b1 == pytest.approx([BS1770_48K_SHELF["b0"], BS1770_48K_SHELF["b1"], BS1770_48K_SHELF["b2"]], abs=1e-7)
    assert a1[1:] == pytest.approx([BS1770_48K_SHELF["a1"], BS1770_48K_SHELF["a2"]], abs=1e-7)
    assert b2 == pytest.approx(
        [BS1770_48K_HIGHPASS["b0"], BS1770_48K_HIGHPASS["b1"], BS1770_48K_HIGHPASS["b2"]], abs=1e-7
    )
    assert a2[1:] == pytest.approx([BS1770_48K_HIGHPASS["a1"], BS1770_48K_HIGHPASS["a2"]], abs=1e-7)


def test_full_scale_997hz_on_one_channel_reads_minus_3_01():
    # BS.1770-5 states this figure outright.
    x = np.zeros((48000 * 5, 2))
    x[:, 0] = sine(48000, 5, 997, 0.0)
    r = measure(x)
    assert r.integrated == pytest.approx(-3.01, abs=0.05)
    assert r.momentary_max == pytest.approx(-3.01, abs=0.05)
    assert r.short_term_max == pytest.approx(-3.01, abs=0.05)


@pytest.mark.parametrize("fs", [44100, 48000, 96000])
def test_minus_23_stereo_tone_reads_minus_23_at_any_rate(fs):
    # EBU Tech 3341 case 1 in synthetic form: 1 kHz stereo at -23 dBFS reads -23.0 M/S/I.
    x = np.repeat(sine(fs, 20, 1000, -23.0)[:, None], 2, axis=1)
    r = measure(x, fs=fs)
    for v in (r.integrated, r.momentary_max, r.short_term_max):
        assert v == pytest.approx(-23.0, abs=0.1)


def test_absolute_gate_ignores_digital_silence():
    x = np.repeat(sine(48000, 20, 1000, -23.0)[:, None], 2, axis=1)
    x = np.concatenate([x, np.zeros((48000 * 20, 2))])
    r = measure(x)
    assert r.integrated == pytest.approx(-23.0, abs=0.1)
    assert r.blocks_gated < r.blocks_total


def test_relative_gate_drops_quiet_passages_and_bs1770_1_does_not():
    loud = np.repeat(sine(48000, 20, 1000, -23.0)[:, None], 2, axis=1)
    quiet = np.repeat(sine(48000, 20, 1000, -43.0)[:, None], 2, axis=1)
    x = np.concatenate([loud, quiet])
    gated = measure(x, relative_gate=True)
    ungated = measure(x, relative_gate=False)
    assert gated.integrated == pytest.approx(-23.0, abs=0.1)
    # Without the relative gate the -43 passage counts: mean energy of the two halves.
    expected = -0.691 + 10 * np.log10((10 ** (-2.3) + 10 ** (-4.3)) / 2) + 0.691
    assert ungated.integrated == pytest.approx(expected, abs=0.15)
    assert ungated.integrated < gated.integrated - 2.5


def test_streaming_in_odd_blocks_gives_identical_results():
    rng = np.random.default_rng(7)
    x = rng.normal(0, 0.05, size=(48000 * 12, 2))
    a = measure(x)
    b = measure(x, block=6151)
    assert a.integrated == pytest.approx(b.integrated, abs=1e-7)
    assert a.lra == pytest.approx(b.lra, abs=1e-7)
    np.testing.assert_allclose(a.momentary, b.momentary, atol=1e-9)


def test_surround_weight_is_plus_1_5_db_and_lfe_is_excluded():
    base = sine(48000, 5, 1000, -23.0)
    left = np.zeros((len(base), 6))
    left[:, 0] = base
    ls = np.zeros((len(base), 6))
    ls[:, 4] = base
    lfe = np.zeros((len(base), 6))
    lfe[:, 3] = base
    l_val = measure(left).integrated
    assert measure(ls).integrated == pytest.approx(l_val + 10 * np.log10(1.41), abs=0.02)
    assert measure(lfe).integrated == -np.inf
    assert list(channel_weights(6)) == [1.0, 1.0, 1.0, 0.0, 1.41, 1.41]


def test_loudness_range_of_two_level_signal_is_their_difference():
    # Tech 3342 style: 20 s at -23 then 20 s at -33 gives an LRA of about 10 LU.
    x = np.concatenate(
        [
            np.repeat(sine(48000, 20, 1000, -23.0)[:, None], 2, axis=1),
            np.repeat(sine(48000, 20, 1000, -33.0)[:, None], 2, axis=1),
        ]
    )
    r = measure(x)
    assert r.lra == pytest.approx(10.0, abs=1.0)
    steady = np.repeat(sine(48000, 20, 1000, -23.0)[:, None], 2, axis=1)
    assert measure(steady).lra == pytest.approx(0.0, abs=0.1)


def test_timelines_have_the_right_length_and_times():
    x = np.repeat(sine(48000, 10, 1000, -23.0)[:, None], 2, axis=1)
    r = measure(x)
    assert len(r.momentary) == 100 - 4 + 1
    assert len(r.short_term) == 100 - 30 + 1
    assert r.momentary_times()[0] == pytest.approx(0.4)
    assert r.short_term_times()[0] == pytest.approx(3.0)
    assert r.duration_s == pytest.approx(10.0)
