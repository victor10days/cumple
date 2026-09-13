# ffmpeg codec and container conformance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A compressed or wrapped delivery (AAC in M4A/MP4/MOV, AC-3, E-AC-3, the audio of an MXF) is decoded by a local ffmpeg when one is installed, measured exactly as a WAV is, and reported with the decoder named, so the destination's container clause fails on the file itself instead of the tool refusing to open it.

**Architecture:** One new read-only module `src/cumple/io/ffmpeg.py` wraps `ffprobe` (JSON probe) and `ffmpeg` (raw float32 stream on stdout) behind argv lists with stdin closed, a protocol whitelist, timeouts and a bounded stderr. `reader.probe` falls back to it when libsndfile refuses a file whose suffix is in `FFMPEG_SUFFIXES`; `reader.iter_blocks` streams through it when the `AudioInfo` says so; `AudioInfo` gains `decoder` and `codec`. The engine's container mapping learns the new tokens and the bit-depth finding says "not PCM" instead of "None-bit". libsndfile 1.2.2 already reads MP3 natively (format token `MP3`), so MP3 needs no fallback and the docs say so.

**Tech Stack:** Python 3.12, numpy, soundfile (libsndfile 1.2.2), subprocess; ffmpeg 9.0.1 on this Mac, apt ffmpeg on the CI Linux runner. No new dependency.

**Spec:** `docs/graph-runs/2026-09-12-ffmpeg-codec-conformance/01-frame.md` (the capability contract and constraints).

## Global Constraints

- No new runtime dependency. `pyproject.toml` dependencies stay as they are.
- Every subprocess call: an argv list, `stdin=subprocess.DEVNULL`, `-nostdin` for ffmpeg, `-protocol_whitelist file` (ffprobe) or `file,pipe` (ffmpeg), a timeout that KILLS the child when it expires (ffprobe through `subprocess.run(timeout=)`, ffmpeg through a `threading.Timer` that calls `proc.kill()`), stderr capped at 4096 bytes, stdout closed in `finally`, no option built from user text other than the resolved absolute path.
- Paths handed to ffmpeg are absolute, resolved, regular files; a path matching `^[A-Za-z][A-Za-z0-9+.\-]*:` (star quantifier: a one-letter drive counts as a scheme) is refused unless it is a Windows drive prefix `^[A-Za-z]:[\\/]`.
- Tests that need ffmpeg skip with `pytest.mark.skipif(find_ffmpeg() is None, reason=...)`; nothing in the suite requires ffmpeg. MP3 fixtures are written by libsndfile itself (`sf.write(..., format="MP3", subtype="MPEG_LAYER_III")`, verified on this Mac) and never skip.
- The measurement entry point is `cumple.meters.measure.measure(path, ...)`; there is no `measure_file`.
- No em or en dashes in prose. The phrase "not checked" never appears. Counts re-pinned from `uv run pytest --collect-only | grep 'tests collected'` in README.md, CONTRIBUTING.md, docs/QA.md, AI_USAGE.md and site/index.html (tests/test_counts.py enforces it).
- Commit after every task with the attribution lines the session reminder gives.
- Run commands from the worktree `/Users/Victor/Code/cumple-wt/loop-02-ffmpeg`; `uv run pytest` alone, never piped into another command.

---

### Task 1: The ffmpeg module

**Files:**
- Create: `src/cumple/io/ffmpeg.py`
- Test: `tests/test_ffmpeg_io.py`

**Interfaces:**
- Consumes: nothing from other tasks.
- Produces: `FFMPEG_SUFFIXES: set[str]`; `class Ffmpeg(ffmpeg: Path, ffprobe: Path, version: str)`; `find_ffmpeg() -> Ffmpeg | None` (cached per environment, PATHEXT-aware through `shutil.which`); `safe_path(path) -> Path`; `class FfprobeInfo(container: str, codec: str, samplerate: int, channels: int, duration_s: float)` with property `subtype -> str`; `probe_ffmpeg(path, tools: Ffmpeg) -> FfprobeInfo`; `iter_blocks_ffmpeg(path, tools: Ffmpeg, channels: int, duration_s: float, block_frames: int, dtype: str) -> Iterator[np.ndarray]`; `class FfmpegError(RuntimeError)`; `decode_budget_s(duration_s: float) -> float`.

- [ ] **Step 1: Write the failing tests**

```python
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

TOOLS = find_ffmpeg()
needs_ffmpeg = pytest.mark.skipif(TOOLS is None, reason="ffmpeg and ffprobe are not on PATH")


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
    blocks = list(iter_blocks_ffmpeg(aac_file, TOOLS, info.channels, info.duration_s, block_frames=8192, dtype="float64"))
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_ffmpeg_io.py -v`
Expected: FAIL at import with "No module named 'cumple.io.ffmpeg'".

