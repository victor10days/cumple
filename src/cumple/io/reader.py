"""Audio file access: probing, streaming blocks, embedded metadata, and delivery packages.

Everything here is read-only. Nothing in this module ever writes to or moves a file.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf

# Bits per sample by libsndfile subtype name.
SUBTYPE_BITS: dict[str, int] = {
    "PCM_S8": 8,
    "PCM_U8": 8,
    "PCM_16": 16,
    "PCM_24": 24,
    "PCM_32": 32,
    "FLOAT": 32,
    "DOUBLE": 64,
    "ALAC_16": 16,
    "ALAC_20": 20,
    "ALAC_24": 24,
    "ALAC_32": 32,
}
FLOAT_SUBTYPES = {"FLOAT", "DOUBLE"}
WAV_FAMILY = {"WAV", "WAVEX", "RF64", "W64"}

# 262144 frames is about 5.5 s at 48 kHz: large enough to amortise Python overhead,
# small enough that a 2-hour 5.1 file never needs more than a few MB at a time.
DEFAULT_BLOCK_FRAMES = 1 << 18

AUDIO_SUFFIXES = {".wav", ".bwf", ".rf64", ".w64", ".aif", ".aiff", ".flac"}


@dataclass(frozen=True)
class AudioInfo:
    """What we know about a file before reading any samples."""

    path: Path
    container: str  # WAV, WAVEX, RF64, AIFF, FLAC ...
    subtype: str  # PCM_24, FLOAT ...
    samplerate: int
    channels: int
    frames: int
    metadata: dict[str, Any] = field(default_factory=dict)

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
    def bext(self) -> dict[str, Any]:
        return self.metadata.get("bext", {})


def probe(path: str | Path) -> AudioInfo:
    """Open the file header and return its shape plus any embedded BWF metadata."""
    path = Path(path)
    with sf.SoundFile(str(path)) as f:
        container = f.format
        info = AudioInfo(
            path=path,
            container=container,
            subtype=f.subtype,
            samplerate=f.samplerate,
            channels=f.channels,
            frames=f.frames,
            metadata=read_metadata(path, container),
        )
    return info


_BEXT_FIELDS = (
    "description",
    "originator",
    "originator_ref",
    "originator_date",
    "originator_time",
    "time_reference",
    "version",
    "umid",
    "coding_history",
    "loudness_value",
    "loudness_range",
    "max_true_peak",
    "max_momentary_loudness",
    "max_shortterm_loudness",
)


def read_metadata(path: str | Path, container: str | None = None) -> dict[str, Any]:
    """bext, iXML, chna and axml via wavinfo, for WAV-family containers only.

    Never raises: a file with damaged metadata still gets measured.
    """
    if container is not None and container not in WAV_FAMILY:
        return {}
    try:
        from wavinfo import WavInfoReader
    except ImportError:
        return {}
    try:
        reader = WavInfoReader(str(path))
    except Exception:
        return {}

    out: dict[str, Any] = {}
    bext = getattr(reader, "bext", None)
    if bext is not None:
        try:
            out["bext"] = dict(bext.to_dict())
        except Exception:
            out["bext"] = {k: getattr(bext, k) for k in _BEXT_FIELDS if hasattr(bext, k)}
    ixml = getattr(reader, "ixml", None)
    if ixml is not None:
        out["ixml"] = {
            k: getattr(ixml, k)
            for k in ("project", "scene", "take", "tape", "family_uid", "family_name")
            if hasattr(ixml, k)
        }
    adm = getattr(reader, "adm", None)
    if adm is not None:
        try:
            out["adm"] = {"track_count": len(getattr(adm, "channel_uids", []) or [])}
        except Exception:
            out["adm"] = {"present": True}
    return out


def iter_blocks(
    path: str | Path,
    block_frames: int = DEFAULT_BLOCK_FRAMES,
    dtype: str = "float64",
) -> Iterator[np.ndarray]:
    """Yield (frames, channels) float blocks. Full scale is 1.0 for every subtype."""
    yield from sf.blocks(str(path), blocksize=block_frames, dtype=dtype, always_2d=True)


def read(path: str | Path, dtype: str = "float64") -> tuple[np.ndarray, int]:
    """Read a whole file as (frames, channels). Use iter_blocks for anything long."""
    data, sr = sf.read(str(path), dtype=dtype, always_2d=True)
    return data, sr


# Channel roles recognised in filename suffixes, for packages of discrete mono files
# (Amazon Studios: "Discrete .wav files required per channel").
ROLE_ALIASES: dict[str, str] = {
    "l": "L",
    "left": "L",
    "r": "R",
    "right": "R",
    "c": "C",
    "centre": "C",
    "center": "C",
    "lfe": "LFE",
    "sub": "LFE",
    "ls": "Ls",
    "lss": "Lss",
    "rs": "Rs",
    "rss": "Rss",
    "lrs": "Lrs",
    "rrs": "Rrs",
    "lb": "Lrs",
    "rb": "Rrs",
    "lt": "Lt",
    "rt": "Rt",
    "m": "M",
    "mono": "M",
}

_ROLE_RE = re.compile(r"[._\- ]([A-Za-z]{1,6})$")


def role_from_name(path: str | Path) -> str | None:
    stem = Path(path).stem
    m = _ROLE_RE.search(stem)
    if not m:
        return None
    return ROLE_ALIASES.get(m.group(1).lower())


@dataclass
class Package:
    """A deliverable made of several files: discrete mono channels, or stems."""

    directory: Path
    files: dict[str, Path]  # role -> file
    infos: dict[str, AudioInfo]

    @property
    def roles(self) -> list[str]:
        return list(self.files)

    @property
    def layout_guess(self) -> str:
        roles = set(self.files)
        if roles >= {"L", "R", "C", "LFE", "Ls", "Rs", "Lrs", "Rrs"}:
            return "7.1"
        if roles >= {"L", "R", "C", "LFE", "Ls", "Rs"}:
            return "5.1"
        if roles >= {"Lt", "Rt"}:
            return "lt-rt"
        if roles >= {"L", "R"}:
            return "stereo"
        if roles == {"M"}:
            return "mono"
        return "unknown"

    def consistent(self) -> list[str]:
        """Problems that make the package unusable as one deliverable."""
        problems: list[str] = []
        infos = list(self.infos.values())
        if not infos:
            return ["no audio files with a recognised channel suffix"]
        rates = {i.samplerate for i in infos}
        if len(rates) > 1:
            problems.append(f"mixed sample rates: {sorted(rates)}")
        frames = {i.frames for i in infos}
        if len(frames) > 1:
            problems.append(f"files differ in length: {sorted(frames)} frames")
        multi = [r for r, i in self.infos.items() if i.channels != 1]
        if multi:
            problems.append(f"not mono: {', '.join(multi)}")
        return problems


def load_package(directory: str | Path) -> Package:
    """Collect the audio files in a directory by channel role from their filename suffix."""
    directory = Path(directory)
    files: dict[str, Path] = {}
    for p in sorted(directory.iterdir()):
        if p.suffix.lower() not in AUDIO_SUFFIXES or p.name.startswith("."):
            continue
        role = role_from_name(p)
        if role is None:
            continue
        if role in files:
            raise ValueError(f"two files claim channel {role}: {files[role].name} and {p.name}")
        files[role] = p
    infos = {role: probe(p) for role, p in files.items()}
    return Package(directory=directory, files=files, infos=infos)
