# ffmpeg codec and container conformance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A compressed or wrapped delivery (AAC in M4A/MP4/MOV, AC-3, E-AC-3, the audio of an MXF) is decoded by a local ffmpeg when one is installed, measured exactly as a WAV is, and reported with the decoder named, so the destination's container clause fails on the file itself instead of the tool refusing to open it.

**Architecture:** One new read-only module `src/cumple/io/ffmpeg.py` wraps `ffprobe` (JSON probe) and `ffmpeg` (raw float32 stream on stdout) behind argv lists with stdin closed, a protocol whitelist, timeouts and a bounded stderr. `reader.probe` falls back to it when libsndfile refuses a file whose suffix is in `FFMPEG_SUFFIXES`; `reader.iter_blocks` streams through it when the `AudioInfo` says so; `AudioInfo` gains `decoder` and `codec`. The engine's container mapping learns the new tokens and the bit-depth finding says "not PCM" instead of "None-bit". libsndfile 1.2.2 already reads MP3 natively (format token `MP3`), so MP3 needs no fallback and the docs say so.

**Tech Stack:** Python 3.12, numpy, soundfile (libsndfile 1.2.2), subprocess; ffmpeg 9.0.1 on this Mac, apt ffmpeg on the CI Linux runner. No new dependency.

**Spec:** `docs/graph-runs/2026-09-12-ffmpeg-codec-conformance/01-frame.md` (the capability contract and constraints).

## Global Constraints

- No new runtime dependency. `pyproject.toml` dependencies stay as they are.
- Every subprocess call: an argv list, `stdin=subprocess.DEVNULL`, `-nostdin` for ffmpeg, `-protocol_whitelist file` (ffprobe) or `file,pipe` (ffmpeg), a timeout, stderr capped at 4096 bytes, no option built from user text other than the resolved absolute path.
- Paths handed to ffmpeg are absolute, resolved, regular files; a path matching `^[A-Za-z][A-Za-z0-9+.\-]+:` is refused unless it is a Windows drive prefix `^[A-Za-z]:[\\/]`.
- Tests that need ffmpeg skip with `pytest.mark.skipif(find_ffmpeg() is None, reason=...)`; nothing in the suite requires ffmpeg.
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
- Produces: `FFMPEG_SUFFIXES: set[str]`; `class Ffmpeg(ffmpeg: Path, ffprobe: Path, version: str)`; `find_ffmpeg() -> Ffmpeg | None`; `safe_path(path) -> Path`; `class FfprobeInfo(container: str, codec: str, samplerate: int, channels: int, duration_s: float)` with property `subtype -> str`; `probe_ffmpeg(path, tools: Ffmpeg) -> FfprobeInfo`; `iter_blocks_ffmpeg(path, tools: Ffmpeg, channels: int, duration_s: float, block_frames: int, dtype: str) -> Iterator[np.ndarray]`; `class FfmpegError(RuntimeError)`; `decode_budget_s(duration_s: float) -> float`.

- [ ] **Step 1: Write the failing tests**

```python
"""ffmpeg is optional: when it is on the machine, compressed deliveries decode; when it is not, nothing here runs."""

from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from cumple.io.ffmpeg import (
    FFMPEG_SUFFIXES,
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
    for bad in ("http://example.com/a.m4a", "concat:a.wav|b.wav", "subfile,,start,0,,:x.wav", "data:audio/aac;base64,AAAA"):
        with pytest.raises(ValueError):
            safe_path(bad)
    with pytest.raises(ValueError):
        safe_path(tmp_path)  # a directory
    with pytest.raises(ValueError):
        safe_path(tmp_path / "missing.m4a")


def test_safe_path_accepts_a_windows_drive_prefix_shape(tmp_path, make_wav):
    # The scheme regex must not mistake "C:\..." for a protocol. The file must still exist, so
    # the check is on the regex alone, through a path that resolves on this machine.
    from cumple.io.ffmpeg import _DRIVE, _SCHEME

    assert _SCHEME.match("C:\\bounce\\mix.m4a") and _DRIVE.match("C:\\bounce\\mix.m4a")
    assert _SCHEME.match("concat:a|b") and not _DRIVE.match("concat:a|b")


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


@needs_ffmpeg
def test_decoding_stops_when_the_budget_expires(aac_file, monkeypatch):
    import cumple.io.ffmpeg as mod

    monkeypatch.setattr(mod, "DECODE_BUDGET_FACTOR", 0.0)
    monkeypatch.setattr(mod, "DECODE_BUDGET_FLOOR_S", 0.0)
    info = probe_ffmpeg(aac_file, TOOLS)
    with pytest.raises(FfmpegError) as e:
        list(iter_blocks_ffmpeg(aac_file, TOOLS, info.channels, info.duration_s, block_frames=8192, dtype="float64"))
    assert "budget" in str(e.value)


@needs_ffmpeg
def test_the_version_is_read_from_the_binary():
    assert TOOLS.version[0].isdigit()


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

import json
import os
import re
import shutil
import subprocess
import tempfile
import time
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
_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]+:")
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
    """The ffmpeg and ffprobe pair under CUMPLE_FFMPEG (a directory or the ffmpeg binary), else on PATH."""
    candidates: list[Path] = []
    hint = os.environ.get("CUMPLE_FFMPEG")
    if hint:
        p = Path(hint)
        candidates.append(p if p.is_file() else p / "ffmpeg")
    found = shutil.which("ffmpeg")
    if found:
        candidates.append(Path(found))
    for exe in candidates:
        exe = exe.resolve()
        probe = exe.with_name("ffprobe" + exe.suffix)
        if exe.is_file() and probe.is_file():
            return Ffmpeg(exe, probe, _version(exe))
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
    started = time.monotonic()
    frame_bytes = 4 * channels
    want = block_frames * frame_bytes
    with tempfile.TemporaryFile() as err:
        proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=err)
        assert proc.stdout is not None
        try:
            carry = b""
            while True:
                if time.monotonic() - started > budget:
                    proc.kill()
                    raise FfmpegError(f"ffmpeg exceeded its {budget:g} s budget on {p.name}")
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
            code = proc.wait(timeout=max(1.0, budget - (time.monotonic() - started)))
            if code != 0:
                raise FfmpegError(f"ffmpeg exited {code} on {p.name}: {_tail(err) or 'no message'}")
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=5)
```