- [ ] **Step 3: Write the module**

```python
"""Decode compressed and wrapped deliveries through a local ffmpeg, when one is installed.

ffmpeg is optional. Nothing here runs unless libsndfile refused the file, and every call is an
argument list to a resolved executable with stdin closed, a protocol whitelist, a timeout and a
bounded error buffer. Read-only, like the rest of the io package: nothing is written or moved.
"""

from __future__ import annotations

import functools
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import numpy as np

# Suffixes libsndfile does not open and ffmpeg does. libsndfile 1.2 reads MP3 itself, so .mp3 is
# here only as a fallback for a build without mpg123. The watch folder does not use this list.
FFMPEG_SUFFIXES = {".mp3", ".m4a", ".aac", ".mp4", ".mov", ".ac3", ".ec3", ".eac3", ".mxf"}

PROBE_TIMEOUT_S = 30.0
DECODE_BUDGET_FACTOR = 10.0  # wall time allowed for a decode: this times the duration ...
DECODE_BUDGET_FLOOR_S = 60.0  # ... plus this
STDERR_CAP = 4096

# Anything that reads as a URL scheme or an ffmpeg protocol prefix (concat:, subfile:, data:) is
# refused; a Windows drive letter ("C:\") is the one colon a real path may carry at the front.
_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*:")
_DRIVE = re.compile(r"^[A-Za-z]:[\\/]")

# ffprobe codec names for PCM, as libsndfile would name the subtype; everything else is lossy.
PCM_SUBTYPES = {
    "pcm_s16le": "PCM_16",
    "pcm_s16be": "PCM_16",
    "pcm_s24le": "PCM_24",
    "pcm_s24be": "PCM_24",
    "pcm_s32le": "PCM_32",
    "pcm_s32be": "PCM_32",
    "pcm_f32le": "FLOAT",
    "pcm_f32be": "FLOAT",
    "pcm_f64le": "DOUBLE",
    "pcm_f64be": "DOUBLE",
}

# ffprobe reports the QuickTime family as one string; the file's own suffix names the container.
_MOV_FAMILY = "mov,mp4,m4a,3gp,3g2,mj2"


class FfmpegError(RuntimeError):
    """ffmpeg or ffprobe could not do what was asked; the message carries its last lines."""


@dataclass(frozen=True)
class Ffmpeg:
    ffmpeg: Path
    ffprobe: Path
    version: str  # "9.0.1", or "unknown"


def find_ffmpeg() -> Ffmpeg | None:
    """The ffmpeg and ffprobe pair under CUMPLE_FFMPEG (a directory or the ffmpeg binary), else on PATH.

    Cached per environment: one `ffmpeg -version` per process, not one per file.
    """
    return _locate(os.environ.get("CUMPLE_FFMPEG") or "", shutil.which("ffmpeg") or "")


@functools.lru_cache(maxsize=8)
def _locate(hint: str, on_path: str) -> Ffmpeg | None:
    pairs: list[tuple[str | None, str | None]] = []
    if hint:
        p = Path(hint)
        directory = str(p.parent if p.is_file() else p)
        pairs.append((shutil.which("ffmpeg", path=directory), shutil.which("ffprobe", path=directory)))
    if on_path:
        pairs.append((on_path, shutil.which("ffprobe")))
    for exe, probe in pairs:
        if exe and probe:
            return Ffmpeg(Path(exe), Path(probe), _version(Path(exe)))
    return None


def _version(exe: Path) -> str:
    try:
        out = subprocess.run(
            [str(exe), "-version"],
            capture_output=True,
            text=True,
            timeout=PROBE_TIMEOUT_S,
            stdin=subprocess.DEVNULL,
            check=False,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    m = re.match(r"ffmpeg version (\S+)", out)
    return m.group(1) if m else "unknown"


def safe_path(path: str | Path) -> Path:
    """An absolute, existing regular file whose text ffmpeg cannot read as a protocol."""
    text = str(path)
    if _SCHEME.match(text) and not _DRIVE.match(text):
        raise ValueError(f"refusing a path that reads as a protocol or URL: {text!r}")
    p = Path(path).resolve()
    if not p.is_file():
        raise ValueError(f"not a regular file: {p}")
    return p


def decode_budget_s(duration_s: float) -> float:
    return DECODE_BUDGET_FACTOR * max(duration_s, 0.0) + DECODE_BUDGET_FLOOR_S


@dataclass(frozen=True)
class FfprobeInfo:
    container: str  # "M4A", "MP4", "MOV", "MXF", "AC3", "EAC3", "MP3" ...
    codec: str  # ffprobe's codec_name: "aac", "ac3", "eac3", "pcm_s24le" ...
    samplerate: int
    channels: int
    duration_s: float

    @property
    def subtype(self) -> str:
        """libsndfile's name for a PCM codec; the codec name upper-cased for anything lossy."""
        return PCM_SUBTYPES.get(self.codec, self.codec.upper())


def _tail(stderr_file) -> str:
    stderr_file.seek(0, os.SEEK_END)
    size = stderr_file.tell()
    stderr_file.seek(max(0, size - STDERR_CAP))
    return stderr_file.read().decode("utf-8", "replace").strip()


def probe_ffmpeg(path: str | Path, tools: Ffmpeg) -> FfprobeInfo:
    """Container, codec and shape of the first audio stream, from ffprobe's JSON."""
    p = safe_path(path)
    argv = [
        str(tools.ffprobe),
        "-v", "error",
        "-protocol_whitelist", "file",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        "-select_streams", "a:0",
        str(p),
    ]
    try:
        done = subprocess.run(argv, capture_output=True, timeout=PROBE_TIMEOUT_S, stdin=subprocess.DEVNULL, check=False)
    except subprocess.TimeoutExpired as e:
        raise FfmpegError(f"ffprobe exceeded {PROBE_TIMEOUT_S:g} s on {p.name}") from e
    err = done.stderr[-STDERR_CAP:].decode("utf-8", "replace").strip()
    if done.returncode != 0:
        raise FfmpegError(f"ffprobe could not read {p.name}: {err or 'no message'}")
    try:
        doc = json.loads(done.stdout.decode("utf-8", "replace"))
        stream = doc["streams"][0]
        fmt = doc.get("format", {})
    except (ValueError, KeyError, IndexError) as e:
        raise FfmpegError(f"ffprobe found no audio stream in {p.name}: {err or 'no message'}") from e
    names = str(fmt.get("format_name", "")).lower()
    container = p.suffix.lstrip(".").upper() if names == _MOV_FAMILY else names.split(",")[0].upper()
    duration = float(stream.get("duration") or fmt.get("duration") or 0.0)
    return FfprobeInfo(
        container=container or "UNKNOWN",
        codec=str(stream.get("codec_name", "unknown")),
        samplerate=int(stream.get("sample_rate") or 0),
        channels=int(stream.get("channels") or 0),
        duration_s=duration,
    )


def iter_blocks_ffmpeg(
    path: str | Path,
    tools: Ffmpeg,
    channels: int,
    duration_s: float,
    block_frames: int,
    dtype: str = "float64",
) -> Iterator[np.ndarray]:
    """Yield (frames, channels) float blocks decoded by ffmpeg, full scale 1.0, within a wall budget."""
    p = safe_path(path)
    if channels < 1:
        raise FfmpegError(f"{p.name}: no audio channels to decode")
    argv = [
        str(tools.ffmpeg),
        "-nostdin",
        "-v", "error",
        "-protocol_whitelist", "file,pipe",
        "-i", str(p),
        "-map", "0:a:0",
        "-f", "f32le",
        "-acodec", "pcm_f32le",
        "-",
    ]
    budget = decode_budget_s(duration_s)
    frame_bytes = 4 * channels
    want = block_frames * frame_bytes
    expired = threading.Event()
    with tempfile.TemporaryFile() as err:
        proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=err)
        assert proc.stdout is not None

        def on_budget() -> None:  # runs on the timer thread; the kill unblocks the read below
            expired.set()
            proc.kill()

        timer = threading.Timer(budget, on_budget)
        timer.daemon = True
        timer.start()
        try:
            carry = b""
            while True:
                chunk = proc.stdout.read(want - len(carry))
                if not chunk:
                    break
                carry += chunk
                whole = len(carry) - len(carry) % frame_bytes
                if whole == 0:
                    continue
                block, carry = carry[:whole], carry[whole:]
                yield np.frombuffer(block, dtype="<f4").reshape(-1, channels).astype(dtype, copy=False)
            if carry:
                whole = len(carry) - len(carry) % frame_bytes
                if whole:
                    yield np.frombuffer(carry[:whole], dtype="<f4").reshape(-1, channels).astype(dtype, copy=False)
            code = proc.wait(timeout=5)
            if expired.is_set():
                raise FfmpegError(f"ffmpeg exceeded its {budget:g} s budget on {p.name}")
            if code != 0:
                raise FfmpegError(f"ffmpeg exited {code} on {p.name}: {_tail(err) or 'no message'}")
        finally:
            timer.cancel()
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=5)
            proc.stdout.close()
```

