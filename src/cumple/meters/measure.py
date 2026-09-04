"""One pass over a file (or a package of discrete channel files) that feeds every meter."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import soundfile as sf

from ..io.reader import DEFAULT_BLOCK_FRAMES, AudioInfo, Package, iter_blocks, probe
from .bs1770 import SUB_HOP_S, LoudnessMeter, LoudnessResult, default_roles
from .dialogue import SpeechDetector, SpeechResult
from .layout import LayoutMeter, LayoutResult
from .leqm import LeqmMeter, LeqmResult
from .truepeak import PeakMeter, PeakResult

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
    rms_dbfs: float = -np.inf
    noise_floor_dbfs: float = -np.inf
    speech_fraction: float | None = None  # share of active programme that is speech-like (heuristic)
    speech: SpeechResult | None = None
    layout_stats: LayoutResult | None = None
    leqm: LeqmResult | None = None
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
        self.sq = 0.0
        self.win = int(round(samplerate * 0.1))
        self._win_pending = np.empty((0, channels))
        self.win_energy: list[float] = []

    def feed(self, x: np.ndarray) -> None:
        n = x.shape[0]
        self.sum += x.sum(axis=0)
        self.sq += float(np.sum(x * x))
        w = np.concatenate([self._win_pending, x]) if self._win_pending.size else x
        k = len(w) // self.win
        if k:
            whole = w[: k * self.win].reshape(k, self.win, self.ch)
            self.win_energy.extend(np.mean(whole * whole, axis=(1, 2)))
        self._win_pending = w[k * self.win :]
        loud = np.flatnonzero(np.abs(x).max(axis=1) >= self.thr)
        if loud.size:
            if self.first_loud is None:
                self.first_loud = self.n + int(loud[0])
            self.last_loud = self.n + int(loud[-1])
        if self.ch == 2:
            left, right = x[:, 0], x[:, 1]
            self.lr += float(left @ right)
            self.ll += float(left @ left)
            self.rr += float(right @ right)
        self.n += n

    def dc(self) -> np.ndarray:
        return self.sum / max(self.n, 1)

    def head_tail(self) -> tuple[float, float]:
        if self.first_loud is None:
            return self.n / self.fs, 0.0
        return self.first_loud / self.fs, (self.n - 1 - self.last_loud) / self.fs

    def rms_dbfs(self) -> float:
        total = self.n * self.ch
        return 10 * np.log10(self.sq / total) if total and self.sq > 0 else -np.inf

    def noise_floor_dbfs(self) -> float:
        """RMS of the quietest 10 % of 100 ms windows (ACX's noise floor idea)."""
        e = np.sort(np.asarray(self.win_energy))
        if e.size == 0:
            return -np.inf
        k = max(1, int(len(e) * 0.1))
        q = float(e[:k].mean())
        return 10 * np.log10(q) if q > 0 else -np.inf

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


def measure_args(profile) -> dict:
    """Keyword arguments for measure() that depend on the destination: the cinema meter with the
    profile's calibration, and the LFE corner for the layout check, one octave above the profile's
    low-pass (where a 24 dB/octave filter leaves -24 dB, so a compliant LFE passes with margin)."""
    args: dict = {}
    if profile.leqm is not None:
        args["leqm"] = {
            "calibration_dbfs": profile.leqm.calibration_dbfs,
            "calibration_db": profile.leqm.calibration_spl_db,
            "surround_offset_db": profile.leqm.surround_offset_db,
        }
    if profile.format.lfe_lowpass_hz:
        args["lfe_corner_hz"] = 2.0 * profile.format.lfe_lowpass_hz
    return args


def measure(
    path: str | Path,
    roles: list[str] | None = None,
    block_frames: int = DEFAULT_BLOCK_FRAMES,
    leqm: bool | dict = False,
    lfe_corner_hz: float | None = None,
) -> Measurement:
    """Measure a file. For a directory, measure it as a package of discrete channel files.
    leqm=True (or a dict of LeqmMeter calibration arguments) also runs the cinema Leq(m) meter,
    an 8k-tap FIR per channel, only when asked. lfe_corner_hz sets where the LFE band check looks."""
    path = Path(path)
    if path.is_dir():
        return measure_package(path, block_frames=block_frames, leqm=leqm, lfe_corner_hz=lfe_corner_hz)
    info = probe(path)
    roles = roles or default_roles(info.channels)
    return _run(
        path,
        info.samplerate,
        info.channels,
        roles,
        iter_blocks(path, block_frames),
        info=info,
        leqm=leqm,
        lfe_corner_hz=lfe_corner_hz,
    )


def measure_package(
    directory: str | Path,
    block_frames: int = DEFAULT_BLOCK_FRAMES,
    leqm: bool | dict = False,
    lfe_corner_hz: float | None = None,
) -> Measurement:
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
    return _run(
        Path(directory),
        fs,
        len(present),
        present,
        _package_blocks(pkg, present, block_frames),
        package=pkg,
        leqm=leqm,
        lfe_corner_hz=lfe_corner_hz,
    )


def _run(
    path: Path,
    fs: int,
    channels: int,
    roles: list[str],
    blocks: Iterator[np.ndarray],
    info: AudioInfo | None = None,
    package: Package | None = None,
    leqm: bool | dict = False,
    lfe_corner_hz: float | None = None,
) -> Measurement:
    loud = LoudnessMeter(fs, channels, roles=roles)
    peak = PeakMeter(fs, channels)
    stats = _Stats(fs, channels)
    speech = SpeechDetector(fs, channels, roles=roles)
    fold = LoudnessMeter(fs, 1) if channels == 2 else None
    layout = LayoutMeter(fs, channels, corner_hz=lfe_corner_hz or 250.0) if channels >= 3 else None
    leqm_meter = LeqmMeter(fs, channels, roles=roles, **(leqm if isinstance(leqm, dict) else {})) if leqm else None
    for block in blocks:
        loud.feed(block)
        peak.feed(block)
        stats.feed(block)
        speech.feed(block)
        if layout is not None:
            layout.feed(block)
        if fold is not None:
            fold.feed(block.mean(axis=1, keepdims=True))
        if leqm_meter is not None:
            leqm_meter.feed(block)
    head, tail = stats.head_tail()
    sp = speech.result()
    lr = loud.result()
    n_sub = len(loud._hop_energies())
    dg, dg_blocks = loud.dialogue_gated(sp.mask_at(SUB_HOP_S, n_sub))
    lr.dialogue_gated, lr.dialogue_blocks = dg, dg_blocks
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
        rms_dbfs=stats.rms_dbfs(),
        noise_floor_dbfs=stats.noise_floor_dbfs(),
        mono_fold_loudness=(fold.result().integrated if fold is not None else None),
        speech_fraction=sp.fraction,
        speech=sp,
        layout_stats=(layout.result() if layout is not None else None),
        leqm=(leqm_meter.result() if leqm_meter is not None else None),
        info=info,
        package=package,
    )
