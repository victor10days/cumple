"""ffmpeg is optional: when it is on the machine, compressed deliveries decode; when it is not, nothing here runs."""

from __future__ import annotations

import re
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf
from typer.testing import CliRunner

from cumple.checks.engine import evaluate
from cumple.cli import app
from cumple.fix import fix_file
from cumple.io.ffmpeg import (
    FFMPEG_SUFFIXES,
    Ffmpeg,
    FfmpegError,
    FfprobeInfo,
    decode_budget_s,
    find_ffmpeg,
    iter_blocks_ffmpeg,
    probe_ffmpeg,
    safe_path,
)
from cumple.io.reader import iter_blocks, probe
from cumple.meters.measure import measure
from cumple.report import render_html
from cumple.report.json_out import report_to_dict
from cumple.specs import load_all

TOOLS = find_ffmpeg()
needs_ffmpeg = pytest.mark.skipif(TOOLS is None, reason="ffmpeg and ffprobe are not on PATH")
runner = CliRunner()


def encode(tools, wav: Path, out: Path, *codec_args: str) -> Path:
    """Encode a WAV with the local ffmpeg for the tests only; the package never writes."""
    subprocess.run(
        [str(tools.ffmpeg), "-y", "-nostdin", "-v", "error", "-i", str(wav), *codec_args, str(out)],
        check=True,
        stdin=subprocess.DEVNULL,
        timeout=60,
    )
    return out


@pytest.fixture
def aac_file(tmp_path, make_wav):
    wav = make_wav("tone.wav", seconds=2.0, amplitude=10 ** (-23 / 20))
    return encode(TOOLS, wav, tmp_path / "tone.m4a", "-c:a", "aac", "-b:a", "192k")


def test_the_fallback_suffixes_are_the_ones_libsndfile_refuses():
    assert {".m4a", ".aac", ".mp4", ".mov", ".ac3", ".ec3", ".eac3", ".mxf"} <= FFMPEG_SUFFIXES
    assert ".wav" not in FFMPEG_SUFFIXES and ".flac" not in FFMPEG_SUFFIXES


def test_safe_path_refuses_protocols_and_non_files(tmp_path, make_wav):
    wav = make_wav("tone.wav")
    assert safe_path(wav) == wav.resolve()
    for bad in ("http://example.com/a.m4a", "concat:a.wav|b.wav", "data:audio/aac;base64,AAAA", "C:relative.m4a"):
        with pytest.raises(ValueError):
            safe_path(bad)
    with pytest.raises(ValueError):
        safe_path(tmp_path)  # a directory
    with pytest.raises(ValueError):
        safe_path(tmp_path / "missing.m4a")


def test_the_scheme_regex_catches_one_letter_schemes_and_the_drive_regex_excuses_real_drives():
    # A drive letter is a one-letter "scheme" to the first regex (star quantifier, not plus); the
    # second regex is the carve-out safe_path applies. The file need not exist for this check.
    from cumple.io.ffmpeg import _DRIVE, _SCHEME

    assert _SCHEME.match("C:\\bounce\\mix.m4a") and _DRIVE.match("C:\\bounce\\mix.m4a")
    assert _SCHEME.match("C:/bounce/mix.m4a") and _DRIVE.match("C:/bounce/mix.m4a")
    assert _SCHEME.match("concat:a|b") and not _DRIVE.match("concat:a|b")
    assert _SCHEME.match("C:relative.m4a") and not _DRIVE.match("C:relative.m4a")


def test_decode_budget_is_ten_times_the_duration_plus_a_minute():
    assert decode_budget_s(0.0) == 60.0
    assert decode_budget_s(120.0) == 1260.0


def test_ffprobe_info_subtype_names_pcm_like_libsndfile_and_codecs_by_name():
    pcm = FfprobeInfo("MXF", "pcm_s24le", 48000, 6, 1.0)
    aac = FfprobeInfo("M4A", "aac", 48000, 2, 1.0)
    assert pcm.subtype == "PCM_24" and aac.subtype == "AAC"