Note for the implementer: `np.frombuffer(...).astype(dtype, copy=False)` returns a read-only view when `dtype` is float32; the meters only read blocks, and the float64 default copies. Keep it that way. The `assert proc.stdout is not None` is for the type checker; leave it. When the timer kills the child mid-read, `read()` returns what it has or an empty bytes object and the loop falls through to the `expired` check, which wins over the exit code (a killed child exits -9). `data:` and `concat:` are refused by `_SCHEME`; `C:relative.m4a` is refused because `_DRIVE` wants a separator after the colon.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_ffmpeg_io.py -v`
Expected: all PASS on this Mac (ffmpeg 9.0.1 on PATH). Then `uv run ruff check src tests && uv run ruff format src tests`.

- [ ] **Step 5: Commit**

```bash
git add src/cumple/io/ffmpeg.py tests/test_ffmpeg_io.py
git commit -m "Decode compressed deliveries through a local ffmpeg, behind a whitelist and a budget"
```

---

### Task 2: The reader falls back, the engine names the decoder

**Files:**
- Modify: `src/cumple/io/reader.py:40-90` (`AudioInfo`, `probe`), `:142-152` (`iter_blocks`)
- Modify: `src/cumple/meters/measure.py:192-201` (`measure`: pass `info` into `iter_blocks`)
- Modify: `src/cumple/report/json_out.py:43-48` (container, codec, decoder in the measurement block), `src/cumple/report/qc_sheet.py:139-143,168` (the format cell and the meta line name the container always and the depth when there is one)
- Modify: `src/cumple/checks/engine.py:370-392` (bit depth wording), `:453-478` (container mapping)
- Modify: `src/cumple/cli.py:264-266` (`info` prints the decoder)
- Test: `tests/test_ffmpeg_io.py` (append), `tests/test_reader.py` (append)

**Interfaces:**
- Consumes: from Task 1, `FFMPEG_SUFFIXES`, `find_ffmpeg`, `probe_ffmpeg`, `iter_blocks_ffmpeg`, `FfmpegError`.
- Produces: `AudioInfo.decoder: str = "libsndfile"`, `AudioInfo.codec: str | None = None`, `AudioInfo.via_ffmpeg`, `AudioInfo.is_pcm`; `iter_blocks(path, block_frames, dtype, info: AudioInfo | None = None)`; engine container tokens `MP3 -> mp3`, `M4A/MP4/MOV/AAC with codec aac -> aac`, `MXF -> mxf`, `AC3 -> ac3`, `EAC3 -> eac3`; JSON `measurement.container`, `measurement.codec`, `measurement.decoder`; the sheet's Format cell reads `48 kHz`, `24-bit WAV · stereo` or `AAC via ffmpeg 9.0.1 · stereo`.

- [ ] **Step 1: Write the failing tests**

Add these imports to the TOP import block of `tests/test_ffmpeg_io.py` (ruff's E402 rejects imports after code), keeping the block sorted the way ruff's isort wants:

```python
from typer.testing import CliRunner

