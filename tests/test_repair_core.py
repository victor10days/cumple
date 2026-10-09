"""The compiled core (cumple_dsp) against independent references; skips when the core is not built."""

from __future__ import annotations

import importlib.util

import numpy as np
import pytest

needs_core = pytest.mark.skipif(
    importlib.util.find_spec("cumple_dsp") is None, reason="cumple-dsp is not built; uv sync --extra repair"
)


@needs_core
def test_stft_matches_scipy_within_tolerance():
    import cumple_dsp
    from scipy.signal import ShortTimeFFT
    from scipy.signal.windows import hann

    fs, n_fft, hop = 48000, 1024, 256
    rng = np.random.default_rng(0)
    x = rng.standard_normal(fs) * 0.1
    ours = cumple_dsp.Stft(n_fft, hop).analyze(x)  # (frames, bins), frame j covers samples j*hop .. j*hop + n_fft - 1
    assert ours.shape == ((fs - n_fft) // hop + 1, n_fft // 2 + 1) and ours.dtype == np.complex128
    # phase_shift=None: scipy's default references each slice's phase to its centre and flips every odd bin against a plain windowed FFT
    sft = ShortTimeFFT(hann(n_fft, sym=False), hop=hop, fs=fs, fft_mode="onesided", phase_shift=None)
    assert sft.p_min == -1, "scipy's first slice index changed; recompute the offset"
    # scipy slice p is centred at p*hop; the slice centred at n_fft//2 = 512 is p = 2, which is column p - p_min = 3
    first = (n_fft // 2) // hop - sft.p_min
    theirs = sft.stft(x)  # (bins, columns)
    common = min(ours.shape[0], theirs.shape[1] - first)
    assert common == ours.shape[0], "every one of our frames has a scipy column to meet"
    np.testing.assert_allclose(ours[:common].T, theirs[:, first : first + common], atol=1e-9, rtol=0)
