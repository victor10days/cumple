"""Score ffmpeg, cathar and cumple (and iZotope RX 8, once its outputs exist) on the damaged-audio set.

Run: uv run python scripts/make_repair_set.py && uv run python scripts/benchmark_repair.py > docs/REPAIR.md
Needs ffmpeg on PATH (or CUMPLE_FFMPEG) and the cathar CLI (CUMPLE_CATHAR, PATH, or ~/.cargo/bin; built from
the commit docs/REPAIR.md names). The script stops when either is missing: the committed report always
carries both baselines, because a column that cannot run says nothing. Reads the set under
~/.cache/cumple/repair/ (CUMPLE_REPAIR_SET overrides), outside the repository.

Per damaged file and tool it decodes the output and computes: delta SDR over all samples, delta SDR over the
damaged samples only, residual clicks (missed, false) at the detector of record's threshold of 5, the peak
error on clipped samples, and the wall time of the tool.

cumple appears as the shipped f64 build run through `repair_file` (the column scored against the others) and,
per file, in three more measurements the spec's scoring rule names: port fidelity (the f32 build through
`process_whole` against cathar's output, rule 1), the precision effect (f64 against f32, rule 1b) and the
chunking cost (the f64 build chunked at DEFAULT_BLOCK_FRAMES against its own whole-file run, rule 2). The script
exits 1 after printing the report when a row misses rule 1, whose bounds are never widened.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the fidelity check reuses tests/repair_helpers.py

from tests.repair_helpers import cathar_gaps  # noqa: E402

from cumple import __version__  # noqa: E402
from cumple.io.ffmpeg import STDERR_CAP, Ffmpeg, FfmpegError, _kill, find_ffmpeg  # noqa: E402
from cumple.io.reader import DEFAULT_BLOCK_FRAMES  # noqa: E402
from cumple.repair import chain, damage, metrics  # noqa: E402
from cumple.repair.runner import repair_file  # noqa: E402

DETECTOR_THRESHOLD = 5.0
CATHAR_REV = "f2c2842f89084589d069e5a8a0b61311aa70d928"
CATHAR_BUDGET_FACTOR = 20.0  # wall time allowed for cathar: this times the duration ...
CATHAR_BUDGET_FLOOR_S = 120.0  # ... plus this
# ffmpeg's adeclip finishes a 4 s slice of one track in 0.3 s at 3 dB input SDR and above, yet does not finish
# a whole 71 s track at 3 dB in 91 s, or a 4 s slice at 1 dB in 25 s (measured 2026-10-08, ffmpeg 9.0.1). The benchmark therefore gives ffmpeg this times the duration
# plus the floor, and a file that exceeds it reads "not run (... exceeded its ... s budget)".
FFMPEG_BUDGET_FACTOR = 0.5
FFMPEG_BUDGET_FLOOR_S = 10.0
FIDELITY_MAX_SAMPLE = 1e-6  # spec rule 1: never widened
FIDELITY_DELTA_SDR_DB = 0.01
NOT_SHORT = "not run (shorter than one block)"
NOT_RUN_RX = "not run (RX 8 outputs not present; see docs/repair/rx8-recipe.md)"


def set_dir() -> Path:
    return Path(os.environ.get("CUMPLE_REPAIR_SET") or Path.home() / ".cache" / "cumple" / "repair")


def find_cathar() -> Path | None:
    """The cathar CLI: CUMPLE_CATHAR, then PATH, then ~/.cargo/bin/cathar."""
    hint = os.environ.get("CUMPLE_CATHAR")
    candidates = [os.path.expanduser(hint)] if hint else []
    candidates.append(shutil.which("cathar") or "")
    candidates.append(str(Path.home() / ".cargo" / "bin" / "cathar"))
    for c in candidates:
        if c and Path(c).is_file():
            return Path(c)
    return None


def _run(argv: list[str], budget_s: float, what: str) -> None:
    """Run argv with stdin closed, its own session, a timeout that kills the whole group, and a capped stderr."""
    with tempfile.TemporaryFile() as err:
        proc = subprocess.Popen(
            argv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=err,
            start_new_session=(os.name != "nt"),
        )
        try:
            code = proc.wait(timeout=budget_s)
        except subprocess.TimeoutExpired as e:
            _kill(proc)
            proc.wait(timeout=5)
            raise FfmpegError(f"{what} exceeded its {budget_s:g} s budget") from e
        if code != 0:
            err.seek(0, os.SEEK_END)
            err.seek(max(0, err.tell() - STDERR_CAP))
            tail = err.read().decode("utf-8", "replace").strip()
            raise FfmpegError(f"{what} exited {code}: {tail or 'no message'}")


def run_ffmpeg(tools: Ffmpeg, src: Path, dst: Path, filter: str) -> Path:
    """Apply one ffmpeg audio filter (adeclick or adeclip, at its defaults) and write 32-bit float WAV."""
    src, dst = Path(src), Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    argv = [
        str(tools.ffmpeg),
        "-nostdin",
        "-v",
        "error",
        "-protocol_whitelist",
        "file",
        "-y",
        "-i",
        str(src),
        "-af",
        filter,
        "-c:a",
        "pcm_f32le",
        str(dst),
    ]
    _run(argv, FFMPEG_BUDGET_FACTOR * sf.info(src).duration + FFMPEG_BUDGET_FLOOR_S, f"ffmpeg {filter} on {src.name}")
    return dst


def cathar_version(binary: Path) -> str:
    out = subprocess.run(
        [str(binary), "--version"], capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=30, check=False
    ).stdout
    return out.strip().splitlines()[0].strip() if out.strip() else "unknown"


def run_cathar(binary: Path, src: Path, dst: Path, module: str, threshold: float) -> Path:
    """Run `cathar declick` or `cathar declip` at an explicit threshold (cathar's own defaults are 10 and 0.95)."""
    src, dst = Path(src), Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    argv = [str(binary), module, str(src), "--out", str(dst), "--threshold", repr(float(threshold)), "--no-banner"]
    budget = CATHAR_BUDGET_FACTOR * sf.info(src).duration + CATHAR_BUDGET_FLOOR_S
    _run(argv, budget, f"cathar {module} on {src.name}")
    return dst


@dataclass
class Cell:
    """One tool's result on one damaged file: the text for the table and the numbers behind it."""

    text: str
    seconds: float | None = None
    d_all: float | None = None
    d_dmg: float | None = None
    peak_db: float | None = None
    missed: int | None = None
    false: int | None = None
    unchanged: bool = False


def not_run(reason: str) -> Cell:
    return Cell(f"not run ({reason})")


def score(entry: damage.Damaged, ref: np.ndarray, y: np.ndarray, est: np.ndarray, seconds: float | None) -> Cell:
    if len(est) != len(ref):
        return not_run(f"output has {len(est)} samples, reference {len(ref)}")
    unchanged = bool(np.array_equal(est.astype(np.float32), y.astype(np.float32)))
    d_all = metrics.delta_sdr(ref, y, est)
    if entry.kind == "clip":
        mask = np.abs(ref) >= entry.threshold
        d_dmg = metrics.delta_sdr(ref, y, est, mask=mask)
        peak = metrics.peak_error_db(ref, est, mask)
        return Cell(f"{d_all:+.2f} / {d_dmg:+.2f} / {peak:+.1f}", seconds, d_all, d_dmg, peak, unchanged=unchanged)
    clicks = entry.clicks or []
    missed, false = metrics.residual_clicks(
        ref, est, [c.position for c in clicks], [c.width for c in clicks], DETECTOR_THRESHOLD
    )
    return Cell(
        f"{d_all:+.2f} / {missed} of {len(clicks)} / {false}",
        seconds,
        d_all,
        missed=missed,
        false=false,
        unchanged=unchanged,
    )


def read_mono(path: Path) -> np.ndarray:
    data, _ = sf.read(path, dtype="float64", always_2d=True)
    return data[:, 0]


def run_tool(name: str, entry: damage.Damaged, root: Path, ref: np.ndarray, y: np.ndarray, tools, cathar) -> Cell:
    stem = Path(entry.file).stem
    src = root / entry.file
    dst = root / "outputs" / name / f"{stem}.wav"
    start = time.perf_counter()
    try:
        if name == "ffmpeg":
            run_ffmpeg(tools, src, dst, "adeclip" if entry.kind == "clip" else "adeclick")
        else:
            run_cathar(
                cathar, src, dst, "declip" if entry.kind == "clip" else "declick", entry.threshold or DETECTOR_THRESHOLD
            )
    except FfmpegError as e:
        return not_run(str(e).splitlines()[0][:120])
    return score(entry, ref, y, read_mono(dst), time.perf_counter() - start)


@dataclass
class Detail:
    """What the spec's rules 1, 1b and 2 measure for one damaged file; every field is text for the table."""

    fid_gaps: str  # De-click: whether the f32 build and cathar listed the same gaps
    fid_max: float | None  # largest |f32 build - cathar|
    fid_dsdr: float | None  # dSDR(f32 build) - dSDR(cathar)
    fid_unclipped: str  # De-clip: whether every unclipped sample is the input's, in both
    prec_gaps: int | None  # De-click: gaps listed by one precision and not the other
    prec_dsdr: float
    prec_max: float
    chunk_dsdr: float | None  # dSDR(whole file) - dSDR(chunked); None when the reference fits one block
    chunk_max: float | None
    misses: list[str]  # the rule 1 bounds this file missed


def run_cumple(entry: damage.Damaged, root: Path, ref: np.ndarray, y: np.ndarray, fs: int, theirs: np.ndarray | None):
    """The shipped f64 build through `repair_file`, then the three measurements around it. Returns (Cell, Detail)."""
    import cumple_dsp

    from cumple.repair import receipt as receipts

    clip = entry.kind == "clip"
    stem = Path(entry.file).stem
    src = root / entry.file
    dst = root / "outputs" / "cumple" / f"{stem}.wav"
    dst.parent.mkdir(parents=True, exist_ok=True)
    for old in (dst, receipts.default_path(dst)):  # repair_file writes nothing when nothing changed
        old.unlink(missing_ok=True)
    steps = f"declip(threshold={entry.threshold!r})" if clip else f"declick(threshold={DETECTOR_THRESHOLD:g})"
    start = time.perf_counter()
    result = repair_file(src, chain.parse(steps), dst)
    seconds = time.perf_counter() - start
    chunked = read_mono(dst) if result.changed else y
    cell = score(entry, ref, y, chunked, seconds)

    def build(precision: str):
        if clip:
            return cumple_dsp.Declip(fs, threshold=entry.threshold, precision=precision)
        return cumple_dsp.Declick(fs, threshold=DETECTOR_THRESHOLD, precision=precision)

    out, gaps = {}, {}
    for precision in ("f32", "f64"):
        m = build(precision)
        out[precision] = m.process_whole(y)
        r = m.report()
        gaps[precision] = list(zip(r["positions"], r["widths"], strict=True))

    def d(est: np.ndarray) -> float:
        return metrics.delta_sdr(ref, y, est)

    misses: list[str] = []
    fid_gaps, fid_max, fid_dsdr, fid_unclipped = (
        "not run (cathar did not run)",
        None,
        None,
        "not run (cathar did not run)",
    )
    if theirs is not None and len(theirs) == len(y):
        fid_max = float(np.max(np.abs(out["f32"] - theirs)))
        fid_dsdr = d(out["f32"]) - d(theirs)
        if fid_max >= FIDELITY_MAX_SAMPLE:
            misses.append(f"largest sample difference {fid_max:.3e}")
        if abs(fid_dsdr) >= FIDELITY_DELTA_SDR_DB:
            misses.append(f"dSDR difference {fid_dsdr:+.4f} dB")
        if clip:
            same = bool(np.array_equal(out["f32"][np.abs(y) < entry.threshold], y[np.abs(y) < entry.threshold]))
            same = same and bool(np.array_equal(theirs[np.abs(y) < entry.threshold], y[np.abs(y) < entry.threshold]))
            fid_unclipped = "equal" if same else "differ"
            if not same:
                misses.append("an unclipped sample moved")
            fid_gaps = "n/a"
        else:
            fid_unclipped = "n/a"
            fid_gaps = "equal" if gaps["f32"] == cathar_gaps(y, DETECTOR_THRESHOLD) else "differ"
            if fid_gaps != "equal":
                misses.append("the gap lists differ")
    prec_gaps = None if clip else len(set(gaps["f32"]) ^ set(gaps["f64"]))
    chunk_dsdr = chunk_max = None
    if len(ref) > DEFAULT_BLOCK_FRAMES:
        whole = out["f64"].astype(np.float32).astype(np.float64)  # the whole-file run, stored as the runner stores it
        chunk_dsdr, chunk_max = d(whole) - d(chunked), float(np.max(np.abs(chunked - whole)))
    detail = Detail(
        fid_gaps,
        fid_max,
        fid_dsdr,
        fid_unclipped,
        prec_gaps,
        d(out["f64"]) - d(out["f32"]),
        float(np.max(np.abs(out["f64"] - out["f32"]))),
        chunk_dsdr,
        chunk_max,
        misses,
    )
    return cell, detail


def rx_cell(entry: damage.Damaged, manifest: damage.Manifest, root: Path, ref: np.ndarray, y: np.ndarray) -> Cell:
    """RX 8's output for this file from rx8/, divided by the recorded scale; 'not run' with the reason otherwise."""
    folder = root / "rx8"
    if not folder.is_dir():
        return Cell(NOT_RUN_RX)
    rx_in = next(r for r in manifest.rx_input if r.name == entry.name)
    given = root / rx_in.file
    if not given.is_file() or damage_sha(given) != rx_in.sha256:
        return not_run("rx8-input does not match the manifest hashes")
    out = folder / f"{entry.name}.wav"
    if not out.is_file():
        return not_run(f"no rx8/{entry.name}.wav")
    return score(entry, ref, y, read_mono(out) / rx_in.scale, None)


def damage_sha(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def fmt_mean(values: list[float], spec: str = "+.2f") -> str:
    finite = [v for v in values if np.isfinite(v)]
    return format(float(np.mean(finite)), spec) if finite else "n/a"


HEAD = "| Damage | Tool | Files ran | Mean ΔSDR all (dB) | Mean ΔSDR damaged (dB) | Mean peak error (dB) | Clicks missed | False detections | Mean wall time (s) |"
SEP = "|---|---|---|---|---|---|---|---|---|"


def summary_row(title: str, tool: str, kind: str, got: list[Cell], entries: list[damage.Damaged], coverage: str) -> str:
    """One summary line; every figure is over the same files `got` covers."""
    clip = kind == "clip"
    total = sum(len(e.clicks or []) for e in entries)
    missed = "n/a" if clip else f"{sum(c.missed for c in got)} of {total}"
    false = "n/a" if clip else str(sum(c.false for c in got))
    dmg = fmt_mean([c.d_dmg for c in got]) if clip else "n/a"
    peak = fmt_mean([c.peak_db for c in got], "+.1f") if clip else "n/a"
    secs = fmt_mean([c.seconds for c in got], ".2f")
    return f"| {title} | {tool} | {coverage} | {fmt_mean([c.d_all for c in got])} | {dmg} | {peak} | {missed} | {false} | {secs} |"


def fmt_range(values: list[float], spec: str = "+.4f") -> str:
    return f"{format(min(values), spec)} to {format(max(values), spec)}" if values else "n/a"


def detail_header(kind: str, level_head: str) -> tuple[str, str]:
    if kind == "clip":
        cols = [
            "Reference",
            level_head,
            "Fidelity max sample",
            "Fidelity ΔSDR diff (dB)",
            "Fidelity unclipped samples",
            "Precision ΔSDR diff (dB)",
            "Precision max sample",
            "Chunking ΔSDR cost (dB)",
            "Chunking max sample",
        ]
    else:
        cols = [
            "Reference",
            level_head,
            "Fidelity gaps",
            "Fidelity max sample",
            "Fidelity ΔSDR diff (dB)",
            "Precision gaps differing",
            "Precision ΔSDR diff (dB)",
            "Precision max sample",
            "Chunking ΔSDR cost (dB)",
            "Chunking max sample",
        ]
    return "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)


def detail_cells(kind: str, d: Detail) -> list[str]:
    fid_max = f"{d.fid_max:.2e}" if d.fid_max is not None else "not run (cathar did not run)"
    fid_dsdr = f"{d.fid_dsdr:+.4f}" if d.fid_dsdr is not None else "not run (cathar did not run)"
    chunk = (f"{d.chunk_dsdr:+.4f}", f"{d.chunk_max:.2e}") if d.chunk_dsdr is not None else (NOT_SHORT, NOT_SHORT)
    if kind == "clip":
        return [fid_max, fid_dsdr, d.fid_unclipped, f"{d.prec_dsdr:+.4f}", f"{d.prec_max:.2e}", *chunk]
    return [d.fid_gaps, fid_max, fid_dsdr, str(d.prec_gaps), f"{d.prec_dsdr:+.4f}", f"{d.prec_max:.2e}", *chunk]


def main() -> None:
    tools = find_ffmpeg()
    if tools is None:
        sys.exit("ffmpeg is not on PATH (or CUMPLE_FFMPEG); the baselines need it")
    cathar = find_cathar()
    if cathar is None:
        sys.exit("cathar is not on PATH, in ~/.cargo/bin or at CUMPLE_CATHAR; see the header of this script")
    from cumple import repair

    repair.require()
    import cumple_dsp  # noqa: F401  (named in the header)

    root = set_dir()
    if not (root / "manifest.json").is_file():
        sys.exit(f"no repair set at {root}; run scripts/make_repair_set.py first")
    manifest = damage.Manifest.model_validate_json((root / "manifest.json").read_text(encoding="utf-8"))
    refs = {r.name: read_mono(root / r.file) for r in manifest.references}
    rates = {r.name: r.samplerate for r in manifest.references}

    tool_names = ("ffmpeg", "cathar", "cumple")
    cells: dict[str, dict[str, Cell]] = {"ffmpeg": {}, "cathar": {}, "cumple": {}, "rx": {}}
    details: dict[str, Detail] = {}
    for i, entry in enumerate(manifest.damaged, 1):
        ref, y = refs[entry.reference], read_mono(root / entry.file)
        for name in ("ffmpeg", "cathar"):
            cells[name][entry.name] = run_tool(name, entry, root, ref, y, tools, cathar)
            print(f"[{i}/{len(manifest.damaged)}] {name} {entry.name}: {cells[name][entry.name].text}", file=sys.stderr)
        theirs = None
        if cells["cathar"][entry.name].d_all is not None:
            theirs = read_mono(root / "outputs" / "cathar" / f"{Path(entry.file).stem}.wav")
        cells["cumple"][entry.name], details[entry.name] = run_cumple(
            entry, root, ref, y, rates[entry.reference], theirs
        )
        print(
            f"[{i}/{len(manifest.damaged)}] cumple {entry.name}: {cells['cumple'][entry.name].text}"
            + (f"; FIDELITY MISS: {'; '.join(details[entry.name].misses)}" if details[entry.name].misses else ""),
            file=sys.stderr,
        )
        cells["rx"][entry.name] = rx_cell(entry, manifest, root, ref, y)

    versions = (
        f"cumple {__version__}, cumple_dsp {getattr(cumple_dsp, '__version__', 'unknown')}, ffmpeg {tools.version}, "
        f"{cathar_version(cathar)} at commit {CATHAR_REV[:7]}"
    )
    built = datetime.fromtimestamp((root / "manifest.json").stat().st_mtime).date()
    lines = [
        "# Repair scores: cumple against ffmpeg and cathar",
        "",
        f"Generated by `scripts/benchmark_repair.py` on {date.today()}. Tools: {versions}. "
        f"The set was built on {built} by `scripts/make_repair_set.py` and is not committed.",
        "",
        "References present: "
        + "; ".join(f"{r.name} ({r.source}, {r.samplerate} Hz)" for r in manifest.references)
        + ".",
        "",
        f"Seeds: impulse {next(e.seed for e in manifest.damaged if e.kind == 'impulse')}, "
        f"burst {next(e.seed for e in manifest.damaged if e.kind == 'burst')} (recorded per file in the manifest). "
        f"Detector of record: cathar's local-RMS detector at threshold {DETECTOR_THRESHOLD:g} over a 64-sample window, "
        "whose ratio cannot exceed sqrt(64) = 8.",
        "",
    ]
    for tool in tool_names:
        ran = [n for n, c in cells[tool].items() if c.d_all is not None]
        same = [n for n in ran if cells[tool][n].unchanged]
        lines.append(
            f"- {tool} ran on {len(ran)} of {len(cells[tool])} damaged files and left {len(same)} of {len(ran)} that ran unchanged."
        )
        if same:
            kind_of = {e.name: e.kind for e in manifest.damaged}
            odd = [n for n in same if kind_of[n] != "burst"]
            lines.append(
                f"  - Unchanged: {', '.join(same)}."
                + (
                    " All are burst files: their clicks sit below the detector's sqrt(window) bound, so nothing was detected "
                    "and nothing should change (spec rule 0 exempts this)."
                    if not odd
                    else f" Not explained by the bound, so the column may be vacuous there: {', '.join(odd)}."
                )
            )
    clip_names = [e.name for e in manifest.damaged if e.kind == "clip"]
    click_names = [e.name for e in manifest.damaged if e.kind != "clip"]
    measured = [n for n in details if details[n].fid_max is not None]
    misses = [(n, m) for n in details for m in details[n].misses]
    lines += [
        f"- ffmpeg ran under a budget of {FFMPEG_BUDGET_FACTOR:g} times the file's duration plus {FFMPEG_BUDGET_FLOOR_S:g} s: "
        'adeclip is far slower on heavily clipped audio, and a file that exceeds the budget reads "not run" with the reason.',
        "  The budget is a property of the machine that generated this report, not of ffmpeg.",
        "- SQAM tracks are 20 s excerpts starting at 2 s (whole when shorter), so ffmpeg can finish them; LibriVox excerpts are 30 s.",
        "- The cumple column is the shipped f64 build: each damaged file through `repair_file` with a per-file chain "
        "(`declip(threshold=<the manifest value>)` for clip files, `declick(threshold=5)` for click files), which streams "
        f"the file in blocks of {DEFAULT_BLOCK_FRAMES:,} frames and stores 32-bit float. Its wall time is the whole call, "
        "including the two loudness measurements the receipt records. A receipt's `iterations` and `frames` are summed over calls and channels.",
        "- The tables and the first summary list each tool's mean over the files it ran on, with its coverage; "
        "the paired summary compares the tools over only the files all three ran, per damage type.",
        "",
        "## Tolerances of the scoring rule",
        "",
        f"- **Rule 1, port fidelity** (the f32 build through `process_whole` against cathar at the same commit, on the same machine; "
        f"every sample within {FIDELITY_MAX_SAMPLE:g} and dSDR(all) within {FIDELITY_DELTA_SDR_DB:g} dB; De-click also the same gap list, "
        "De-clip also every unclipped sample equal to the input): "
        + (
            f"**met on all {len(measured)} of {len(details)} files**."
            if not misses and len(measured) == len(details)
            else f"**NOT MET**: {len(set(n for n, _ in misses))} files miss, first {misses[0][0]}: {misses[0][1]}."
            if misses
            else f"**not measured on {len(details) - len(measured)} files**, where cathar did not run."
        ),
        f"  - Largest sample difference {max(details[n].fid_max for n in measured):.2e}; "
        f"dSDR difference from {min(details[n].fid_dsdr for n in measured):+.4f} to {max(details[n].fid_dsdr for n in measured):+.4f} dB."
        if measured
        else "  - No file was measured.",
        f"  - De-click gap lists equal on {sum(details[n].fid_gaps == 'equal' for n in click_names)} of {len(click_names)} files.",
        f"  - De-clip unclipped samples equal on {sum(details[n].fid_unclipped == 'equal' for n in clip_names)} of {len(clip_names)} files.",
        "- **Rule 1b, precision effect** (f64 against f32, reported, not gated): "
        f"dSDR difference from {min(d.prec_dsdr for d in details.values()):+.4f} to {max(d.prec_dsdr for d in details.values()):+.4f} dB, "
        f"largest sample difference up to {max(d.prec_max for d in details.values()):.2e}; "
        f"the two builds listed different De-click gaps on {sum(bool(details[n].prec_gaps) for n in click_names)} of {len(click_names)} files "
        "(where cathar's float32 running sum drifts).",
    ]
    for title, names in (("De-click", click_names), ("De-clip", clip_names)):
        cost = [details[n].chunk_dsdr for n in names if details[n].chunk_dsdr is not None]
        peak = [details[n].chunk_max for n in names if details[n].chunk_max is not None]
        lines.append(
            f"- **Rule 2, chunking cost, {title}** (the f64 build chunked at {DEFAULT_BLOCK_FRAMES:,} frames against its own whole-file "
            f"run, stored as 32-bit float, reported and pinned below 0.5 dB, not gated): {len(cost)} of {len(names)} files are longer than "
            f"one block; dSDR cost from {fmt_range(cost)} dB, largest sample difference up to {max(peak, default=0.0):.2e}."
        )
    lines += [
        "  - `tests/test_repair_declip.py` also holds De-clip's chunking cost on a 36 s file at this block size under 0.5 dB "
        "(Task 4 measured +0.027 dB there).",
        "",
    ]

    kinds = {
        "clip": ("De-clip", "adeclip", "declip", "ΔSDR all / ΔSDR damaged / peak error (dB)", "Input SDR (dB)"),
        "impulse": ("Impulse De-click", "adeclick", "declick", "ΔSDR all / clicks missed / false detections", "Seed"),
        "burst": ("Burst De-click", "adeclick", "declick", "ΔSDR all / clicks missed / false detections", "Seed"),
    }
    for kind, (title, ff, ca, cols, level_head) in kinds.items():
        entries = [e for e in manifest.damaged if e.kind == kind]
        lines += [
            f"## {title}",
            "",
            f"Each cell reads {cols}. ΔSDR is against the clean reference; the detector of record runs at threshold {DETECTOR_THRESHOLD:g}.",
            "",
            f"| Reference | {level_head} | ffmpeg {ff} | cathar {ca} | cumple (f64, shipped) | RX 8 |",
            "|---|---|---|---|---|---|",
        ]
        for e in entries:
            level = f"{e.sdr_db:g}" if kind == "clip" else str(e.seed)
            lines.append(
                f"| {e.reference} | {level} | {cells['ffmpeg'][e.name].text} | {cells['cathar'][e.name].text} | {cells['cumple'][e.name].text} | {cells['rx'][e.name].text} |"
            )
        head, rule = detail_header(kind, level_head)
        lines += [
            "",
            f"Fidelity is the f32 build against cathar (rule 1: max sample under {FIDELITY_MAX_SAMPLE:g}, ΔSDR difference under "
            f"{FIDELITY_DELTA_SDR_DB:g} dB). Precision is f64 minus f32 (rule 1b). Chunking is the whole-file ΔSDR minus the chunked "
            "ΔSDR of the f64 build (rule 2).",
            "",
            head,
            rule,
        ]
        for e in entries:
            level = f"{e.sdr_db:g}" if kind == "clip" else str(e.seed)
            lines.append(f"| {e.reference} | {level} | " + " | ".join(detail_cells(kind, details[e.name])) + " |")
        lines.append("")
    lines += burst_visibility(manifest, refs, root)
    lines += clip_peak_errors(manifest, cells)

    by_name = {e.name: e for e in manifest.damaged}
    lines += [
        "## Summary",
        "",
        "Each tool's mean over the files it ran on; infinite values are left out of a mean.",
        "",
    ]
    lines += [HEAD, SEP]
    for kind, (title, *_rest) in kinds.items():
        names = [e.name for e in manifest.damaged if e.kind == kind]
        for tool in tool_names:
            ran = [n for n in names if cells[tool][n].d_all is not None]
            lines.append(
                summary_row(
                    title,
                    tool,
                    kind,
                    [cells[tool][n] for n in ran],
                    [by_name[n] for n in ran],
                    f"{len(ran)} of {len(names)}",
                )
            )
        rx_ran = [n for n in names if cells["rx"][n].d_all is not None]
        if rx_ran:
            lines.append(
                summary_row(
                    title,
                    "RX 8",
                    kind,
                    [cells["rx"][n] for n in rx_ran],
                    [by_name[n] for n in rx_ran],
                    f"{len(rx_ran)} of {len(names)}",
                )
            )
        else:
            lines.append(f"| {title} | RX 8 | 0 of {len(names)} | {NOT_RUN_RX} | | | | | |")
    lines += [
        "",
        "## Summary, paired",
        "",
        "Only the files ffmpeg, cathar and cumple all ran on, per damage type; the rows of a damage type cover the same files.",
        "",
    ]
    lines += [HEAD, SEP]
    for kind, (title, *_rest) in kinds.items():
        names = [e.name for e in manifest.damaged if e.kind == kind]
        both = [n for n in names if all(cells[t][n].d_all is not None for t in tool_names)]
        for tool in tool_names:
            lines.append(
                summary_row(
                    title,
                    tool,
                    kind,
                    [cells[tool][n] for n in both],
                    [by_name[n] for n in both],
                    f"{len(both)} of {len(names)}",
                )
            )
    lines.append("")
    print("\n".join(lines))
    if misses:
        for n, m in misses:
            print(f"RULE 1 NOT MET: {n}: {m}", file=sys.stderr)
        sys.exit(1)


def clip_peak_errors(manifest: damage.Manifest, cells: dict[str, dict[str, Cell]]) -> list[str]:
    """Mean peak error on the clipped samples by input level: A-SPADE overshoots at the lowest levels."""
    levels = sorted({e.sdr_db for e in manifest.damaged if e.kind == "clip"})
    lines = [
        "## De-clip peak error by input level",
        "",
        "Peak error on the clipped samples in dB against the clean reference (0 is exact, positive overshoots), "
        "mean over the files each tool ran on at that level; cumple's is the f64 build.",
        "",
        "| Input SDR (dB) | cathar | cumple | cumple worst file |",
        "|---|---|---|---|",
    ]
    for level in levels:
        names = [e.name for e in manifest.damaged if e.kind == "clip" and e.sdr_db == level]
        cumple = [cells["cumple"][n].peak_db for n in names if cells["cumple"][n].peak_db is not None]
        cath = [cells["cathar"][n].peak_db for n in names if cells["cathar"][n].peak_db is not None]
        worst = max(cumple, key=abs, default=None)
        lines.append(
            f"| {level:g} | {fmt_mean(cath, '+.1f')} | {fmt_mean(cumple, '+.1f')} | "
            + (f"{worst:+.1f}" if worst is not None else "n/a")
            + " |"
        )
    for tool in ("cumple", "cathar"):
        fixture = {
            e.sdr_db: cells[tool][e.name].peak_db
            for e in manifest.damaged
            if e.kind == "clip" and e.reference == "fixture" and cells[tool][e.name].peak_db is not None
        }
        if fixture:
            lines += [
                "",
                f"On the fixture, {tool}'s peak error is "
                + ", ".join(f"{v:+.1f} dB at {level:g} dB" for level, v in sorted(fixture.items()))
                + " input SDR.",
            ]
    return lines + [""]


def burst_visibility(manifest: damage.Manifest, refs: dict[str, np.ndarray], root: Path) -> list[str]:
    """Share of burst clicks the detector of record sees in the damaged files, by width band: its real weakness."""
    bands = [(4, 8), (9, 16), (17, 32), (33, 64)]
    seen = {b: [0, 0] for b in bands}
    for e in (e for e in manifest.damaged if e.kind == "burst"):
        ratio = metrics.local_rms_ratio(read_mono(root / e.file))
        for c in e.clicks or []:
            first, last = metrics.click_span(c.position, c.width)
            band = next(b for b in bands if b[0] <= c.width <= b[1])
            seen[band][0] += int(ratio[first : last + 1].max() > DETECTOR_THRESHOLD)
            seen[band][1] += 1
    lines = [
        "## Burst clicks the detector of record can see",
        "",
        f"Share of burst clicks whose local-RMS ratio exceeds {DETECTOR_THRESHOLD:g} somewhere in the click, in the damaged files, by width. "
        "A click that dominates its 64-sample window reaches only about sqrt(128 / width) of its local RMS.",
        "",
        "| Width (samples) | Clicks | Visible |",
        "|---|---|---|",
    ]
    for (lo, hi), (hit, total) in seen.items():
        lines.append(
            f"| {lo} to {hi} | {total} | {100 * hit / total:.0f} % |" if total else f"| {lo} to {hi} | 0 | n/a |"
        )
    return lines + [""]


if __name__ == "__main__":
    main()
