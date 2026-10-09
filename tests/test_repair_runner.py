"""The repair runner: a copy written the way `fix` writes one, block by block by the chunk protocol, and its receipt."""

from __future__ import annotations

import dataclasses
import hashlib
import json

import numpy as np
import pytest
import soundfile as sf

from cumple import __version__
from cumple.repair import chain, damage, metrics, runner
from cumple.repair.receipt import Receipt
from cumple.repair.runner import repair_file
from tests.repair_helpers import chunked
from tests.test_repair_baselines import FIXTURE
from tests.test_repair_core import needs_core

pytestmark = needs_core
BLOCK = 8192
# The cost of the two-module chain at 8,192-frame blocks: ΔSDR(process_whole twice) minus ΔSDR(runner), in dB.
# It splits into De-clip's own chunking cost (whole against two chunked passes, where De-clip's right context has
# been through De-click) and the cost of the raw right context the spec gives every module (two chunked passes
# against the runner). Measured on 2026-10-09 on an arm64 Mac, fixture clipped to 5 dB input SDR, seed 3 clicks:
# +0.0125 in all, -0.1326 of it De-clip's chunking, +0.1451 the raw right context. Over 24 layouts (input SDR 3,
# 5 and 10 dB, seeds 1 to 8): the total -0.124 to +0.056, De-clip's chunking -0.208 to +0.238, the raw right
# context -0.257 to +0.204. The raw right context costs no more than A-SPADE's own block edges, and the two partly
# cancel. The tolerance is twice the largest total measured.
CHAIN_COST_TOLERANCE = 0.25


