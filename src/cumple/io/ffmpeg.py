"""Decode compressed and wrapped deliveries through a local ffmpeg, when one is installed.

ffmpeg is optional. Nothing here runs unless libsndfile refused the file, and every call is an
argument list to a resolved executable with stdin closed, a protocol whitelist, a timeout and a
bounded error buffer. Read-only, like the rest of the io package: no file is written.
"""

from __future__ import annotations

import functools
import json
import os
import re
import shutil
import signal
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


def _search_path() -> str:
    """PATH as the environment gives it; passed explicitly so Windows does not prepend the current directory."""
    return os.environ.get("PATH", os.defpath)


def find_ffmpeg() -> Ffmpeg | None:
    """The ffmpeg and ffprobe pair under CUMPLE_FFMPEG (a directory or the ffmpeg binary), else on PATH.

    Cached per environment: one `ffmpeg -version` per process, not one per file.
    """
    return _locate(os.environ.get("CUMPLE_FFMPEG") or "", shutil.which("ffmpeg", path=_search_path()) or "")


@functools.lru_cache(maxsize=8)
def _locate(hint: str, on_path: str) -> Ffmpeg | None:
    pairs: list[tuple[str | None, str | None]] = []
    if hint:
        p = Path(hint)
        directory = str(p.parent if p.is_file() else p)
        pairs.append((shutil.which("ffmpeg", path=directory), shutil.which("ffprobe", path=directory)))
    if on_path:
        pairs.append((on_path, shutil.which("ffprobe", path=_search_path())))
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
    """Container, codec and shape of the file's one audio stream, from ffprobe's JSON.

    A file with no audio stream, or with more than one, is refused with the count named: cumple
    measures one interleaved stream, and picking the first of several would measure the wrong thing
    silently.
    """
    p = safe_path(path)
    argv = [
        str(tools.ffprobe),
        "-v",
        "error",
        "-protocol_whitelist",
        "file",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
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
        streams = [s for s in doc.get("streams", []) if s.get("codec_type") == "audio"]
        fmt = doc.get("format", {})
    except (ValueError, AttributeError) as e:
        raise FfmpegError(f"ffprobe returned unreadable JSON for {p.name}: {err or 'no message'}") from e
    if not streams:
        raise FfmpegError(f"ffprobe found no audio stream in {p.name}: {err or 'no message'}")
    if len(streams) > 1:
        raise FfmpegError(
            f"{p.name} carries {len(streams)} audio streams; cumple reads a single interleaved stream, "
            "bounce the programme as one WAV or one-track MXF first"
        )
    stream = streams[0]
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
    if block_frames < 1:
        raise FfmpegError(f"{p.name}: block_frames must be at least 1")
    # The probe refused any file with more than one audio stream, so a:0 is the only one there is.
    argv = [
        str(tools.ffmpeg),
        "-nostdin",
        "-v",
        "error",
        "-protocol_whitelist",
        "file,pipe",
        "-i",
        str(p),
        "-map",
        "0:a:0",
        "-f",
        "f32le",
        "-acodec",
        "pcm_f32le",
        "-",
    ]
    budget = decode_budget_s(duration_s)
    frame_bytes = 4 * channels
    want = block_frames * frame_bytes
    expired = threading.Event()
    with tempfile.TemporaryFile() as err:
        # Its own session on POSIX, so a wrapper script's children die with it and the pipe closes.
        proc = subprocess.Popen(
            argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=err, start_new_session=(os.name != "nt")
        )
        assert proc.stdout is not None

        def on_budget() -> None:  # runs on the timer thread; the kill unblocks the read below
            expired.set()
            if proc.poll() is None:
                _kill(proc)

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
            # carry is shorter than one frame here: a trailing partial frame was dropped inside the loop.
            code = proc.wait(timeout=5)
            if expired.is_set():
                raise FfmpegError(f"ffmpeg exceeded its {budget:g} s budget on {p.name}")
            if code != 0:
                raise FfmpegError(f"ffmpeg exited {code} on {p.name}: {_tail(err) or 'no message'}")
        finally:
            timer.cancel()
            if proc.poll() is None:
                _kill(proc)
                proc.wait(timeout=5)
            proc.stdout.close()


def _kill(proc: subprocess.Popen) -> None:
    """Kill the child and, on POSIX, everything in the session it started."""
    if os.name != "nt":
        try:
            os.killpg(proc.pid, signal.SIGKILL)
            return
        except ProcessLookupError:
            return
        except PermissionError:
            pass
    proc.kill()
