"""De-click: the port matches upstream cathar whole-file within tolerance, chunking costs what it costs, and nothing outside the clicks moves."""

from __future__ import annotations

import numpy as np
import pytest
import soundfile as sf
from scripts.benchmark_repair import find_cathar, run_cathar

from cumple.repair import damage, metrics
from tests.repair_helpers import cathar_gaps, cathar_local_rms, chunked, gap_mask
from tests.test_repair_baselines import FIXTURE, needs_cathar
from tests.test_repair_core import needs_core

CATHAR = find_cathar()
# The first seed from 1 up on which the f32 and f64 builds detect different gaps. On seed 1 the f32 build
# lists 70 gaps and the f64 build 10; the first that only f32 finds is (22547, 17). After the click at 22186
# the float32 running sum has drifted, so sample 22555 (-1.5e-4) has a local RMS of 2.0e-5 in float32 and
# 1.2e-4 in float64: a ratio of 7.7 against 1.2. Seeds 3, 5 and 6 agree, so the f64 mutation passes there.
PRECISION_SEED = 1


def clicked(seed=3):
    x, fs = sf.read(FIXTURE, dtype="float64")
    y, clicks, mask = damage.add_clicks(x, fs, seed=seed, per_minute=200, **damage.IMPULSE)  # about ten clicks in 3 s
    return x, y, clicks, mask, fs


def test_cathar_gaps_gives_a_lone_lsb_in_digital_silence_its_17_sample_gap():
    """A lone sample in zeros has ratio sqrt(64) = 8 to its own RMS: a 1-sample run, padded by 8 on each side."""
    y = np.zeros(4096)
    y[2048] = 2.0**-15
    assert cathar_gaps(y, threshold=5.0, window=64) == [(2040, 17)]


def test_cathar_gaps_puts_two_close_clicks_in_one_gap():
    """The second click lies in the first one's shoulder and in the jump past it, so one gap covers both."""
    y = 0.01 * np.sin(2 * np.pi * 440 * np.arange(4096) / 16000)
    y[1004] += 0.5
    assert cathar_gaps(y, threshold=5.0, window=64) == [(996, 17)]  # alone, the second click has its own gap
    y[1000] += 0.5
    assert cathar_gaps(y, threshold=5.0, window=64) == [(992, 17)]


def test_cathar_local_rms_is_the_float32_running_sum_step_for_step():
    """The vectorised cumsum equals a scalar float32 loop in restore.rs's order bit for bit, drift included."""
    rng = np.random.default_rng(0)
    y = np.concatenate([0.9 * np.sign(rng.standard_normal(64)), 1e-5 * rng.standard_normal(600)]).astype(np.float32)
    half, n = 32, len(y)
    s, count = np.float32(0.0), 0
    for v in y[:half]:
        s, count = np.float32(s + v * v), count + 1
    want = np.empty(n, dtype=np.float32)
    for i in range(n):
        if i >= half:
            s, count = np.float32(s - y[i - half] * y[i - half]), count - 1
        if i + half < n:
            s, count = np.float32(s + y[i + half] * y[i + half]), count + 1
        with np.errstate(invalid="ignore"):
            r = np.sqrt(np.float32(s / np.float32(count)))
        want[i] = r if r >= np.float32(1e-10) else np.float32(1e-10)  # NaN takes the floor, as f32::max gives it
    got = cathar_local_rms(y, 64)
    assert got.view(np.uint32).tolist() == want.view(np.uint32).tolist()
    true = metrics.local_rms(y.astype(np.float64), 64)
    assert np.max(np.abs(got[200:] / true[200:] - 1.0)) > 0.5  # the drift is real here, so the test pins it


@needs_core
def test_declick_removes_injected_clicks_and_touches_only_its_own_gaps():
    import cumple_dsp

    x, y, clicks, mask, fs = clicked()
    assert all(metrics.local_rms_ratio(y)[c.position] > 5.0 for c in clicks), "setup: a click the detector cannot see"
    m = cumple_dsp.Declick(fs)
    est = m.process_whole(y)
    assert not np.array_equal(est, y)  # spec rule 0
    missed, false = metrics.residual_clicks(
        x, est, [c.position for c in clicks], [c.width for c in clicks], threshold=5.0
    )
    assert missed <= len(clicks) // 10
    report = m.report()
    # spec rule 3: the module's own gaps
    gaps = damage.dilate(gap_mask(len(y), report["positions"], report["widths"]), 8)
    np.testing.assert_allclose(est[~gaps], y[~gaps], atol=1e-9)
    assert metrics.delta_sdr(x, y, est) > 3.0
    assert report["clicks"] >= len(clicks) * 0.9


@needs_core
def test_declick_rejects_a_threshold_the_detector_cannot_reach():
    import cumple_dsp

    with pytest.raises(ValueError, match="sqrt"):
        cumple_dsp.Declick(48000, threshold=8.0, window=64)


