"""Score ffmpeg and cathar (and cumple and iZotope RX 8, once they have run) on the damaged-audio set.

Run: uv run python scripts/make_repair_set.py && uv run python scripts/benchmark_repair.py > docs/REPAIR.md
Needs ffmpeg on PATH (or CUMPLE_FFMPEG) and the cathar CLI (CUMPLE_CATHAR, PATH, or ~/.cargo/bin; built from
the commit docs/REPAIR.md names). The script stops when either is missing: the committed report always
carries both baselines, because a column that cannot run says nothing. Reads the set under
~/.cache/cumple/repair/ (CUMPLE_REPAIR_SET overrides), outside the repository.

Per damaged file and tool it decodes the output and computes: delta SDR over all samples, delta SDR over the
damaged samples only, residual clicks (missed, false) at the detector of record's threshold of 5, the peak
error on clipped samples, and the wall time of the tool.
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

from cumple import __version__
from cumple.io.ffmpeg import STDERR_CAP, Ffmpeg, FfmpegError, _kill, find_ffmpeg
from cumple.repair import damage, metrics

DETECTOR_THRESHOLD = 5.0
CATHAR_REV = "f2c2842f89084589d069e5a8a0b61311aa70d928"
CATHAR_BUDGET_FACTOR = 20.0  # wall time allowed for cathar: this times the duration ...
CATHAR_BUDGET_FLOOR_S = 120.0  # ... plus this
# ffmpeg's adeclip finishes a 4 s slice of one track in 0.3 s at 3 dB input SDR and above, yet does not finish
# a whole 71 s track at 3 dB in 91 s, or a 4 s slice at 1 dB in 25 s (measured 2026-10-08, ffmpeg 9.0.1). The benchmark therefore gives ffmpeg this times the duration
# plus the floor, and a file that exceeds it reads "not run (... exceeded its ... s budget)".
FFMPEG_BUDGET_FACTOR = 0.5
FFMPEG_BUDGET_FLOOR_S = 10.0
NOT_RUN_CUMPLE = "not run: build 1 Task 5"
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


def main() -> None:
    tools = find_ffmpeg()
    if tools is None:
        sys.exit("ffmpeg is not on PATH (or CUMPLE_FFMPEG); the baselines need it")
    cathar = find_cathar()
    if cathar is None:
        sys.exit("cathar is not on PATH, in ~/.cargo/bin or at CUMPLE_CATHAR; see the header of this script")
    root = set_dir()
    if not (root / "manifest.json").is_file():
        sys.exit(f"no repair set at {root}; run scripts/make_repair_set.py first")
    manifest = damage.Manifest.model_validate_json((root / "manifest.json").read_text(encoding="utf-8"))
    refs = {r.name: read_mono(root / r.file) for r in manifest.references}

    cells: dict[str, dict[str, Cell]] = {"ffmpeg": {}, "cathar": {}, "rx": {}}
    for i, entry in enumerate(manifest.damaged, 1):
        ref, y = refs[entry.reference], read_mono(root / entry.file)
        for name in ("ffmpeg", "cathar"):
            cells[name][entry.name] = run_tool(name, entry, root, ref, y, tools, cathar)
            print(f"[{i}/{len(manifest.damaged)}] {name} {entry.name}: {cells[name][entry.name].text}", file=sys.stderr)
        cells["rx"][entry.name] = rx_cell(entry, manifest, root, ref, y)

    versions = f"cumple {__version__}, ffmpeg {tools.version}, {cathar_version(cathar)} at commit {CATHAR_REV[:7]}"
    built = datetime.fromtimestamp((root / "manifest.json").stat().st_mtime).date()
    lines = [
        "# Repair scores: ffmpeg and cathar baselines",
        "",
        f"Generated by `scripts/benchmark_repair.py` on {date.today()}. Tools: {versions}. "
        f"The set was built on {built} by `scripts/make_repair_set.py` and is not committed.",
        "",
        "References present: "
        + "; ".join(f"{r.name} ({r.source}, {r.samplerate} Hz)" for r in manifest.references)
        + ".",
        "",
    ]
    for tool, label in (("ffmpeg", "ffmpeg"), ("cathar", "cathar")):
        vacuous = [n for n, c in cells[tool].items() if c.unchanged]
        lines.append(
            f"- {label} left {len(vacuous)} of {len(cells[tool])} damaged files byte-for-byte unchanged"
            + (": a baseline that changes nothing makes its column vacuous." if vacuous else ".")
        )
    lines += [
        f"- ffmpeg ran under a budget of {FFMPEG_BUDGET_FACTOR:g} times the file's duration plus {FFMPEG_BUDGET_FLOOR_S:g} s: "
        'adeclip is far slower on heavily clipped audio, and a file that exceeds the budget reads "not run" with the reason.',
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
            f"| Reference | {level_head} | ffmpeg {ff} | cathar {ca} | cumple | RX 8 |",
            "|---|---|---|---|---|---|",
        ]
        for e in entries:
            level = f"{e.sdr_db:g}" if kind == "clip" else str(e.seed)
            lines.append(
                f"| {e.reference} | {level} | {cells['ffmpeg'][e.name].text} | {cells['cathar'][e.name].text} | {NOT_RUN_CUMPLE} | {cells['rx'][e.name].text} |"
            )
        lines.append("")
    lines += burst_visibility(manifest, refs, root)

    lines += ["## Summary", "", "Means over the files each tool ran on; infinite values are left out of a mean.", ""]
    lines += [
        "| Damage | Tool | Files | Mean ΔSDR all (dB) | Mean ΔSDR damaged (dB) | Mean peak error (dB) | Clicks missed | False detections | Mean wall time (s) |"
    ]
    lines += ["|---|---|---|---|---|---|---|---|---|"]
    for kind, (title, *_rest) in kinds.items():
        names = [e.name for e in manifest.damaged if e.kind == kind]
        for tool in ("ffmpeg", "cathar"):
            got = [cells[tool][n] for n in names if cells[tool][n].d_all is not None]
            total = sum(len(next(e for e in manifest.damaged if e.name == n).clicks or []) for n in names)
            missed = f"{sum(c.missed for c in got)} of {total}" if kind != "clip" else "n/a"
            false = str(sum(c.false for c in got)) if kind != "clip" else "n/a"
            dmg = fmt_mean([c.d_dmg for c in got]) if kind == "clip" else "n/a"
            peak = fmt_mean([c.peak_db for c in got], "+.1f") if kind == "clip" else "n/a"
            lines.append(
                f"| {title} | {tool} | {len(got)} | {fmt_mean([c.d_all for c in got])} | {dmg} | {peak} | {missed} | {false} | {fmt_mean([c.seconds for c in got], '.2f')} |"
            )
        lines.append(f"| {title} | cumple | 0 | {NOT_RUN_CUMPLE} | | | | | |")
        lines.append(f"| {title} | RX 8 | 0 | {NOT_RUN_RX} | | | | | |")
    print("\n".join(lines))


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
