"""De-clip: the f32 build matches upstream cathar at every survey level, chunking costs what it costs, and no unclipped sample moves."""

from __future__ import annotations

import numpy as np
import pytest
import soundfile as sf
from scripts.benchmark_repair import find_cathar, run_cathar

from cumple.io.reader import DEFAULT_BLOCK_FRAMES
from cumple.repair import damage, metrics
from tests.repair_helpers import chunked
from tests.test_repair_baselines import FIXTURE, needs_cathar
from tests.test_repair_core import needs_core

CATHAR = find_cathar()
LEVELS = (1, 3, 5, 7, 10, 15, 20)  # the survey's input SDRs, in dB
FRAME = 1024  # A-SPADE's frame


def clipped(level: float, tiles: int = 1):
    """The fixture, repeated `tiles` times, hard-clipped to `level` dB input SDR: (clean, clipped, threshold, mask, rate).

    The fixture is 16-bit and the threshold is a float32 value, so every clipped sample is float32-exact.
    """
    x, fs = sf.read(FIXTURE, dtype="float64")
    x = np.tile(x, tiles)
    y, thr, mask = damage.clip_to_sdr(x, level)
    return x, y, thr, mask, fs


def runs(mask: np.ndarray) -> tuple[list[int], list[int]]:
    """Start and length of every run of True in mask."""
    edges = np.diff(np.concatenate(([0], mask.astype(np.int8), [0])))
    starts, ends = np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)
    return starts.tolist(), (ends - starts).tolist()


def cost(x, y, whole, out) -> float:
    """The chunking cost: whole-file ΔSDR(all) minus chunked ΔSDR(all), in dB."""
    return metrics.delta_sdr(x, y, whole) - metrics.delta_sdr(x, y, out)


@needs_core
def test_declip_restores_the_clipped_fixture_and_leaves_every_unclipped_sample_alone():
    import cumple_dsp

    x, y, thr, mask, fs = clipped(5)
    m = cumple_dsp.Declip(fs, threshold=thr)
    est = m.process_whole(y)
    assert not np.array_equal(est, y)  # spec rule 0
    assert metrics.delta_sdr(x, y, est) >= 2.0  # 03c measured +7.56 for a faithful port
    assert np.array_equal(est[~mask], y[~mask])  # spec rule 3: the projection returns them unchanged, no dilation
    # 03c measured +1.98 at 5 dB; at 1 and 3 dB A-SPADE overshoots, which REPAIR.md reports rather than this test
    assert abs(metrics.peak_error_db(x, est, mask)) < 3.0
    report = m.report()
    positions, widths = runs(mask)
    assert (report["positions"], report["widths"]) == (positions, widths)
    assert report["runs"] == len(positions) and report["longest_run"] == max(widths)
    assert report["channels"] == [0] * len(positions)
    assert report["peak_in"] == thr and report["peak_out"] == np.max(np.abs(est))
    assert 1 <= report["iterations"] <= 100
    assert report["frames"] == (len(y) - FRAME) // 256 + 2  # off the hop grid, so a flush frame ends the layout


@needs_core
@needs_cathar
@pytest.mark.parametrize("level", LEVELS)
def test_declip_matches_upstream_cathar_whole_file(level, tmp_path):
    """Spec rule 1: the f32 build does cathar's arithmetic in cathar's order, so a failure is a difference to find."""
    import cumple_dsp

    x, y, thr, mask, fs = clipped(level)
    p = tmp_path / f"clip{level}.wav"
    sf.write(p, y, fs, subtype="FLOAT")
    y, _ = sf.read(p, dtype="float64")  # the stored float32 values cathar reads
    up, _ = sf.read(run_cathar(CATHAR, p, tmp_path / f"up{level}.wav", "declip", threshold=thr), dtype="float64")
    est = cumple_dsp.Declip(fs, threshold=thr, precision="f32").process_whole(y)
    assert not np.array_equal(up, y)  # spec rule 0: upstream acted, or the comparison is vacuous
    assert np.array_equal(est[~mask], y[~mask]) and np.array_equal(up[~mask], y[~mask])
    worst = np.max(np.abs(est - up))
    assert worst < 1e-6, f"{level} dB: largest sample difference {worst:.3e}"
    gap = metrics.delta_sdr(x, y, est) - metrics.delta_sdr(x, y, up)
    assert abs(gap) < 0.01, f"{level} dB: ΔSDR differs by {gap:+.4f} dB"


@needs_core
def test_the_precision_effect_is_measured():
    """Spec rule 1b: the shipped f64 build against the f32 build at each level, printed, not gated."""
    import cumple_dsp

    for level in LEVELS:
        x, y, thr, mask, fs = clipped(level)
        a = cumple_dsp.Declip(fs, threshold=thr, precision="f32").process_whole(y)
        b = cumple_dsp.Declip(fs, threshold=thr, precision="f64").process_whole(y)
        print(
            f"precision effect at {level} dB: dSDR {metrics.delta_sdr(x, y, b) - metrics.delta_sdr(x, y, a):+.4f} dB, "
            f"max sample {np.max(np.abs(a - b)):.2e}"
        )
        assert not np.array_equal(a, b), f"{level} dB: the two precisions gave the same samples"
        assert np.array_equal(a[~mask], y[~mask]) and np.array_equal(b[~mask], y[~mask])


