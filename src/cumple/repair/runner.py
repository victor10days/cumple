"""Run a chain over a file and write the repaired copy, streaming, the way `fix` writes its copy.

The file goes through the chain in blocks by the chunk protocol of crates/cumple-dsp/src/module.rs
(`Chunker::run`): each call's centre is one block, with up to `context_frames` of the module's own
earlier output on the left and `context_frames` raw samples on the right; a tail shorter than the longest
context in the chain joins the call before it, and `Edge` says where the file starts and ends. In a chain every module
keeps its own left context, and its right context is the raw lookahead, which the modules before it have
not processed yet. Memory holds a few blocks and each module's context, whatever the file's length.
"""

from __future__ import annotations

import contextlib
import itertools
import os
import time
import unicodedata
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf

from .. import __version__
from ..io.reader import DEFAULT_BLOCK_FRAMES, iter_blocks, probe
from ..meters.measure import measure
from . import receipt as receipts
from . import require
from .chain import Chain, dump


@dataclass
class RepairResult:
    dst: Path | None  # None when nothing changed: no copy is written
    receipt_path: Path | None
    reports: list[dict[str, Any]]  # each module's report() with its id under "module", in chain order
    changed: bool  # some module repaired something
    receipt: receipts.Receipt | None = None


def _refuse(src: Path, target: Path, option: str) -> None:
    if target.is_dir():
        raise ValueError(f"{target} is a directory; give {option} a file path")
    # samefile as well as resolve(): on a case-insensitive volume (macOS's default, Windows) TAKE.WAV is take.wav,
    # yet the two resolve to different paths, and os.replace onto TAKE.WAV would replace the source.
    if target.exists() and (target.resolve() == src.resolve() or os.path.samefile(target, src)):
        raise ValueError(f"refusing to overwrite the source file {src}; give {option} a different path")


def _folded(path: Path) -> str:
    return unicodedata.normalize("NFC", path.name).casefold()


def _one_file(a: Path, b: Path) -> bool:
    """Whether two destinations may name one file. Neither need exist yet, so besides resolve() and samefile this
    compares the names in one folder after case folding and NFC normalisation, which macOS's default volume and
    Windows both ignore (os.path.normcase would not do: on macOS it changes nothing). On a case-sensitive volume
    two names that differ only in case are refused too, which costs nothing."""
    if a.resolve() == b.resolve() or (a.exists() and b.exists() and os.path.samefile(a, b)):
        return True
    try:
        same_folder = os.path.samefile(a.parent, b.parent)
    except OSError:  # a folder that does not exist; writing there fails later with its own message
        same_folder = a.resolve().parent == b.resolve().parent
    return same_folder and _folded(a) == _folded(b)


def _stored(info) -> Callable[[np.ndarray], np.ndarray]:
    """The values the file will hold. An integer subtype gets its samples rounded to its grid and clipped to its
    range here, because libsndfile 1.2.2 truncates toward minus infinity on the way to 24 bits (0.7 LSB is stored as
    0, -0.3 as -1). Values already on the grid are stored exactly, so the residual is exactly input minus copy."""
    if info.is_float:
        return lambda v: v
    scale = 2.0 ** (info.bit_depth - 1)
    return lambda v: np.clip(np.round(v * scale), -scale, scale - 1) / scale


def _run(modules: list, blocks: Iterator[np.ndarray], channels: int, block: int, write: Callable) -> None:
    """Feed the file through the modules in order, call by call, and hand each centre to `write(raw, repaired)`."""
    contexts = [m.context_frames for m in modules]
    reach = max(contexts)
    behind = [np.empty((0, channels)) for _ in modules]  # each module's own last output, up to its context
    ahead = np.empty((0, channels))  # raw frames from the current centre on
    ended = False
    start = 0
    while True:
        while not ended and len(ahead) < block + reach:
            nxt = next(blocks, None)
            if nxt is None:
                ended = True
            else:
                ahead = np.concatenate([ahead, nxt])
        if not len(ahead):
            break
        end = min(block, len(ahead))
        if ended and len(ahead) - end < reach:  # a tail shorter than the context joins this call
            end = len(ahead)
        last = ended and end == len(ahead)
        y = ahead[:end]
        for i, m in enumerate(modules):
            right = ahead[end : end + contexts[i]]  # raw; empty on the last call, which runs to the file's end
            out = m.process(np.concatenate([behind[i], y, right]), edge=(start <= contexts[i], last, 0))
            y = out[len(behind[i]) : len(behind[i]) + end]
            kept = np.concatenate([behind[i], y])
            behind[i] = kept[len(kept) - min(contexts[i], len(kept)) :]
        write(ahead[:end], y)
        ahead = ahead[end:]
        start += end
    for i, m in enumerate(modules):
        if len(m.flush()):  # nothing, for a module without latency; a sample here would be lost
            raise RuntimeError(f"step {i + 1} of the chain held samples back at the end of the file")