@needs_ffmpeg
def test_probe_reports_the_shape_of_an_aac_file(aac_file):
    info = probe_ffmpeg(aac_file, TOOLS)
    assert info.container == "M4A" and info.codec == "aac"
    assert info.samplerate == 48000 and info.channels == 2
    assert abs(info.duration_s - 2.0) < 0.1


@needs_ffmpeg
def test_blocks_cover_the_whole_file_as_float_at_full_scale_one(aac_file, make_wav):
    info = probe_ffmpeg(aac_file, TOOLS)
    blocks = list(
        iter_blocks_ffmpeg(aac_file, TOOLS, info.channels, info.duration_s, block_frames=8192, dtype="float64")
    )
    assert all(b.ndim == 2 and b.shape[1] == 2 and b.dtype == np.float64 for b in blocks)
    frames = sum(len(b) for b in blocks)
    assert abs(frames - 96000) <= 4096  # AAC priming and padding may add or trim a frame or two of samples
    peak = max(float(np.abs(b).max()) for b in blocks)
    expected = 10 ** (-23 / 20)
    assert abs(peak - expected) < 0.02  # the codec is lossy, the scale is not


@needs_ffmpeg
def test_a_file_that_is_not_audio_raises_with_ffmpegs_words(tmp_path):
    bad = tmp_path / "notes.m4a"
    bad.write_text("this is not audio")
    with pytest.raises(FfmpegError) as e:
        probe_ffmpeg(bad, TOOLS)
    assert "Invalid data" in str(e.value) or "moov" in str(e.value) or "Error" in str(e.value)


@pytest.mark.skipif(sys.platform == "win32", reason="the stalling stand-in is a shell script")
def test_a_stalled_decoder_is_killed_when_the_budget_expires(tmp_path, make_wav, monkeypatch):
    """The budget must kill a child that emits nothing, not only refuse to start one."""
    import cumple.io.ffmpeg as mod

    stall = tmp_path / "ffmpeg"
    stall.write_text("#!/bin/sh\nsleep 30\n")
    stall.chmod(0o755)
    tools = Ffmpeg(ffmpeg=stall, ffprobe=stall, version="stall")
    monkeypatch.setattr(mod, "DECODE_BUDGET_FACTOR", 0.0)
    monkeypatch.setattr(mod, "DECODE_BUDGET_FLOOR_S", 0.5)
    wav = make_wav("tone.wav")
    started = time.monotonic()
    with pytest.raises(FfmpegError) as e:
        list(iter_blocks_ffmpeg(wav, tools, 2, 1.0, block_frames=8192, dtype="float64"))
    assert "budget" in str(e.value)
    assert time.monotonic() - started < 5.0  # not the 30 s the child wanted


@needs_ffmpeg
def test_the_version_is_read_from_the_binary():
    assert re.match(r"^[nN]?\d", TOOLS.version), TOOLS.version


CONTAINERS = [
    # ffmpeg encoder arguments, suffix, container token, codec, is_pcm
    (("-c:a", "aac", "-b:a", "192k"), ".m4a", "M4A", "aac", False),
    (("-c:a", "ac3", "-b:a", "192k"), ".ac3", "AC3", "ac3", False),
    (("-c:a", "eac3", "-b:a", "192k"), ".ec3", "EAC3", "eac3", False),
    (("-ac", "1", "-c:a", "pcm_s24le", "-f", "mxf_opatom"), ".mxf", "MXF", "pcm_s24le", True),
]


@needs_ffmpeg
@pytest.mark.parametrize(("args", "suffix", "container", "codec", "is_pcm"), CONTAINERS)
def test_each_claimed_container_probes_and_decodes(tmp_path, make_wav, args, suffix, container, codec, is_pcm):
    wav = make_wav("tone.wav", seconds=1.0, amplitude=10 ** (-23 / 20))
    out = encode(TOOLS, wav, tmp_path / ("tone" + suffix), *args)
    info = probe_ffmpeg(out, TOOLS)
    assert info.container == container and info.codec == codec
    assert (info.subtype in ("PCM_16", "PCM_24", "PCM_32")) is is_pcm
    channels = 1 if "-ac" in args else 2
    assert info.channels == channels and info.samplerate == 48000
    frames = sum(len(b) for b in iter_blocks_ffmpeg(out, TOOLS, info.channels, info.duration_s, block_frames=8192))
    assert abs(frames - 48000) <= 4096