@needs_core
def test_chunking_cost_is_measured_and_small():
    """Spec rule 2 on the fixture at 8,192-sample blocks: printed, and held under 0.5 dB (03c measured 0.29)."""
    import cumple_dsp

    x, y, thr, mask, fs = clipped(5)
    whole = cumple_dsp.Declip(fs, threshold=thr).process_whole(y)
    out = chunked(cumple_dsp.Declip(fs, threshold=thr), y[:, None], block=8192)[:, 0]
    print(f"chunking cost at 8192: dSDR {cost(x, y, whole, out):+.4f} dB, max sample {np.max(np.abs(out - whole)):.2e}")
    assert abs(cost(x, y, whole, out)) < 0.5
    assert np.array_equal(out[~mask], y[~mask])


@needs_core
def test_chunking_cost_over_more_than_two_blocks():
    """The fixture tiled to 36 s, more than two blocks of DEFAULT_BLOCK_FRAMES; one 65,536 block would hold 3 s whole."""
    import cumple_dsp

    x, y, thr, mask, fs = clipped(5, tiles=12)
    assert len(y) > 2 * DEFAULT_BLOCK_FRAMES
    whole = cumple_dsp.Declip(fs, threshold=thr).process_whole(y)
    for block in (DEFAULT_BLOCK_FRAMES, 65_536):
        out = chunked(cumple_dsp.Declip(fs, threshold=thr), y[:, None], block=block)[:, 0]
        print(
            f"chunking cost at {block} on 36 s: dSDR {cost(x, y, whole, out):+.4f} dB, "
            f"max sample {np.max(np.abs(out - whole)):.2e}"
        )
        assert abs(cost(x, y, whole, out)) < 0.5, f"block {block}"
        assert np.array_equal(out[~mask], y[~mask]), f"block {block}"


@needs_core
def test_a_clipped_run_longer_than_a_block_is_rebuilt_in_every_centre_and_reported_once():
    """Blocks shorter than a clipped run: each centre the run reaches is rebuilt, and the report counts the run once.

    A 3 Hz tone at 0.5 with a 440 Hz ripple, clipped at 0.3: the runs on the slow peaks are about 1,350 samples.
    A-SPADE in blocks need not match one call; the cubic fill in blocks matches it exactly.
    """
    import cumple_dsp

    fs = 16_000
    t = np.arange(16_000) / fs
    x = 0.5 * np.sin(2 * np.pi * 3 * t) + 0.05 * np.sin(2 * np.pi * 440 * t)
    thr = float(np.float32(0.3))
    y, mask = np.clip(x, -thr, thr), np.abs(x) >= thr
    positions, widths = runs(mask)
    assert max(widths) > 1000
    for method, blocks in (("spade", (500, 1000)), ("cubic", (1, 7, 500, 1000))):
        one = cumple_dsp.Declip(fs, threshold=thr, method=method)
        whole = one.process_whole(y)
        for block in blocks:
            m = cumple_dsp.Declip(fs, threshold=thr, method=method)
            out = chunked(m, y[:, None], block=block)[:, 0]
            label = f"{method}, block {block}"
            assert (m.report()["positions"], m.report()["widths"]) == (positions, widths), label
            assert m.report()["longest_run"] == one.report()["longest_run"] == max(widths), label
            if method == "cubic":
                assert np.array_equal(out, whole), label
                continue
            print(f"{label}: dSDR {cost(x, y, whole, out):+.4f} dB, max sample {np.max(np.abs(out - whole)):.2e}")
            assert np.array_equal(out[~mask], y[~mask]), label
            assert np.all(np.abs(out[mask]) >= thr), label  # every clipped sample stays clipping-consistent
            for s, w in zip(positions, widths, strict=True):
                # every centre holding 64 or more of a run's samples holds rebuilt ones, not only the plateau
                for c in range(s // block * block, s + w, block):
                    inside = slice(max(s, c), min(s + w, c + block))
                    if inside.stop - inside.start >= 64:
                        assert np.any(out[inside] != y[inside]), f"{label}: run at {s}, centre at {c}"


@needs_core
def test_a_file_below_the_threshold_and_a_chunk_shorter_than_a_frame_pass_through():
    import cumple_dsp

    x, fs = sf.read(FIXTURE, dtype="float64")
    above = float(np.float32(np.max(np.abs(x)) * 1.01))
    m = cumple_dsp.Declip(fs, threshold=above)
    assert np.array_equal(m.process_whole(x), x)
    assert m.report()["runs"] == 0 and m.report()["iterations"] == 0 and m.report()["frames"] == 0

    x, y, thr, mask, fs = clipped(5)
    k = int(np.flatnonzero(mask)[0])
    short = y[k : k + FRAME - 1]
    assert mask[k : k + FRAME - 1].sum() > 10
    assert np.array_equal(cumple_dsp.Declip(fs, threshold=thr).process_whole(short), short)
    m = cumple_dsp.Declip(fs, threshold=thr)
    assert np.array_equal(m.process(short, edge=(True, True, 0)), short)
    assert m.report()["runs"] > 0 and m.report()["iterations"] == 0


@needs_core
def test_declip_refuses_what_it_cannot_use():
    import cumple_dsp

    for threshold in (0.0, 5e-5, 1.5, float("nan")):
        with pytest.raises(ValueError, match="threshold"):
            cumple_dsp.Declip(48000, threshold=threshold)
    with pytest.raises(ValueError, match="method"):
        cumple_dsp.Declip(48000, method="social")
    with pytest.raises(ValueError, match="precision"):
        cumple_dsp.Declip(48000, precision="f16")