Note for the implementer: `np.frombuffer(...).astype(dtype, copy=False)` returns a read-only view when `dtype` is float32; the meters only read blocks, and the float64 default copies. Keep it that way. The `assert proc.stdout is not None` is for the type checker; leave it.

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
- Modify: `src/cumple/meters/measure.py:192-201` (pass `info` into `iter_blocks`)
- Modify: `src/cumple/checks/engine.py:370-392` (bit depth wording), `:453-478` (container mapping)
- Modify: `src/cumple/cli.py:264-266` (`info` prints the decoder)
- Test: `tests/test_ffmpeg_io.py` (append), `tests/test_reader.py` (append)

**Interfaces:**
- Consumes: from Task 1, `FFMPEG_SUFFIXES`, `find_ffmpeg`, `probe_ffmpeg`, `iter_blocks_ffmpeg`, `FfmpegError`.
- Produces: `AudioInfo.decoder: str = "libsndfile"`, `AudioInfo.codec: str | None = None`; `iter_blocks(path, block_frames, dtype, info: AudioInfo | None = None)`; engine container tokens `MP3 -> mp3`, `M4A/MP4/MOV/AAC with codec aac -> aac`, `MXF -> mxf`, `AC3 -> ac3`, `EAC3 -> eac3`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_ffmpeg_io.py`:

```python
from typer.testing import CliRunner

from cumple.checks.engine import evaluate
from cumple.cli import app
from cumple.io.reader import iter_blocks, probe
from cumple.meters.measure import measure_file
from cumple.specs import load_all

runner = CliRunner()


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
    a = measure_file(aac_file)
    w = measure_file(wav)
    assert abs(a.loudness.integrated - w.loudness.integrated) < 0.5
    assert a.info is not None and a.info.decoder.startswith("ffmpeg ")


@needs_ffmpeg
def test_netflix_fails_the_container_and_names_the_codec_and_acx_bit_depth_says_not_pcm(aac_file):
    profiles = load_all()
    report = evaluate(profiles["netflix-2.0"], measure_file(aac_file))
    container = next(f for f in report.findings if f.code == "format.container")
    assert container.status.name == "FAIL"
    assert "M4A" in container.measured and "aac" in container.measured and "ffmpeg" in container.measured
    assert "compression is never allowed" in (container.clause or "")
    depth = next(f for f in report.findings if f.code == "format.bit_depth")
    assert depth.status.name == "FAIL" and "not PCM" in depth.measured and "None" not in depth.measured


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
def test_mp3_reads_through_libsndfile_and_says_so(make_wav, tmp_path):
    """libsndfile 1.2 decodes MP3 itself; the fallback is never consulted for it."""
    import shutil
    import subprocess

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        pytest.skip("ffmpeg is needed only to write the MP3 fixture")
    wav = make_wav("tone.wav", seconds=1.0)
    mp3 = tmp_path / "tone.mp3"
    subprocess.run([ffmpeg, "-y", "-nostdin", "-v", "error", "-i", str(wav), "-c:a", "libmp3lame", str(mp3)], check=True, timeout=60)
    info = probe(mp3)
    assert info.container == "MP3" and info.decoder == "libsndfile" and info.codec is None
```

(`tests/test_reader.py` already imports `probe` and `pytest`; check the top of the file and add `import pytest` if it is missing.)

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_ffmpeg_io.py tests/test_reader.py -v`
Expected: the new tests FAIL (`probe` raises `LibsndfileError` on the M4A; `iter_blocks` rejects `info=`; `AudioInfo` has no `decoder`).

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

In `src/cumple/meters/measure.py`, `measure_file` (around line 199): change `iter_blocks(path, block_frames),` to `iter_blocks(path, block_frames, info=info),`.

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

Run: `uv run pytest tests/test_ffmpeg_io.py tests/test_reader.py tests/test_engine.py tests/test_cli_edges.py -v`
Expected: all PASS. Then the whole suite: `uv run pytest` (expect the previous count plus the new tests, all green) and `uv run ruff check src tests && uv run ruff format src tests`.

- [ ] **Step 5: Commit**

```bash
git add src/cumple/io/reader.py src/cumple/meters/measure.py src/cumple/checks/engine.py src/cumple/cli.py tests/test_ffmpeg_io.py tests/test_reader.py
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
WAV, BWF, RF64, AIFF, FLAC and MP3, mono to 7.1 and packages of discrete mono files. With a local ffmpeg it also decodes AAC, AC-3 and E-AC-3 and the audio of MXF, MOV and MP4 files, and the report names the decoder. No Dolby Atmos or ADM checks yet.
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

- [ ] **Step 5: Re-pin the counts**

Run: `uv run pytest --collect-only 2>/dev/null | grep 'tests collected'` and put that number in the five places (`**Tests**: N,` in README, `# N tests;` in CONTRIBUTING, `` `uv run pytest`, N tests`` in docs/QA.md, `N tests, including` in AI_USAGE, `N tests with 91 %` in site/index.html) and `runs N-29 of them on Ubuntu` in README.

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