def test_wav_written_by_soundfile_is_the_reference_for_the_aac_test(make_wav):
    wav = make_wav("tone.wav", seconds=2.0, amplitude=10 ** (-23 / 20))
    data, sr = sf.read(str(wav))
    assert sr == 48000 and abs(float(np.abs(data).max()) - 10 ** (-23 / 20)) < 1e-3


@pytest.fixture
def mp3_file(tmp_path, make_wav):
    """libsndfile 1.2 writes and reads MP3 itself; no ffmpeg involved."""
    n = 48000 * 2
    t = np.arange(n) / 48000
    tone = 10 ** (-23 / 20) * np.sin(2 * np.pi * 1000 * t)
    path = tmp_path / "tone.mp3"
    sf.write(str(path), np.repeat(tone[:, None], 2, axis=1), 48000, format="MP3", subtype="MPEG_LAYER_III")
    return path


@needs_ffmpeg
def test_probe_falls_back_to_ffmpeg_for_aac(aac_file):
    info = probe(aac_file)
    assert info.container == "M4A" and info.codec == "aac"
    assert info.decoder.startswith("ffmpeg ") and info.subtype == "AAC"
    assert info.bit_depth is None and not info.is_float
    assert info.samplerate == 48000 and info.channels == 2 and abs(info.frames - 96000) < 4800


@needs_ffmpeg
def test_iter_blocks_uses_the_decoder_the_info_names(aac_file):
    info = probe(aac_file)
    frames = sum(len(b) for b in iter_blocks(aac_file, block_frames=8192, info=info))
    assert abs(frames - 96000) <= 4096


@needs_ffmpeg
def test_an_aac_delivery_measures_like_its_wav(aac_file, make_wav):
    wav = make_wav("ref.wav", seconds=2.0, amplitude=10 ** (-23 / 20))
    a = measure(aac_file)
    w = measure(wav)
    assert abs(a.loudness.integrated - w.loudness.integrated) < 0.5
    assert a.info is not None and a.info.decoder.startswith("ffmpeg ")


@needs_ffmpeg
def test_an_aac_delivery_fails_netflix_and_its_bit_depth_says_not_pcm(aac_file):
    profiles = load_all()
    report = evaluate(profiles["netflix-2.0"], measure(aac_file))
    container = next(f for f in report.findings if f.code == "format.container")
    assert container.status.name == "FAIL"
    assert "M4A" in container.measured and "aac" in container.measured and "ffmpeg" in container.measured
    assert "compression is never allowed" in (container.clause or "")
    depth = next(f for f in report.findings if f.code == "format.bit_depth")
    assert depth.status.name == "FAIL" and "not PCM" in depth.measured and "None" not in depth.measured


def test_an_mp3_fails_netflix_with_the_clause_and_passes_acx(mp3_file):
    """The MP3 -> mp3 token is load-bearing for every audiobook delivery; no ffmpeg needed."""
    profiles = load_all()
    netflix = evaluate(profiles["netflix-2.0"], measure(mp3_file))
    container = next(f for f in netflix.findings if f.code == "format.container")
    assert container.status.name == "FAIL" and container.measured == "MP3"
    assert "compression is never allowed" in (container.clause or "")
    acx = evaluate(profiles["acx"], measure(mp3_file))
    container = next(f for f in acx.findings if f.code == "format.container")
    assert container.status.name == "PASS" and container.measured == "MP3"
    assert "MP3" in render_html(acx) and "MPEG_LAYER_III MP3" not in render_html(acx)