from cumple.checks.engine import evaluate
from cumple.cli import app
from cumple.io.reader import iter_blocks, probe
from cumple.meters.measure import measure
from cumple.report import render_html
from cumple.report.json_out import report_to_dict
from cumple.specs import load_all
```

and `runner = CliRunner()` after `needs_ffmpeg = ...`. Then append these tests:

```python
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


def test_a_broken_wav_still_reports_libsndfiles_error_not_ffmpegs(tmp_path):
    bad = tmp_path / "broken.wav"
    bad.write_bytes(b"RIFF\x00\x00\x00\x00WAVEjunk")
    with pytest.raises(RuntimeError) as e:
        probe(bad)
    assert "ffmpeg" not in str(e.value).lower()
```

Append to `tests/test_reader.py`:

```python
def test_mp3_reads_through_libsndfile_and_says_so(tmp_path):
    """libsndfile 1.2 decodes MP3 itself; the fallback is never consulted for it, on any platform."""
    n = 48000
    t = np.arange(n) / 48000
    tone = 0.1 * np.sin(2 * np.pi * 1000 * t)
    mp3 = tmp_path / "tone.mp3"
    sf.write(str(mp3), np.repeat(tone[:, None], 2, axis=1), 48000, format="MP3", subtype="MPEG_LAYER_III")
    info = probe(mp3)
    assert info.container == "MP3" and info.decoder == "libsndfile" and info.codec is None
    assert info.bit_depth is None and not info.is_pcm
