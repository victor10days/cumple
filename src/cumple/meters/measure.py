"""One pass over a file (or a package of discrete channel files) that feeds every meter."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

import numpy as np
import soundfile as sf

from ..io.reader import DEFAULT_BLOCK_FRAMES, AudioInfo, Package, iter_blocks, probe
from .bs1770 import LoudnessMeter, LoudnessResult, default_roles
from .truepeak import PeakMeter, PeakResult, to_db

SILENCE_DBFS = -80.0  # below this, a sample counts as padding / digital black
SMPTE_ORDER = ["L", "R", "C", "LFE", "Ls", "Rs", "Lrs", "Rrs"]


@dataclass
class Measurement:
    path: Path
    samplerate: int
    channels: int
    roles: list[str]
    duration_s: float
    loudness: LoudnessResult
    peaks: PeakResult
    dc_offset: np.ndarray  # linear, per channel
    head_silence_s: float
    tail_silence_s: float
    phase_correlation: float | None = None  # stereo only
    mono_fold_loudness: float | None = None  # loudness of (L+R)/2, stereo only
    speech_fraction: float | None = None  # not measured yet (lands with the dialogue gate)
    info: AudioInfo | None = None
    package: Package | None = None
    extra: dict = field(default_factory=dict)

    @property
    def is_package(self) -> bool:
        return self.package is not None

    @property
    def layout(self) -> str:
        roles = set(self.roles)
        if roles == {"M"} or self.channels == 1:
            return "mono"
        if roles == {"Lt", "Rt"}:
            return "lt-rt"
        if self.channels == 2:
            return "stereo"
        if roles >= {"L", "R", "C", "LFE", "Ls", "Rs", "Lrs", "Rrs"}:
            return "7.1"
        if roles >= {"L", "R", "C", "LFE", "Ls", "Rs"}:
            return "5.1"
        return f"{self.channels}ch"


class _Stats:
    """DC offset, head/tail silence, stereo correlation. Streaming, one pass."""

    def __init__(self, samplerate: int, channels: int):
        self.fs = samplerate
        self.ch = channels
        self.sum = np.zeros(channels)
        self.n = 0
        self.thr = 10 ** (SILENCE_DBFS / 20)
        self.first_loud: int | None = None
        self.last_loud: int | None = None
        self.lr = 0.0
        self.ll = 0.0
        self.rr = 0.0

    def feed(self, x: np.ndarray) -> None:
        n = x.shape[0]
        self.sum += x.sum(axis=0)
        loud = np.flatnonzero(np.abs(x).max(axis=1) >= self.thr)
        if loud.size:
            if self.first_loud is None:
                self.first_loud = self.n + int(loud[0])
            self.last_loud = self.n + int(loud[-1])
        if self.ch == 2:
            l, r = x[:, 0], x[:, 1]
            self.lr += float(l @ r)
            self.ll += float(l @ l)
            self.rr += float(r @ r)
        self.n += n

    def dc(self) -> np.ndarray:
        return self.sum / max(self.n, 1)

    def head_tail(self) -> tuple[float, float]:
        if self.first_loud is None:
            return self.n / self.fs, 0.0
        return self.first_loud / self.fs, (self.n - 1 - self.last_loud) / self.fs

    def correlation(self) -> float | None:
        if self.ch != 2 or self.ll <= 0 or self.rr <= 0:
            return None
        return self.lr / np.sqrt(self.ll * self.rr)


def _package_blocks(pkg: Package, roles: list[str], block_frames: int) -> Iterator[np.ndarray]:
    handles = [sf.SoundFile(str(pkg.files[r])) for r in roles]
    try:
        while True:
            cols = [h.read(block_frames, dtype="float64", always_2d=True) for h in handles]
            n = min(c.shape[0] for c in cols)
            if n == 0:
                break
            yield np.hstack([c[:n] for c in cols])
    finally:
        for h in handles:
            h.close()


def measure(path: str | Path, roles: list[str] | None = None, block_frames: int = DEFAULT_BLOCK_FRAMES) -> Measurement:
    """Measure a file. For a directory, measure it as a package of discrete channel files."""
    path = Path(path)
    if path.is_dir():
        return measure_package(path, block_frames=block_frames)
    info = probe(path)
    roles = roles or default_roles(info.channels)
    return _run(path, info.samplerate, info.channels, roles, iter_blocks(path, block_frames), info=info)


def measure_package(directory: str | Path, block_frames: int = DEFAULT_BLOCK_FRAMES) -> Measurement:
    from ..io.reader import load_package

    pkg = load_package(directory)
    problems = pkg.consistent()
    if problems:
        raise ValueError("package is not consistent: " + "; ".join(problems))
    present = [r for r in SMPTE_ORDER if r in pkg.files]
    for r in ("Lt", "Rt", "M"):
        if r in pkg.files and r not in present:
            present.append(r)
    if not present:
        raise ValueError("no recognised channel files in package")
    fs = next(iter(pkg.infos.values())).samplerate
    return _run(Path(directory), fs, len(present), present, _package_blocks(pkg, present, block_frames), package=pkg)


def _run(path: Path, fs: int, channels: int, roles: list[str], blocks: Iterator[np.ndarray], info: AudioInfo | None = None, package: Package | None = None) -> Measurement:
    loud = LoudnessMeter(fs, channels, roles=roles)
    peak = PeakMeter(fs, channels)
    stats = _Stats(fs, channels)
    fold = LoudnessMeter(fs, 1) if channels == 2 else None
    for block in blocks:
        loud.feed(block)
        peak.feed(block)
        stats.feed(block)
        if fold is not None:
            fold.feed(block.mean(axis=1, keepdims=True))
    head, tail = stats.head_tail()
    lr = loud.result()
    return Measurement(
        path=path,
        samplerate=fs,
        channels=channels,
        roles=list(roles),
        duration_s=lr.duration_s,
        loudness=lr,
        peaks=peak.result(),
        dc_offset=stats.dc(),
        head_silence_s=head,
        tail_silence_s=tail,
        phase_correlation=stats.correlation(),
        mono_fold_loudness=(fold.result().integrated if fold is not None else None),
        info=info,
        package=package,
    )