@needs_ffmpeg
def test_json_and_sheet_name_the_decoder_even_without_a_container_clause(aac_file):
    """youtube has no containers clause, so the finding never exists; the report must still say."""
    profiles = load_all()
    report = evaluate(profiles["youtube"], measure(aac_file))
    doc = report_to_dict(report)
    assert doc["measurement"]["container"] == "M4A" and doc["measurement"]["codec"] == "aac"
    assert doc["measurement"]["decoder"].startswith("ffmpeg ")
    html = render_html(report)
    assert "M4A" in html and "via ffmpeg" in html and "None-bit" not in html


def test_json_and_sheet_name_the_container_for_a_wav(make_wav):
    profiles = load_all()
    report = evaluate(profiles["youtube"], measure(make_wav("tone.wav")))
    doc = report_to_dict(report)
    assert doc["measurement"]["container"] == "WAV" and doc["measurement"]["codec"] is None
    assert doc["measurement"]["decoder"] == "libsndfile"
    assert "24-bit WAV" in render_html(report)


@needs_ffmpeg
def test_info_prints_the_decoder(aac_file):
    result = runner.invoke(app, ["info", str(aac_file)])
    assert result.exit_code == 0, result.output
    assert "decoded by ffmpeg" in result.output and "aac" in result.output


def test_without_ffmpeg_the_error_names_what_to_install(tmp_path, monkeypatch):
    import cumple.io.reader as reader_mod

    monkeypatch.setattr(reader_mod, "find_ffmpeg", lambda: None)
    fake = tmp_path / "mix.m4a"
    fake.write_bytes(b"\x00" * 64)
    with pytest.raises(RuntimeError) as e:
        probe(fake)
    assert "ffmpeg" in str(e.value).lower()
    assert "CUMPLE_FFMPEG" in str(e.value)


def test_a_broken_wav_still_reports_libsndfiles_error_not_ffmpegs(tmp_path):
    bad = tmp_path / "broken.wav"
    bad.write_bytes(b"RIFF\x00\x00\x00\x00WAVEjunk")
    with pytest.raises(RuntimeError) as e:
        probe(bad)
    assert "ffmpeg" not in str(e.value).lower()


def test_a_zero_shape_from_ffprobe_raises_instead_of_reaching_the_meter(tmp_path, monkeypatch):
    """A shape ffprobe could not fill in (0 Hz, 0 channels) must never reach LoudnessMeter,
    which divides by the sample rate and the channel count."""
    import cumple.io.reader as reader_mod

    monkeypatch.setattr(reader_mod, "find_ffmpeg", lambda: Ffmpeg(Path("/x"), Path("/x"), "0"))
    monkeypatch.setattr(reader_mod, "probe_ffmpeg", lambda path, tools: FfprobeInfo("M4A", "aac", 0, 0, 1.0))
    fake = tmp_path / "mix.m4a"
    fake.write_bytes(b"\x00" * 64)
    with pytest.raises(RuntimeError) as e:
        probe(fake)
    assert "no usable audio stream" in str(e.value)


@needs_ffmpeg
def test_fix_refuses_an_ffmpeg_decoded_file_and_says_bounce_it_first(aac_file):
    profiles = load_all()
    with pytest.raises(ValueError, match="PCM only"):
        fix_file(aac_file, profiles["youtube"])


@needs_ffmpeg
def test_a_pcm_stream_ffmpeg_decoded_still_names_the_decoder_in_the_sheet(tmp_path, make_wav):
    """MXF wraps PCM: bit_depth is not None, but the decoder is still ffmpeg and the sheet must say."""
    wav = make_wav("tone.wav", seconds=1.0, amplitude=10 ** (-23 / 20))
    out = encode(TOOLS, wav, tmp_path / "tone.mxf", "-ac", "1", "-c:a", "pcm_s24le", "-f", "mxf_opatom")
    profiles = load_all()
    report = evaluate(profiles["youtube"], measure(out))
    html = render_html(report)
    assert "24-bit MXF" in html and "via ffmpeg" in html
