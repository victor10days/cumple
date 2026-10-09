"""Metrics and synthetic damage with known answers; nothing here needs the Rust core."""

from __future__ import annotations

import numpy as np

from cumple.repair import damage, metrics

FS = 48000


def tone(seconds=120.0, hz=440.0):
    t = np.arange(int(seconds * FS)) / FS
    return 0.5 * np.sin(2 * np.pi * hz * t)


def test_sdr_of_a_perfect_estimate_is_infinite_and_of_half_gain_is_six_db():
    x = tone(2.0)
    assert metrics.sdr_db(x, x) == np.inf
    assert abs(metrics.sdr_db(x, 0.5 * x) - 6.02) < 0.01


def test_clip_to_sdr_lands_within_a_tenth_of_a_db_and_returns_the_mask():
    x = tone(2.0)
    y, thr, mask = damage.clip_to_sdr(x, 5.0)
    assert abs(metrics.sdr_db(x, y) - 5.0) < 0.1
    assert mask.dtype == bool and mask.sum() > 0
    assert np.all(np.abs(y[mask]) == thr) and np.all(y[~mask] == x[~mask])
    assert np.float32(thr) == thr  # the manifest stores the float32 repr so |v| >= thr holds on the stored samples


def test_add_clicks_is_seeded_and_only_touches_the_mask():
    x = tone(120.0)  # two minutes at 40 per minute: 80 clicks
    y1, clicks1, mask1 = damage.add_clicks(x, FS, seed=7, per_minute=40, **damage.IMPULSE)
    y2, clicks2, mask2 = damage.add_clicks(x, FS, seed=7, per_minute=40, **damage.IMPULSE)
    assert clicks1 == clicks2 and np.array_equal(y1, y2)
    assert np.all(y1[~mask1] == x[~mask1]) and len(clicks1) == 80
    assert all(1 <= c.width <= 3 for c in clicks1)


def test_impulse_clicks_are_visible_to_the_local_rms_detector():
    """cathar's detector cannot exceed sqrt(window) = 8 at window 64; the IMPULSE preset must clear threshold 5 at every click's peak."""
    x = tone(10.0)
    y, clicks, _ = damage.add_clicks(x, FS, seed=1, per_minute=60, **damage.IMPULSE)
    ratios = metrics.local_rms_ratio(y, window=64)
    assert all(ratios[c.position] > 5.0 for c in clicks)  # the detector of record runs at threshold 5


def test_a_lone_sample_in_silence_sits_exactly_on_the_bound():
    """The local RMS includes the sample tested, so a single non-zero sample in zeros has ratio sqrt(window): any threshold below 8 fires on it."""
    y = np.zeros(4096)
    y[2048] = 2.0**-15  # one LSB at 16 bits
    assert abs(metrics.local_rms_ratio(y, window=64)[2048] - 8.0) < 1e-12


def test_delta_sdr_on_damaged_samples_only_ignores_the_rest():
    x = tone(2.0)
    y, _, mask = damage.clip_to_sdr(x, 3.0)
    assert metrics.delta_sdr(x, y, x, mask=mask) == np.inf
    assert metrics.delta_sdr(x, y, y, mask=mask) == 0.0


def test_residual_clicks_counts_missed_and_false():
    x = tone(10.0)
    y, clicks, _ = damage.add_clicks(x, FS, seed=1, per_minute=60, **damage.IMPULSE)
    pos, wid = [c.position for c in clicks], [c.width for c in clicks]
    missed, false = metrics.residual_clicks(x, y, pos, wid, threshold=5.0)
    assert missed == len(clicks) and false == 0
    missed, false = metrics.residual_clicks(x, x, pos, wid, threshold=5.0)
    assert missed == 0 and false == 0
