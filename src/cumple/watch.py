"""Watch folder: every audio file that lands gets a QC sheet next to it and a line in a CSV log.

Rules that matter in a post house:
- A file is only measured once it has stopped growing (Pro Tools and most bounce paths
  write the file incrementally). Size and modification time must hold still for
  `stable_s` seconds.
- Source files are never modified, renamed or moved.
- A file that already has a newer QC sheet is skipped, so restarting the watcher does not
  redo the whole folder.
"""

from __future__ import annotations

import csv
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .checks import Status, evaluate
from .io.reader import AUDIO_SUFFIXES
from .meters.measure import measure
from .report import report_to_dict, write_sheet
from .specs.schema import Profile

PARTIAL_SUFFIXES = {".part", ".partial", ".tmp", ".crdownload", ".download"}
CSV_FIELDS = [
    "time",
    "file",
    "profile",
    "verdict",
    "integrated_lufs",
    "true_peak_dbtp",
    "lra_lu",
    "duration_s",
    "failed",
    "sheet",
]


@dataclass
class Seen:
    size: int
    mtime: float
    first_stable: float | None = None


def is_candidate(p: Path) -> bool:
    if not p.is_file() or p.name.startswith(".") or p.name.startswith("._"):
        return False
    if p.suffix.lower() in PARTIAL_SUFFIXES:
        return False
    return p.suffix.lower() in AUDIO_SUFFIXES


def already_done(p: Path, out_dir: Path | None) -> bool:
    target = (out_dir or p.parent) / f"{p.stem}.qc.json"
    return target.exists() and target.stat().st_mtime >= p.stat().st_mtime


def process(p: Path, profile: Profile, out_dir: Path | None, pdf: bool, log_csv: Path | None):
    m = measure(p, leqm=profile.leqm is not None)
    report = evaluate(profile, m)
    base = out_dir or p.parent
    base.mkdir(parents=True, exist_ok=True)
    html_path, pdf_path = write_sheet(report, base / f"{p.stem}.qc.html", pdf=pdf)
    (base / f"{p.stem}.qc.json").write_text(__import__("json").dumps(report_to_dict(report), indent=2))
    if log_csv is not None:
        new = not log_csv.exists()
        with log_csv.open("a", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
            if new:
                w.writeheader()
            w.writerow(
                {
                    "time": datetime.now(UTC).isoformat(timespec="seconds"),
                    "file": p.name,
                    "profile": profile.id,
                    "verdict": report.verdict,
                    "integrated_lufs": f"{m.loudness.integrated:.2f}",
                    "true_peak_dbtp": f"{m.peaks.true_peak_dbtp:.2f}",
                    "lra_lu": f"{m.loudness.lra:.2f}",
                    "duration_s": f"{m.duration_s:.3f}",
                    "failed": ";".join(f.code for f in report.findings if f.status is Status.FAIL),
                    "sheet": str(pdf_path or html_path),
                }
            )
    return report, html_path, pdf_path


class Watcher:
    """Folder state between polls. Call poll() as often as you like; files are measured once
    they have held still for stable_s seconds."""

    def __init__(
        self,
        folder: Path,
        profile: Profile,
        stable_s: float = 5.0,
        pdf: bool = False,
        out_dir: Path | None = None,
        log_csv: Path | None = None,
        redo: bool = False,
        clock: Callable[[], float] = time.time,
    ):
        self.folder = Path(folder)
        self.profile = profile
        self.stable_s = stable_s
        self.pdf = pdf
        self.out_dir = out_dir
        self.log_csv = log_csv
        self.redo = redo
        self.clock = clock
        self.seen: dict[Path, Seen] = {}
        self.done: set[Path] = set()
        self.processed = 0
        self.errors: list[tuple[Path, str]] = []

    def pending(self) -> list[Path]:
        return [p for p in self.seen if p not in self.done]

    def poll(self) -> list[tuple[Path, object, Path, Path | None]]:
        now = self.clock()
        results = []
        for p in sorted(self.folder.iterdir()):
            if not is_candidate(p) or p in self.done:
                continue
            if not self.redo and already_done(p, self.out_dir):
                self.done.add(p)
                continue
            st = p.stat()
            prev = self.seen.get(p)
            if prev is None or prev.size != st.st_size or prev.mtime != st.st_mtime:
                self.seen[p] = Seen(st.st_size, st.st_mtime, first_stable=now)
                continue
            if prev.first_stable is not None and now - prev.first_stable >= self.stable_s:
                try:
                    report, html_path, pdf_path = process(p, self.profile, self.out_dir, self.pdf, self.log_csv)
                except Exception as e:  # a broken file must not stop the watcher
                    self.errors.append((p, str(e)))
                    self.done.add(p)
                    continue
                self.done.add(p)
                self.processed += 1
                results.append((p, report, html_path, pdf_path))
        return results


def watch(
    folder: Path,
    profile: Profile,
    interval_s: float = 2.0,
    stable_s: float = 5.0,
    pdf: bool = False,
    out_dir: Path | None = None,
    log_csv: Path | None = None,
    once: bool = False,
    redo: bool = False,
    on_result: Callable[[Path, object, Path, Path | None], None] | None = None,
    on_status: Callable[[str], None] | None = None,
    clock: Callable[[], float] = time.time,
    sleep: Callable[[float], None] = time.sleep,
) -> int:
    """Run until interrupted. With once=True, return as soon as every file present has been
    measured or has held still (a file still growing keeps the pass alive)."""
    w = Watcher(folder, profile, stable_s=stable_s, pdf=pdf, out_dir=out_dir, log_csv=log_csv, redo=redo, clock=clock)
    if on_status:
        on_status(
            f"watching {folder} against {profile.name}; files are measured {stable_s:g} s after they stop growing"
        )
    reported_errors = 0
    while True:
        for p, report, html_path, pdf_path in w.poll():
            if on_result:
                on_result(p, report, html_path, pdf_path)
        if on_status and len(w.errors) > reported_errors:
            for p, msg in w.errors[reported_errors:]:
                on_status(f"could not measure {p.name}: {msg}")
            reported_errors = len(w.errors)
        if once and not w.pending():
            return w.processed
        sleep(interval_s if not once else min(interval_s, stable_s))