@needs_core
@needs_cathar
def test_declick_matches_upstream_cathar_whole_file(tmp_path):
    """Seed 3, and PRECISION_SEED, where an f32 build whose local RMS ran in f64 would list other gaps."""
    import cumple_dsp

    for seed in (3, PRECISION_SEED):
        x, y, clicks, mask, fs = clicked(seed)
        p = tmp_path / f"clicks{seed}.wav"
        sf.write(p, y, fs, subtype="FLOAT")
        # the stored float32 values cathar reads; clicks are not float32-exact before this
        y, _ = sf.read(p, dtype="float64")
        up, _ = sf.read(run_cathar(CATHAR, p, tmp_path / f"up{seed}.wav", "declick", threshold=5.0), dtype="float64")
        # the fidelity build: cathar's arithmetic, cathar's order
        m = cumple_dsp.Declick(fs, threshold=5.0, precision="f32")
        est = m.process_whole(y)
        assert not np.array_equal(up, y)  # upstream acted too, or the comparison is vacuous
        theirs = cathar_gaps(y, threshold=5.0, window=64)  # cathar's detector re-expressed exactly in float32
        ours = list(zip(m.report()["positions"], m.report()["widths"], strict=True))
        assert ours == theirs, f"seed {seed}"  # the same gaps, start for start (shoulders included)
        changed = np.flatnonzero(up != y)
        inside = gap_mask(len(y), [g[0] for g in theirs], [g[1] for g in theirs])
        assert inside[changed].all()  # every sample cathar changed lies inside a listed gap
        assert all((up[s : s + w] != y[s : s + w]).any() for s, w in theirs)  # and every listed gap holds a change
        # spec rule 1: a failure is an arithmetic difference to find, not a bound to widen
        assert np.max(np.abs(est - up)) < 1e-6, f"seed {seed}"
        assert abs(metrics.delta_sdr(x, y, est) - metrics.delta_sdr(x, y, up)) < 0.01, f"seed {seed}"


@needs_core
def test_the_precision_effect_is_measured():
    """Spec rule 1b: the shipped f64 build against the f32 build, printed, not gated; rules 0 and 3 hold for both, rule 3
    on float32-exact input, which the f32 build stores without loss."""
    import cumple_dsp

    # a layout where the two builds' detections differ; see the note on PRECISION_SEED
    x, y, clicks, mask, fs = clicked(seed=PRECISION_SEED)
    ma, mb = cumple_dsp.Declick(fs, precision="f32"), cumple_dsp.Declick(fs, precision="f64")
    a, b = ma.process_whole(y), mb.process_whole(y)
    print(
        f"precision effect: dSDR {metrics.delta_sdr(x, y, b) - metrics.delta_sdr(x, y, a):+.4f} dB, "
        f"max sample {np.max(np.abs(a - b)):.2e}"
    )
    assert not np.array_equal(b, y) and not np.array_equal(a, y)
    # f32 drift is visible here, so a build that computes local_rms in f64 cannot pass the fidelity test
    assert ma.report()["positions"] != mb.report()["positions"]
    # spec rule 3 for each build: outside its own gaps, dilated by the shoulder pad, the output is the input
    y32 = y.astype(np.float32).astype(np.float64)
    for precision in ("f32", "f64"):
        m = cumple_dsp.Declick(fs, precision=precision)
        est = m.process_whole(y32)
        gaps = damage.dilate(gap_mask(len(y32), m.report()["positions"], m.report()["widths"]), 8)
        assert gaps.any() and not gaps.all(), precision
        np.testing.assert_allclose(est[~gaps], y32[~gaps], atol=1e-9, rtol=0, err_msg=precision)


@needs_core
def test_chunking_cost_is_measured_and_small():
    import cumple_dsp

    x, y, clicks, mask, fs = clicked(seed=5)
    whole = cumple_dsp.Declick(fs).process_whole(y)
    a = chunked(cumple_dsp.Declick(fs), y[:, None], block=8192)[:, 0]
    b = chunked(cumple_dsp.Declick(fs), y[:, None], block=16384)[:, 0]
    np.testing.assert_allclose(a, whole, atol=1e-9)  # every gap here is far shorter than the context covers
    np.testing.assert_allclose(b, whole, atol=1e-9)
    # Blocks shorter than a 17-sample gap: its rebuilt samples must reach every centre they fall in. The click
    # at 10005 has the file start in its left context; the one at 20005 has a left context of earlier output.
    clean = 0.3 * np.sin(2 * np.pi * 440 * np.arange(40_000) / 16_000)
    for k in (10_005, 20_005):
        y = clean.copy()
        y[k] += 3.0
        whole = cumple_dsp.Declick(16_000).process_whole(y)
        assert abs(whole[k] - clean[k]) < 0.1
        for block in (4, 8):
            out = chunked(cumple_dsp.Declick(16_000), y[:, None], block=block)[:, 0]
            np.testing.assert_allclose(out, whole, atol=1e-9, err_msg=f"click at {k}, block {block}")