def repair_file(
    src: str | Path,
    chain: Chain,
    dst: str | Path,
    residual: str | Path | None = None,
    *,
    receipt_path: str | Path | None = None,
    block_frames: int = DEFAULT_BLOCK_FRAMES,
) -> RepairResult:
    """Write `dst` as `src` through `chain`, with the same rate, channels, subtype and container, and a receipt
    beside it (`<dst>.cumple-repair.json` unless `receipt_path` says otherwise). `residual`, when given, gets
    the input minus the output through the same path: what the chain removed.

    When no module finds anything to repair, nothing is written and `changed` is False. A failure before the
    copy is in place leaves no copy, no residual and no receipt, and an older file at those paths as it was.
    """
    require()
    import cumple_dsp

    started = time.perf_counter()
    src, dst = Path(src), Path(dst)
    receipt_path = Path(receipt_path) if receipt_path is not None else receipts.default_path(dst)
    targets = {"--out": dst, "--receipt": receipt_path}
    if residual is not None:
        residual = Path(residual)
        targets["--residual"] = residual
    for option, target in targets.items():
        _refuse(src, target, option)
    for (option_a, a), (option_b, b) in itertools.combinations(targets.items(), 2):
        if _one_file(a, b):
            raise ValueError(f"{option_a} and {option_b} name the same file, {a} and {b}; give each a different path")
    # Refused here, before any work: the receipt is written last, so a missing folder there would leave a copy in
    # place with no receipt beside it.
    for option, target in targets.items():
        if not target.parent.is_dir():
            raise ValueError(
                f"the folder for {option}, {target.parent}, does not exist; create it or give another path"
            )
    info = probe(src)
    if info.via_ffmpeg or not info.is_pcm:
        raise ValueError(
            f"{src.name} is {info.codec or info.subtype} decoded by {info.decoder}; "
            "repair writes PCM only, bounce it as WAV first"
        )
    make = {"declick": cumple_dsp.Declick, "declip": cumple_dsp.Declip}
    modules = [make[step.module](info.samplerate, **step.params.model_dump()) for step in chain.steps]
    if any(m.latency_frames for m in modules):
        raise RuntimeError("a module in the chain delays its output; the runner serves modules without latency")
    stored = _stored(info)

    def open_for(path: Path) -> sf.SoundFile:
        return sf.SoundFile(
            str(path),
            "w",
            samplerate=info.samplerate,
            channels=info.channels,
            subtype=info.subtype,
            format=info.container,
        )

    # Write next to each destination under a temporary name and move it into place only once the whole
    # copy succeeded, so a failure half-way never leaves a truncated deliverable behind.
    tmp = dst.with_name(f".{dst.name}.cumple-tmp")
    tmp_residual = residual.with_name(f".{residual.name}.cumple-tmp") if residual is not None else None
    try:
        with contextlib.ExitStack() as files:
            fout = files.enter_context(open_for(tmp))
            rout = files.enter_context(open_for(tmp_residual)) if tmp_residual is not None else None

            def write(raw: np.ndarray, repaired: np.ndarray) -> None:
                copy = stored(repaired)
                fout.write(copy)
                if rout is not None:
                    rout.write(stored(raw - copy))

            _run(modules, iter_blocks(src, block_frames, info=info), info.channels, block_frames, write)
        reports = [{"module": step.module, **m.report()} for step, m in zip(chain.steps, modules, strict=True)]
        if not any(len(r["positions"]) for r in reports):
            return RepairResult(None, None, reports, False)
        before, after = measure(src), measure(tmp)
        records = {"input": receipts.record(src), "output": receipts.record(dst, digest_of=tmp)}
        if residual is not None:
            records["residual"] = receipts.record(residual, digest_of=tmp_residual)
        os.replace(tmp, dst)
        if residual is not None:
            os.replace(tmp_residual, residual)
    finally:
        for t in (tmp, tmp_residual):
            if t is not None and t.exists():
                t.unlink()
    receipt = receipts.Receipt(
        cumple_version=__version__,
        cumple_dsp_version=cumple_dsp.__version__,
        core_version=cumple_dsp.core_version(),
        chain_yaml=dump(chain),
        chain=chain,
        **records,
        before=receipts.levels(before),
        after=receipts.levels(after),
        reports=reports,
        wall_time_s=time.perf_counter() - started,
    )
    receipts.write(receipt_path, receipt)
    return RepairResult(dst, receipt_path, reports, True, receipt)
