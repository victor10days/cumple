"""The receipt: a JSON sidecar beside a repaired copy that says exactly what ran on what.

It names the versions, the chain in both forms, the files by SHA-256, what `measure()` read before and
after, and each module's own report. The runner writes it last, once the copy is in place.
"""

from __future__ import annotations

import hashlib
import math
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from ..meters.measure import Measurement
from .chain import Chain

SUFFIX = ".cumple-repair.json"


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FileRecord(_Model):
    path: str
    sha256: str


class Levels(_Model):
    """What `measure()` reads with its default arguments; None where the value is not finite (silence)."""

    integrated_lufs: float | None
    true_peak_dbtp: float | None
    sample_peak_dbfs: float | None
    clipped_runs: int  # runs of 3 or more samples at full scale, as `check` counts them


class Receipt(_Model):
    cumple_version: str
    cumple_dsp_version: str
    core_version: str
    chain_yaml: str
    chain: Chain
    input: FileRecord
    output: FileRecord
    residual: FileRecord | None = None
    before: Levels
    after: Levels
    reports: list[dict[str, Any]]  # each module's report() with its id under "module", in chain order
    wall_time_s: float


def default_path(dst: Path) -> Path:
    """`<dst>.cumple-repair.json`, beside the copy."""
    return dst.with_name(dst.name + SUFFIX)


def sha256(path: Path) -> str:
    with path.open("rb") as fh:
        return hashlib.file_digest(fh, "sha256").hexdigest()


def record(path: Path, digest_of: Path | None = None) -> FileRecord:
    """A file by its absolute path, hashed from `digest_of` when the bytes still sit under a temporary name."""
    return FileRecord(path=str(path.resolve()), sha256=sha256(digest_of or path))


def levels(m: Measurement) -> Levels:
    def finite(v: float) -> float | None:
        return float(v) if math.isfinite(v) else None

    return Levels(
        integrated_lufs=finite(m.loudness.integrated),
        true_peak_dbtp=finite(m.peaks.true_peak_dbtp),
        sample_peak_dbfs=finite(m.peaks.sample_peak_dbfs),
        clipped_runs=m.peaks.clipped_runs,
    )


def write(path: Path, receipt: Receipt) -> Path:
    """Write the receipt as JSON under a temporary name beside `path`, then move it into place."""
    tmp = path.with_name(f".{path.name}.cumple-tmp")
    try:
        tmp.write_text(receipt.model_dump_json(indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()
    return path