```

(Check the top of `tests/test_reader.py`: it needs `import numpy as np`, `import soundfile as sf` and `from cumple.io.reader import probe`; add whichever is missing to the import block, not after code.)

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_ffmpeg_io.py tests/test_reader.py -v`
Expected: the new tests FAIL (`probe` raises `LibsndfileError` on the M4A; `iter_blocks` rejects `info=`; `AudioInfo` has no `decoder`; `report_to_dict` has no `container` key; the sheet prints nothing for the MP3's format).

- [ ] **Step 3: Implement the fallback**

In `src/cumple/io/reader.py`:

Replace the `AudioInfo` dataclass with:

```python
@dataclass(frozen=True)
class AudioInfo:
    """What we know about a file before reading any samples."""

    path: Path
    container: str  # WAV, WAVEX, RF64, AIFF, FLAC, MP3; M4A, MXF, AC3 ... when ffmpeg decoded it
    subtype: str  # PCM_24, FLOAT, MPEG_LAYER_III; AAC, AC3 ... when ffmpeg decoded it
    samplerate: int
    channels: int
    frames: int
    metadata: dict[str, Any] = field(default_factory=dict)
    decoder: str = "libsndfile"  # or "ffmpeg 9.0.1"
    codec: str | None = None  # ffprobe's codec name when ffmpeg decoded it

    @property
    def duration_s(self) -> float:
        return self.frames / self.samplerate if self.samplerate else 0.0

    @property
    def bit_depth(self) -> int | None:
        return SUBTYPE_BITS.get(self.subtype)

    @property
    def is_float(self) -> bool:
        return self.subtype in FLOAT_SUBTYPES

    @property
    def is_pcm(self) -> bool:
        return self.subtype in SUBTYPE_BITS

    @property
    def via_ffmpeg(self) -> bool:
        return self.decoder.startswith("ffmpeg")

    @property
    def bext(self) -> dict[str, Any]:
        return self.metadata.get("bext", {})
```

Replace `probe` with:

```python
def probe(path: str | Path) -> AudioInfo:
    """Open the file header and return its shape plus any embedded BWF metadata.

    libsndfile first. When it refuses a file whose suffix names a compressed or wrapped delivery
    and a local ffmpeg exists, ffprobe supplies the shape and the report names the decoder.
    """
    path = Path(path)
    try:
        with sf.SoundFile(str(path)) as f:
            container = f.format
            return AudioInfo(
                path=path,
                container=container,
                subtype=f.subtype,
                samplerate=f.samplerate,
                channels=f.channels,
                frames=f.frames,
                metadata=read_metadata(path, container),
            )
    except sf.LibsndfileError as e:
        if path.suffix.lower() not in FFMPEG_SUFFIXES:
            raise
        tools = find_ffmpeg()
        if tools is None:
            raise RuntimeError(
                f"{path.name}: libsndfile cannot open this container; install ffmpeg (and ffprobe) "
                "to check compressed and wrapped deliveries, or point CUMPLE_FFMPEG at it"
            ) from e
    try:
        pi = probe_ffmpeg(path, tools)
    except FfmpegError as e:
        raise RuntimeError(str(e)) from e
    return AudioInfo(
        path=path,
        container=pi.container,
        subtype=pi.subtype,
        samplerate=pi.samplerate,
        channels=pi.channels,
        frames=int(round(pi.duration_s * pi.samplerate)),
        decoder=f"ffmpeg {tools.version}",
        codec=pi.codec,
    )
```

Add the import near the top, after `import soundfile as sf`:

```python
from .ffmpeg import FFMPEG_SUFFIXES, FfmpegError, find_ffmpeg, iter_blocks_ffmpeg, probe_ffmpeg
```

Replace `iter_blocks` with:

```python
def iter_blocks(
    path: str | Path,
    block_frames: int = DEFAULT_BLOCK_FRAMES,
    dtype: str = "float64",
    info: AudioInfo | None = None,
) -> Iterator[np.ndarray]:
    """Yield (frames, channels) float blocks. Full scale is 1.0 for every subtype.

    Pass the AudioInfo that probe() returned: when it names ffmpeg as the decoder, the blocks come
    from ffmpeg; otherwise from libsndfile.
    """
    if info is not None and info.via_ffmpeg:
        tools = find_ffmpeg()
        if tools is None:
            raise RuntimeError(f"{Path(path).name} was probed through ffmpeg, which is no longer on PATH")
        try:
            yield from iter_blocks_ffmpeg(path, tools, info.channels, info.duration_s, block_frames, dtype)
        except FfmpegError as e:
            raise RuntimeError(str(e)) from e
        return
    yield from sf.blocks(str(path), blocksize=block_frames, dtype=dtype, always_2d=True)
```

In `src/cumple/meters/measure.py`, inside `measure` (around line 199): change `iter_blocks(path, block_frames),` to `iter_blocks(path, block_frames, info=info),`.

In `src/cumple/report/json_out.py`, the `"measurement"` dict (line 43): add three keys right after `"samplerate": m.samplerate,`:

```python
            "container": m.info.container if m.info else None,
            "codec": m.info.codec if m.info else None,
            "decoder": m.info.decoder if m.info else None,
```

In `src/cumple/report/qc_sheet.py`, add one helper near `_mmss` (line 40):

```python
def _encoding(m) -> str:
    """"24-bit WAV", "AAC via ffmpeg 9.0.1", or "" when nothing is known about the file."""
    i = m.info
    if i is None:
        return ""
    if i.bit_depth:
        return f"{i.bit_depth}-bit {i.container}"
    codec = (i.codec or i.subtype).upper()
    return f"{codec} via {i.decoder}" if i.via_ffmpeg else f"{codec} {i.container}"
```

then change the Format strip cell (line 142) from
`(f"{m.info.bit_depth}-bit · " if m.info and m.info.bit_depth else "") + m.layout,`
to
`(f"{_encoding(m)} · " if _encoding(m) else "") + m.layout,`
and the meta line's `depth` (line 168) from
`depth = (", " + str(m.info.bit_depth) + "-bit " + _esc(m.info.container)) if m.info and m.info.bit_depth else ""`
to
`depth = (", " + _esc(_encoding(m))) if _encoding(m) else ""`.
Run `uv run pytest tests/test_qc_sheet.py tests/test_pdf.py -q` after: the existing sheet tests must still pass (a WAV renders "24-bit WAV" where it rendered "24-bit WAV" before).

In `src/cumple/checks/engine.py`, the bit-depth finding (around line 370): replace the block that computes `ok` and `measured` with:

```python
    if f.bit_depths and info is not None:
        depth = info.bit_depth
        if info.is_float:
            ok = f.allow_float
            measured = f"{depth}-bit float"
        elif depth is None:
            ok = False
            what = info.codec or info.subtype.lower()
            measured = f"not PCM ({what})"
        else:
            ok = depth in f.bit_depths
            measured = f"{depth}-bit"
```

and keep the `Finding(...)` that follows unchanged (its `value=float(depth or 0)` already tolerates None).

In the container finding (around line 453), replace the mapping and the measured text:

```python
    if f.containers and info is not None:
        name = {
            "WAV": "wav",
            "WAVEX": "wav",
            "RF64": "rf64",
            "W64": "rf64",
            "AIFF": "aiff",
            "AIFC": "aiff",
            "FLAC": "flac",
            "MP3": "mp3",
            "MXF": "mxf",
            "AC3": "ac3",
            "EAC3": "eac3",
        }.get(info.container, info.container.lower())
        if info.codec == "aac" and name in ("m4a", "mp4", "mov", "aac"):
            name = "aac"
        have = {name}
        if name == "wav" and info.bext:
            have.add("bwf")
        if name == "rf64":
            have.add("bwf")
        ok = bool(have & set(f.containers))
        measured = info.container + (" with bext" if info.bext else "")
        if info.via_ffmpeg:
            measured += f", {info.codec}, decoded by {info.decoder}"
        out.append(
            Finding(
                "format.container",
                Status.PASS if ok else Status.FAIL,
                "container",
                measured,
                ", ".join(f.containers),
                clause=clause("format.container"),
            )
        )
```

In `src/cumple/cli.py`, the `info` command (around line 264), after `table.add_row("container", i.container)` add:

```python
    if i.via_ffmpeg:
        table.add_row("decoder", f"{i.codec}, decoded by {i.decoder}")
```

and change the encoding row to:

```python
    depth = f"{i.bit_depth}-bit" if i.bit_depth is not None else "not PCM"
    table.add_row("encoding", f"{i.subtype} ({'float' if i.is_float else 'integer'}, {depth})")
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_ffmpeg_io.py tests/test_reader.py tests/test_engine.py tests/test_cli_edges.py tests/test_qc_sheet.py tests/test_app.py -v`
Expected: all PASS. Then the whole suite: `uv run pytest` (expect the previous count plus the new tests, all green) and `uv run ruff check src tests && uv run ruff format src tests`.

- [ ] **Step 5: Commit**

```bash
git add src/cumple/io/reader.py src/cumple/meters/measure.py src/cumple/checks/engine.py src/cumple/cli.py src/cumple/report/json_out.py src/cumple/report/qc_sheet.py tests/test_ffmpeg_io.py tests/test_reader.py
git commit -m "Fall back to ffmpeg when libsndfile refuses a delivery, and name the decoder in the report"
```

---

### Task 3: CI runs the decode tests on Linux; the docs say what is read now

**Files:**
- Modify: `.github/workflows/tests.yml:16-32`
- Modify: `README.md:456-461` (the codec limit line in Honest limits), `README.md:108` area if a one-line note under `info` fits
- Modify: `site/index.html:219` (JSON-LD answer) and `:401` (the FAQ answer), which `tests/test_site.py` holds equal
- Modify: `docs/ROADMAP.md` (R2 row), `AI_USAGE.md` (one paragraph at the end of "The competitive landscape" section or a new short section)
- Modify: counts in README.md, CONTRIBUTING.md, docs/QA.md, AI_USAGE.md, site/index.html
- Test: `tests/test_site.py` (existing; the JSON-LD twin test), `tests/test_counts.py` (existing)

**Interfaces:**
- Consumes: the behaviour from Task 2.
- Produces: nothing for later tasks.

- [ ] **Step 1: Add the ffmpeg step to the Linux CI job**

In `.github/workflows/tests.yml`, inside the `test` job's steps, after the `Install` step and before `Lint`, add:

```yaml
      - name: Install ffmpeg (the decode tests run only where it exists)
        if: runner.os == 'Linux'
        run: |
          sudo apt-get update -qq
          sudo apt-get install -y -qq ffmpeg
          ffmpeg -version | head -1
```

and change the comment above the `Test` step (lines 29-30) to:

```yaml
        # The 29 EBU conformance cases skip here: the EBU test set is free but not redistributed;
        # the conformance job below runs them when the repository holds a link to a copy. The
        # ffmpeg-gated decode tests run on Linux, where the step above installs ffmpeg, and skip
        # on macOS and Windows.
```

- [ ] **Step 2: Reword the README limit**

Replace the bullet at `README.md:458-459` ("Reads what libsndfile reads: WAV, BWF, RF64, AIFF, FLAC, and others. It does not decode delivery codecs (AAC, AC-3, MP3) or MXF; check the master.") with:

```markdown
- Reads what libsndfile reads: WAV, BWF, RF64, AIFF, FLAC and MP3. With a
  local ffmpeg (`ffmpeg` and `ffprobe` on PATH, or `CUMPLE_FFMPEG`) it also
  decodes AAC, AC-3 and E-AC-3 and the audio of MXF, MOV and MP4 files, so a
  compressed delivery is measured and its container fails the destination's
  clause instead of the tool refusing to open it; the report names the decoder.
  Without ffmpeg those files are refused with a message that says so. `diff`
  and `fix` still need PCM files.
```

Read the surrounding bullets first and keep the line width they use.

- [ ] **Step 3: Update the FAQ answer and its JSON-LD twin**

In `site/index.html`, the `<details>` whose summary is "Which files does it read?" (line 401) and the JSON-LD `Question` with the same name (line 219) both carry this answer today:

```
WAV, BWF, RF64, AIFF and FLAC, mono to 7.1 and packages of discrete mono files. Not AAC, AC-3, MP3 or MXF, and no Dolby Atmos or ADM checks yet. Check the master.
```

Replace it in both places with exactly these words:

```
WAV, BWF, RF64, AIFF, FLAC and MP3, mono to 7.1 and packages of discrete mono files. With a local ffmpeg it also decodes AAC, AC-3 and E-AC-3 and the audio of MXF, MOV and MP4 files, and the report names the decoder; diff and fix still need PCM files. No Dolby Atmos or ADM checks yet.
```

The JSON-LD string must equal the visible text character for character (`tests/test_site.py::test_faq_json_ld_repeats_the_visible_answers` checks it).

- [ ] **Step 4: ROADMAP and AI_USAGE**

In `docs/ROADMAP.md`, change the R2 row's Status cell from `proposed for this loop` to `building` now, and in Task 4's docs step to `merged` with the PR number; the Receipt cell gets `docs/graph-runs/2026-09-12-ffmpeg-codec-conformance/05-receipt.md` when the receipt exists (the receipt is written by the main session after the PR opens; leave the cell empty in this task).

In `AI_USAGE.md`, append a section:

```markdown
## Compressed deliveries (12 September)

The roadmap's second item. A finding on the way in: libsndfile 1.2.2 already
reads MP3, so the README's line that cumple "does not decode MP3" had been
wrong since the soundfile wheel bundled it; the line now says what is read
natively and what needs ffmpeg. The ffmpeg wrapper is one module that never
builds a command from user text beyond the resolved file path, closes stdin,
whitelists the file protocol, keeps a wall budget of ten times the duration
plus a minute, and caps what it keeps of ffmpeg's error output; a reviewer
with the security checklist read it before merge. The decode tests run on
this Mac and on the Linux CI runner, which installs ffmpeg with apt; the
macOS and Windows jobs skip them.
```

- [ ] **Step 5: Re-pin the counts, and say where the decode tests run**

Run: `uv run pytest --collect-only 2>/dev/null | grep 'tests collected'` and put that number in the five places (`**Tests**: N,` in README, `# N tests;` in CONTRIBUTING, `` `uv run pytest`, N tests`` in docs/QA.md, `N tests, including` in AI_USAGE, `N tests with 91 %` in site/index.html).

Then count the ffmpeg-gated tests by running the two files with ffmpeg hidden (PATH without Homebrew, uv by its full path):

`PATH=/usr/bin:/bin ~/.local/bin/uv run pytest tests/test_ffmpeg_io.py tests/test_reader.py -rs -q 2>&1 | grep -c "ffmpeg and ffprobe are not on PATH"`

That number is G. README.md:413-414 currently reads "CI runs 171 of them on Ubuntu, macOS and Windows on every push. The 29 EBU cases ...". Rewrite it (keeping the regex shape `runs (\d+) of them on Ubuntu` that tests/test_counts.py matches) to:

`runs N-29 of them on Ubuntu, and G fewer on macOS and Windows, which have no ffmpeg for the decode tests, on every push. The 29 EBU cases ...` with N-29 and G as digits.

- [ ] **Step 6: Run the suite and the site tests**

Run: `uv run pytest`
Expected: all green, count matches. `uv run ruff check src tests scripts && uv run ruff format --check src tests scripts`. `grep -n '[—–]' README.md site/index.html AI_USAGE.md docs/ROADMAP.md` prints nothing.

- [ ] **Step 7: Commit**

```bash
git add .github/workflows/tests.yml README.md site/index.html docs/ROADMAP.md AI_USAGE.md CONTRIBUTING.md docs/QA.md
git commit -m "Say which files are read natively and which through ffmpeg, and run the decode tests on Linux CI"
```

---

### Task 4: Re-pin the benchmark to the ffmpeg on this machine

**Files:**
- Regenerate: `docs/BENCHMARK.md` (by `scripts/benchmark_meters.py`)
- Modify: `docs/RELATED.md:29-35` (the ffmpeg ebur128 and loudcheck sections: which ffmpeg produced the run and when), and the first table's ffmpeg or loudcheck "in our run" cells only if the run's summary lines changed
- Modify: `site/index.html` only where `tests/test_site_numbers.py` says a derived figure changed
- Modify: `docs/ROADMAP.md` ("Open for Victor" section: the ffmpeg question is closed; R2 row status)
- Test: `tests/test_site_numbers.py` (existing)

**Interfaces:** none.

- [ ] **Step 1: Confirm the inputs the script needs**

Run: `ls ~/.cache/cumple/ebu-loudness-test-set | head -3 && ffmpeg -version | head -1 && brew --prefix libebur128 && uv run python -c "import loudcheck, pyloudnorm; print('ok')"`
Expected: the EBU files are present, ffmpeg 9.0.1, a libebur128 prefix, `ok`. If libebur128 is missing: `brew install libebur128` is allowed (it does not touch ffmpeg; confirm with `brew deps libebur128`).

- [ ] **Step 2: Regenerate the report**

Run: `uv run python scripts/benchmark_meters.py > /private/tmp/claude-501/-Users-Victor/8532c3f4-e22f-43f1-a095-493e2c73d608/scratchpad/BENCHMARK.new.md && diff docs/BENCHMARK.md /private/tmp/claude-501/-Users-Victor/8532c3f4-e22f-43f1-a095-493e2c73d608/scratchpad/BENCHMARK.new.md`
Expected: the header line changes (date and ffmpeg version); the readings either match to the hundredth or differ on a few rows. Record the diff in the commit message. Then copy the new report over `docs/BENCHMARK.md`.

- [ ] **Step 3: Update RELATED.md's two sections**

In the `## ffmpeg ebur128` section, after "Version checked: ffmpeg 8.0.", add: "Run again on 12 September 2026 with ffmpeg 9.0.1 (a Homebrew dependency upgraded the machine's ffmpeg during the competitive-landscape research); BENCHMARK.md is that run, and <its readings match the 8.0 run to the hundredth | it differs on N rows, listed there>." Choose the true clause from Step 2's diff. In the `## loudcheck` section add the same sentence shape (loudcheck measures through the ffmpeg on PATH). Do not change the "Read on 8 September 2026" source reads: the source was read then and is still the source.

- [ ] **Step 4: Run the derived-figure tests**

Run: `uv run pytest tests/test_site_numbers.py tests/test_related.py -v`
Expected: PASS if the summary lines did not change. If a "N of M readings in our run" cell or the largest-gap figure changed, the test names the page cell; update `docs/RELATED.md`'s first table cell and `site/index.html` to the new true value (both, they are held equal), and say so in the commit.

- [ ] **Step 5: Close the ffmpeg question in the roadmap**

In `docs/ROADMAP.md`, replace the "## Open for Victor" section body with: "Closed 12 September: Victor chose to accept the machine's ffmpeg 9.0.1 (exact 8.0 was not restorable; its libraries had been upgraded) and the benchmark was re-run and re-pinned in PR <number>." Keep the heading. Set R2's Status to `merged` and its PR cell to the PR number once the main session gives it (leave `building` if the number is not known yet).

- [ ] **Step 6: Run everything and commit**

Run: `uv run pytest` then `uv run ruff check src tests scripts && uv run ruff format --check src tests scripts` and `grep -n '[—–]' docs/RELATED.md docs/BENCHMARK.md docs/ROADMAP.md site/index.html`.
Expected: green, formatted, no dashes.

```bash
git add docs/BENCHMARK.md docs/RELATED.md docs/ROADMAP.md site/index.html
git commit -m "Re-run the benchmark with the ffmpeg on this machine and say which one it was"
```