def sha(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def names(folder) -> list[str]:
    return sorted(p.name for p in folder.iterdir())


def read(path) -> np.ndarray:
    return sf.read(path, dtype="float64", always_2d=True)[0]


def clicked_fixture(tmp_path, seed: int = 3):
    """The fixture with seeded impulse clicks, stored as float32: (path, clean, stored, clicks, rate)."""
    x, fs = sf.read(FIXTURE, dtype="float64")
    y, clicks, _ = damage.add_clicks(x, fs, seed=seed, per_minute=200, **damage.IMPULSE)
    path = tmp_path / "clicks.wav"
    sf.write(path, y, fs, subtype="FLOAT")  # the clicks reach 2.6, above full scale, which only a float file holds
    return path, x, read(path)[:, 0], clicks, fs


def clicked_and_clipped(tmp_path, seed: int = 3):
    """The fixture clipped to 5 dB input SDR, then clicked: (path, clean, stored, clip threshold, rate)."""
    x, fs = sf.read(FIXTURE, dtype="float64")
    clipped, thr, _ = damage.clip_to_sdr(x, 5.0)
    y, _, _ = damage.add_clicks(clipped, fs, seed=seed, per_minute=200, **damage.IMPULSE)
    path = tmp_path / "both.wav"
    sf.write(path, y, fs, subtype="FLOAT")
    return path, x, read(path)[:, 0], thr, fs


def tone(fs: int = 48000, seconds: float = 2.0) -> np.ndarray:
    """Two low sines with no digital silence, so the click detector has nothing to fire on."""
    t = np.arange(int(fs * seconds)) / fs
    return 0.02 * (np.sin(2 * np.pi * 440 * t) + 0.5 * np.sin(2 * np.pi * 1234 * t))


def stereo_clicked_in_one_channel(tmp_path):
    """24-bit stereo: channel 0 the clean tone, channel 1 the same tone with clicks. (path, clicks)."""
    clean = tone()
    hit, clicks, _ = damage.add_clicks(clean, 48000, seed=3, per_minute=200, **damage.IMPULSE)
    assert np.max(np.abs(hit)) < 1.0, "setup: a click above full scale would be stored clipped"
    path = tmp_path / "stereo.wav"
    sf.write(path, np.column_stack([clean, hit]), 48000, subtype="PCM_24")
    return path, clicks


def test_declick_writes_a_repaired_copy_and_a_receipt_beside_it(tmp_path):
    import cumple_dsp

    src, x, y, clicks, fs = clicked_fixture(tmp_path)
    dst = tmp_path / "out.wav"
    c = chain.parse("declick()")
    r = repair_file(src, c, dst)
    assert r.changed and r.dst == dst and r.receipt_path == tmp_path / "out.wav.cumple-repair.json"
    assert names(tmp_path) == ["clicks.wav", "out.wav", "out.wav.cumple-repair.json"]
    assert sha(dst) != sha(src)
    shape = ("format", "subtype", "samplerate", "channels", "frames")
    assert [getattr(sf.info(str(dst)), k) for k in shape] == [getattr(sf.info(str(src)), k) for k in shape]
    # 3 s fit in one block, so the copy is one call over the whole file, stored as float32 and not clipped
    m = cumple_dsp.Declick(fs)
    assert np.array_equal(read(dst)[:, 0], m.process_whole(y).astype(np.float32))

    text = r.receipt_path.read_text(encoding="utf-8")
    receipt = json.loads(text)
    assert Receipt.model_validate_json(text) == r.receipt
    assert receipt["cumple_version"] == __version__
    assert receipt["cumple_dsp_version"] == cumple_dsp.__version__
    assert receipt["core_version"] == cumple_dsp.core_version()
    assert receipt["chain_yaml"] == chain.dump(c) and chain.Chain.model_validate(receipt["chain"]) == c
    assert receipt["input"]["sha256"] == sha(src) and receipt["output"]["sha256"] == sha(dst)
    assert receipt["input"]["path"] == str(src.resolve()) and receipt["output"]["path"] == str(dst.resolve())
    assert receipt["residual"] is None
    for when in ("before", "after"):
        assert set(receipt[when]) == {"integrated_lufs", "true_peak_dbtp", "sample_peak_dbfs", "clipped_runs"}
    assert receipt["before"]["sample_peak_dbfs"] > 6.0  # the clicks were the peaks, at up to 2.6
    assert receipt["after"]["sample_peak_dbfs"] < -6.0
    assert len(receipt["reports"]) == 1 and receipt["reports"][0] == {"module": "declick", **m.report()}
    assert receipt["reports"][0]["clicks"] >= len(clicks) * 0.9
    assert receipt["wall_time_s"] > 0


def test_repair_refuses_the_source_a_directory_and_a_decoded_file(tmp_path, monkeypatch):
    src, *_ = clicked_fixture(tmp_path)
    before = sha(src)
    c = chain.parse("declick()")
    with pytest.raises(ValueError, match="source"):
        repair_file(src, c, src)
    with pytest.raises(ValueError, match="directory"):
        repair_file(src, c, tmp_path)
    with pytest.raises(ValueError, match="source"):
        repair_file(src, c, tmp_path / "out.wav", residual=src)
    with pytest.raises(ValueError, match="different"):
        repair_file(src, c, tmp_path / "out.wav", residual=tmp_path / "out.wav")
    real = runner.probe(src)
    decoded = dataclasses.replace(real, subtype="AAC", decoder="ffmpeg 9.0.1", codec="aac")
    monkeypatch.setattr(runner, "probe", lambda path: decoded)
    with pytest.raises(ValueError, match="PCM only"):
        repair_file(src, c, tmp_path / "out.wav")
    assert sha(src) == before and names(tmp_path) == ["clicks.wav"]


def test_each_channel_is_repaired_on_its_own(tmp_path):
    src, clicks = stereo_clicked_in_one_channel(tmp_path)
    r = repair_file(src, chain.parse("declick()"), tmp_path / "out.wav")
    x, y = read(src), read(tmp_path / "out.wav")
    assert sf.info(str(tmp_path / "out.wav")).subtype == "PCM_24"
    assert np.array_equal(y[:, 0], x[:, 0])  # the clean channel comes back bit for bit
    assert not np.array_equal(y[:, 1], x[:, 1])
    report = r.reports[0]
    assert report["clicks"] >= len(clicks) * 0.9 and set(report["channels"]) == {1}
    assert metrics.delta_sdr(tone(), x[:, 1], y[:, 1]) > 3.0


def test_the_residual_is_the_input_minus_the_copy(tmp_path):
    src, _ = stereo_clicked_in_one_channel(tmp_path)
    dst, res = tmp_path / "out.wav", tmp_path / "clicks-only.wav"
    r = repair_file(src, chain.parse("declick()"), dst, residual=res)
    x, y, d = read(src), read(dst), read(res)
    assert sf.info(str(res)).subtype == "PCM_24"
    np.testing.assert_allclose(d, x - y, atol=1e-9, rtol=0)
    assert np.any(d[:, 1] != 0) and not np.any(d[:, 0])
    assert r.receipt.residual is not None and r.receipt.residual.sha256 == sha(res)


def test_a_clean_file_changes_nothing_and_writes_nothing(tmp_path):
    src = tmp_path / "clean.wav"
    sf.write(src, np.column_stack([tone(), tone()]), 48000, subtype="PCM_24")
    r = repair_file(src, chain.parse("declick(),declip()"), tmp_path / "out.wav", residual=tmp_path / "res.wav")
    assert not r.changed and r.dst is None and r.receipt_path is None and r.receipt is None
    assert [rep["module"] for rep in r.reports] == ["declick", "declip"]
    assert r.reports[0]["clicks"] == 0 and r.reports[1]["runs"] == 0
    assert names(tmp_path) == ["clean.wav"]


def test_a_failure_half_way_leaves_no_temporary_file_and_the_old_copy_alone(tmp_path, monkeypatch):
    src, *_ = clicked_fixture(tmp_path)
    dst = tmp_path / "out.wav"
    dst.write_bytes(b"yesterday's copy")
    write, calls = sf.SoundFile.write, []

    def fails_on_the_third_write(self, data):
        calls.append(len(data))
        if len(calls) == 3:
            raise OSError("disk full")
        return write(self, data)

    monkeypatch.setattr(sf.SoundFile, "write", fails_on_the_third_write)
    with pytest.raises(OSError, match="disk full"):
        repair_file(src, chain.parse("declick()"), dst, residual=tmp_path / "res.wav", block_frames=BLOCK)
    assert calls == [BLOCK, BLOCK, BLOCK]  # copy, residual, copy: it failed with both files part-written
    assert names(tmp_path) == ["clicks.wav", "out.wav"] and dst.read_bytes() == b"yesterday's copy"


def test_one_module_in_blocks_is_the_chunk_protocol_call_for_call(tmp_path):
    """At 8,192-frame blocks the copy is chunked()'s output (tests/repair_helpers.py), sample for sample."""
    import cumple_dsp

    src, x, y, thr, fs = clicked_and_clipped(tmp_path)
    for name, text, make in (
        ("declick", "declick()", lambda: cumple_dsp.Declick(fs)),
        ("declip", f"declip(threshold={thr!r})", lambda: cumple_dsp.Declip(fs, threshold=thr)),
    ):
        r = repair_file(src, chain.parse(text), tmp_path / f"{name}.wav", block_frames=BLOCK)
        module = make()
        want = chunked(module, y[:, None], BLOCK)[:, 0]
        assert np.array_equal(read(tmp_path / f"{name}.wav")[:, 0], want.astype(np.float32)), text
        assert r.reports[0] == {"module": name, **module.report()}, text
        whole = make().process_whole(y)
        print(
            f"{text} through the runner at {BLOCK}: dSDR {metrics.delta_sdr(x, y, whole) - metrics.delta_sdr(x, y, want):+.4f} dB "
            f"against process_whole, max sample {np.max(np.abs(want - whole)):.2e}"
        )


def test_a_two_module_chain_in_blocks_costs_what_raw_right_context_costs(tmp_path):
    """Spec section 3: each module's right context is the raw lookahead, so De-clip sees clicks De-click has not
    yet removed to the right of each centre. Against process_whole twice, the cost is measured and held."""
    import cumple_dsp

    src, x, y, thr, fs = clicked_and_clipped(tmp_path)
    dst = tmp_path / "chain.wav"
    r = repair_file(src, chain.parse(f"declick(),declip(threshold={thr!r})"), dst, block_frames=BLOCK)
    out = read(dst)[:, 0]
    whole = cumple_dsp.Declip(fs, threshold=thr).process_whole(cumple_dsp.Declick(fs).process_whole(y))
    passes = chunked(cumple_dsp.Declick(fs), y[:, None], BLOCK)
    passes = chunked(cumple_dsp.Declip(fs, threshold=thr), passes, BLOCK)[:, 0]
    reference = metrics.delta_sdr(x, y, whole)
    cost = reference - metrics.delta_sdr(x, y, out)
    declip_chunking = reference - metrics.delta_sdr(x, y, passes)
    print(
        f"two-module chain at {BLOCK}: dSDR {metrics.delta_sdr(x, y, out):+.4f} dB against {reference:+.4f} whole, "
        f"cost {cost:+.4f} dB ({declip_chunking:+.4f} of it De-clip's own chunking), "
        f"max sample {np.max(np.abs(out - whole)):.2e}"
    )
    assert [rep["module"] for rep in r.reports] == ["declick", "declip"]
    assert r.reports[0]["clicks"] > 0 and r.reports[1]["runs"] > 0
    assert abs(cost) < CHAIN_COST_TOLERANCE


def test_the_file_edges_reach_the_module_as_file_edges(tmp_path):
    """Clicks in the first block and the last: the runner passes Edge.first and the file's true end, so De-click
    solves AR at both ends and no gap is filled linearly for want of context (the report counts both fallbacks)."""
    import cumple_dsp

    fs, n = 16_000, 41_234  # not a multiple of the block
    y = tone(fs, 3.0)[:n]
    for k in (300, 20_000, n - 300):
        y[k] += 0.5
    src = tmp_path / "edges.wav"
    sf.write(src, y, fs, subtype="FLOAT")
    y = read(src)[:, 0]
    r = repair_file(src, chain.parse("declick()"), tmp_path / "out.wav", block_frames=BLOCK)
    report = r.reports[0]
    assert report["clicks"] == 3
    centres = [p + w // 2 for p, w in zip(report["positions"], report["widths"], strict=True)]
    assert np.max(np.abs(np.subtract(centres, [300, 20_000, n - 300]))) <= 1
    assert report["context_fallbacks"] == 0 and report["linear_fallbacks"] == 0
    out = read(tmp_path / "out.wav")[:, 0]
    assert len(out) == n
    np.testing.assert_allclose(out, cumple_dsp.Declick(fs).process_whole(y), atol=1e-6, rtol=0)
