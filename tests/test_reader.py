from __future__ import annotations

import numpy as np

from cumple.io import iter_blocks, load_package, probe, read
from cumple.io.reader import role_from_name


def test_probe_reports_shape_and_depth(make_wav):
    p = make_wav(sr=48000, channels=2, seconds=1.0, subtype="PCM_24")
    i = probe(p)
    assert (i.container, i.subtype) == ("WAV", "PCM_24")
    assert (i.samplerate, i.channels, i.frames) == (48000, 2, 48000)
    assert i.bit_depth == 24 and not i.is_float
    assert abs(i.duration_s - 1.0) < 1e-9


def test_blocks_cover_every_frame_exactly_once(make_wav):
    p = make_wav(seconds=1.0)
    blocks = list(iter_blocks(p, block_frames=7000))
    assert sum(b.shape[0] for b in blocks) == 48000
    assert all(b.ndim == 2 and b.shape[1] == 2 for b in blocks)
    whole, sr = read(p)
    assert sr == 48000
    np.testing.assert_allclose(np.concatenate(blocks), whole)


def test_full_scale_is_one(make_wav):
    p = make_wav(amplitude=0.5, subtype="PCM_16")
    data, _ = read(p)
    assert 0.49 < np.abs(data).max() <= 0.5


def test_role_from_name():
    assert role_from_name("Show_5.1_L.wav") == "L"
    assert role_from_name("Show.LFE.wav") == "LFE"
    assert role_from_name("show-lt.wav") == "Lt"
    assert role_from_name("Show_Printmaster.wav") is None


def test_package_layout(make_wav, tmp_path):
    for role in ("L", "R", "C", "LFE", "Ls", "Rs"):
        make_wav(name=f"Show_5.1_{role}.wav", channels=1, seconds=0.5)
    pkg = load_package(tmp_path)
    assert pkg.layout_guess == "5.1"
    assert pkg.consistent() == []
    make_wav(name="Show_5.1_Lt.wav", channels=2, seconds=0.25)
    pkg = load_package(tmp_path)
    problems = pkg.consistent()
    assert any("length" in s for s in problems) and any("not mono" in s for s in problems)
