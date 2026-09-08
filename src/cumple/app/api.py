"""The desktop app's Python side: everything the window's JavaScript can call.

pywebview runs every call on its own thread, so nothing here blocks: measuring goes through one
worker thread and a job the window polls; the watch folder runs on its own thread and publishes a
snapshot after each poll. Every method returns a dict with "ok", so a failure is a sentence in the
window rather than a rejected promise nobody can read. The engine is untouched: the same
`measure`, `evaluate`, `write_sheet`, `Watcher` and diff functions the CLI calls.
"""

from __future__ import annotations

import copy
import json
import logging
import platform
import queue
import sys
import threading
import uuid
import webbrowser
from datetime import UTC, datetime
from pathlib import Path

import soundfile as sf

from .. import __version__
from ..checks.engine import Status, evaluate
from ..diff.compare import MAX_SECONDS_IN_MEMORY, diff_files, sum_stems_against
from ..diff.render import describe, diff_to_dict
from ..io.reader import load_package
from ..meters.measure import measure, measure_args
from ..report.diff_sheet import verdict as diff_verdict
from ..report.diff_sheet import write_diff_sheet
from ..report.json_out import report_to_dict
from ..report.qc_sheet import find_chrome, sheet_target, to_pdf, write_sheet
from ..specs.registry import ProfileNotFound, get, load_all
from ..watch import Watcher, is_candidate
from . import desktop

log = logging.getLogger("cumple.app.api")

FAMILY_ORDER = ["streaming", "broadcast", "cinema", "music", "podcast", "audiobook", "standard"]
AUDIO_FILTER = "Audio files (*.wav;*.bwf;*.rf64;*.w64;*.aif;*.aiff;*.flac)"  # the description must match [\w ]+
ALL_FILES = "All files (*.*)"
REPO_URL = "https://github.com/victor10days/cumple"
SITE_URL = "https://cumple-uxa7.onrender.com/"
NO_PDF = "no Chrome, Chromium or Edge found, or printing failed; the HTML sheet is the deliverable"


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _fmt(x: float | None, digits: int = 1, signed: bool = False) -> str:
    if x is None or x != x or x in (float("inf"), float("-inf")):
        return "silence" if x is not None and x == float("-inf") else "n/a"
    return f"{x:+.{digits}f}" if signed else f"{x:.{digits}f}"


def _profile_error(e: ProfileNotFound, profile_id: str) -> str:
    return str(e.args[0]) if e.args else f"no profile named {profile_id!r}"


def expand_paths(paths) -> list[dict]:
    """Dropped or picked paths become check items: a file, a package directory, or a folder's audio files.

    A directory whose files carry channel roles in their names (`_L`, `_R`, `_C`, `_LFE`...) is one
    delivery package and one item; any other directory contributes its top-level audio files, with
    dotfiles, AppleDouble files and partial downloads skipped the way the watch folder skips them.
    """
    items: list[dict] = []
    seen: set[Path] = set()

    def add(p: Path, kind: str) -> None:
        if p not in seen:
            seen.add(p)
            items.append({"path": str(p), "name": p.name, "kind": kind})

    for raw in paths or []:
        p = Path(str(raw).rstrip("/\\")).expanduser()
        if p.is_dir():
            try:
                pkg = load_package(p)
            except ValueError:  # two files claim one role: not a package
                pkg = None
            if pkg is not None and pkg.files:
                add(p, "package")
            else:
                for child in sorted(p.iterdir()):
                    if is_candidate(child):
                        add(child, "file")
        elif is_candidate(p):
            add(p, "file")
    return items


def _too_long(paths) -> str | None:
    """Diff loads whole files into memory; refuse before queuing, with the sentence the engine would raise."""
    for p in paths:
        p = Path(p)
        try:
            duration = sf.info(str(p)).duration
        except Exception as e:  # unreadable, or not audio
            return f"cannot read {p.name}: {e}"
        if duration > MAX_SECONDS_IN_MEMORY:
            return (
                f"{p.name} is {duration / 60:.0f} minutes long; diff loads whole files "
                f"and stops at {MAX_SECONDS_IN_MEMORY // 60} minutes"
            )
    return None


class Api:
    """Exposed to the window as `window.pywebview.api`. Methods starting with an underscore are not."""

    def __init__(self, initial_paths=(), initial_spec: str | None = None):
        self.window = None  # set by main.run once the window exists
        self._lock = threading.Lock()
        self._jobs: dict[str, dict] = {}
        self._queue: queue.Queue[str | None] = queue.Queue()
        self._worker: threading.Thread | None = None
        self._watch: _WatchThread | None = None
        self._initial = {"paths": [str(p) for p in initial_paths], "spec": initial_spec}

    # ---- fast, synchronous -------------------------------------------------------------------------

    def info(self) -> dict:
        settings = desktop.load_settings()
        return {
            "ok": True,
            "version": __version__,
            "platform": platform.system(),
            "frozen": bool(getattr(sys, "frozen", False)),
            "chrome": find_chrome(),
            "last_spec": settings.get("spec"),
            "pdf": bool(settings.get("pdf", False)),
            "out_dir": settings.get("out_dir"),
            "initial": self._initial,
            "repo": REPO_URL,
            "site": SITE_URL,
            "diff_cap_minutes": MAX_SECONDS_IN_MEMORY // 60,
        }

    def profiles(self) -> dict:
        rows = []
        for p in load_all().values():
            rows.append(
                {
                    "id": p.id,
                    "name": p.name,
                    "family": p.family,
                    "grade": p.grade.value,
                    "has_defaults": p.has_defaults,
                    "loudness": p.loudness_compact(),
                    "peak": p.peak_summary(),
                    "summary": p.summary,
                }
            )
        rows.sort(key=lambda r: (FAMILY_ORDER.index(r["family"]) if r["family"] in FAMILY_ORDER else 99, r["id"]))
        return {"ok": True, "profiles": rows, "families": FAMILY_ORDER}

    def explain(self, profile_id: str) -> dict:
        try:
            p = get(profile_id)
        except ProfileNotFound as e:
            return {"ok": False, "error": _profile_error(e, profile_id)}
        rules = [r.describe() for r in p.loudness.rules] if p.loudness else []
        return {
            "ok": True,
            "id": p.id,
            "name": p.name,
            "family": p.family,
            "grade": p.grade.value,
            "summary": p.summary,
            "loudness": p.loudness_summary(),
            "peak": p.peak_summary(),
            "rules": rules,
            "clauses": dict(p.clauses),
            "clauses_verbatim": p.clauses_verbatim,
            "provenance": [
                {
                    "title": s.title,
                    "publisher": s.publisher,
                    "version": s.version,
                    "published": s.published,
                    "url": s.url,
                    "retrieved": s.retrieved.isoformat(),
                    "grade": s.grade.value,
                    "role": s.role,
                    "notes": s.notes,
                }
                for s in p.provenance
            ],
        }

    def sheet_html(self, path: str) -> dict:
        p = Path(path)
        if not (p.name.endswith(".qc.html") or p.name.endswith(".diff.html")) or not p.is_file():
            return {"ok": False, "error": "not a cumple sheet"}
        try:
            return {"ok": True, "html": p.read_text(encoding="utf-8")}
        except OSError as e:
            return {"ok": False, "error": str(e)}

    def open_url(self, url: str) -> dict:
        if not str(url).startswith(("http://", "https://")):
            return {"ok": False, "error": "only web links open from the sheet"}
        webbrowser.open(str(url))
        return {"ok": True}

    def open_path(self, path: str) -> dict:
        p = Path(path)
        if not p.exists():
            return {"ok": False, "error": f"{p.name} is not there any more"}
        webbrowser.open(p.resolve().as_uri())
        return {"ok": True}

    def reveal(self, path: str) -> dict:
        return {"ok": desktop.reveal(path)}

    def save_pdf(self, html_path: str) -> dict:
        html = Path(html_path)
        if not html.is_file():
            return {"ok": False, "error": "the sheet is not there any more"}
        pdf = html.with_suffix(".pdf")
        if to_pdf(html, pdf):
            return {"ok": True, "pdf": str(pdf)}
        return {"ok": False, "error": NO_PDF}

    def remember(self, spec: str | None = None, pdf: bool | None = None, out_dir: str | None = None) -> dict:
        return {"ok": True, "settings": desktop.save_settings({"spec": spec, "pdf": pdf, "out_dir": out_dir})}

    def pick_files(self) -> dict:
        if self.window is None:
            return {"ok": False, "error": "no window"}
        import webview

        result = self.window.create_file_dialog(
            webview.FileDialog.OPEN, allow_multiple=True, file_types=(AUDIO_FILTER, ALL_FILES)
        )
        return {"ok": True, "paths": [str(p) for p in (result or [])]}

    def pick_folder(self) -> dict:
        if self.window is None:
            return {"ok": False, "error": "no window"}
        import webview

        result = self.window.create_file_dialog(webview.FileDialog.FOLDER)
        return {"ok": True, "paths": [str(p) for p in (result or [])]}

    # ---- jobs: one worker, one file at a time, the window polls ------------------------------------

    def start_checks(self, paths, spec: str, pdf: bool = False, out_dir: str | None = None) -> dict:
        try:
            get(spec)
        except ProfileNotFound as e:
            return {"ok": False, "error": _profile_error(e, spec)}
        items = expand_paths(paths)
        if not items:
            return {"ok": False, "error": "nothing to check: no audio file, package or folder of bounces in the drop"}
        job = self._new_job("check", spec=spec, pdf=bool(pdf), out_dir=str(out_dir) if out_dir else None, items=items)
        return {"ok": True, "job": job["id"], "items": len(items)}

    def diff(self, a: str, b: str, pdf: bool = False, max_offset: float = 10.0) -> dict:
        for p in (a, b):
            if not Path(p).is_file():
                return {"ok": False, "error": f"{Path(p).name} is not a file"}
        err = _too_long([a, b])
        if err:
            return {"ok": False, "error": err}
        item = {
            "path": str(b),
            "name": f"{Path(b).name} against {Path(a).name}",
            "kind": "diff",
            "a": str(a),
            "b": str(b),
            "max_offset": float(max_offset),
        }
        job = self._new_job("diff", pdf=bool(pdf), items=[item])
        return {"ok": True, "job": job["id"]}

    def stems(self, stems, against: str, pdf: bool = False, max_offset: float = 2.0) -> dict:
        stems = [str(s) for s in (stems or [])]
        if not stems:
            return {"ok": False, "error": "drop the stems first, then the printmaster"}
        for p in [*stems, against]:
            if not Path(p).is_file():
                return {"ok": False, "error": f"{Path(p).name} is not a file"}
        err = _too_long([*stems, against])
        if err:
            return {"ok": False, "error": err}
        item = {
            "path": str(against),
            "name": f"{len(stems)} stems against {Path(against).name}",
            "kind": "stems",
            "stems": stems,
            "against": str(against),
            "max_offset": float(max_offset),
        }
        job = self._new_job("diff", pdf=bool(pdf), items=[item])
        return {"ok": True, "job": job["id"]}

    def job(self, job_id: str) -> dict:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return {"ok": False, "error": "no such job"}
            public = {k: copy.deepcopy(v) for k, v in job.items() if not k.startswith("_")}
        public["ok"] = True
        return public

    def cancel(self, job_id: str) -> dict:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return {"ok": False, "error": "no such job"}
            job["_cancel"].set()
            for it in job["items"]:
                if it["state"] == "queued":
                    it["state"] = "skipped"
        return {"ok": True}

    def _new_job(self, kind: str, **fields) -> dict:
        job = {"id": uuid.uuid4().hex[:8], "type": kind, "state": "queued", "created": _now(), **fields}
        for it in job["items"]:
            it["state"] = "queued"
        job["_cancel"] = threading.Event()
        with self._lock:
            self._jobs[job["id"]] = job
        self._queue.put(job["id"])
        self._ensure_worker()
        return job

    def _ensure_worker(self) -> None:
        if self._worker is None or not self._worker.is_alive():
            self._worker = threading.Thread(target=self._run_queue, name="cumple-worker", daemon=True)
            self._worker.start()

    def _run_queue(self) -> None:
        while True:
            job_id = self._queue.get()
            if job_id is None:
                return
            with self._lock:
                job = self._jobs[job_id]
                job["state"] = "running"
            for item in job["items"]:
                if job["_cancel"].is_set():
                    with self._lock:
                        if item["state"] == "queued":
                            item["state"] = "skipped"
                    continue
                with self._lock:
                    item["state"] = "running"
                try:
                    if job["type"] == "check":
                        self._check_one(job, item)
                    else:
                        self._diff_one(job, item)
                except Exception as e:  # unreadable file, inconsistent package, libsndfile errors
                    log.exception("job %s: %s failed", job_id, item.get("name"))
                    with self._lock:
                        item.update(state="error", error=f"cannot measure {item.get('name')}: {e}")
            with self._lock:
                job["state"] = "cancelled" if job["_cancel"].is_set() else "done"
                job["finished"] = _now()

    def _check_one(self, job: dict, item: dict) -> None:
        profile = get(job["spec"])
        path = Path(item["path"])
        m = measure(path, **measure_args(profile))
        report = evaluate(profile, m)
        target = sheet_target(path, Path(job["out_dir"]) if job.get("out_dir") else None)
        target.parent.mkdir(parents=True, exist_ok=True)
        html_path, pdf_path = write_sheet(report, target, pdf=job["pdf"])
        d = report_to_dict(report)
        json_path = target.with_suffix(".json")
        json_path.write_text(json.dumps(d, indent=2), encoding="utf-8")
        with self._lock:
            item.update(
                state="done",
                verdict=report.verdict,
                layout=m.layout,
                duration_s=round(m.duration_s, 3),
                measurement=d["measurement"],
                findings=d["findings"],
                fixes=report.fixes(),
                failed=[f["what"] for f in d["findings"] if f["status"] == Status.FAIL.value],
                sheet=str(html_path),
                pdf=str(pdf_path) if pdf_path else None,
                pdf_error=NO_PDF if job["pdf"] and not pdf_path else None,
                json=str(json_path),
            )

    def _diff_one(self, job: dict, item: dict) -> None:
        if item["kind"] == "stems":
            r = sum_stems_against(
                [Path(s) for s in item["stems"]], Path(item["against"]), max_offset_s=item["max_offset"]
            )
            target = Path(item["against"])
        else:
            r = diff_files(Path(item["a"]), Path(item["b"]), max_offset_s=item["max_offset"])
            target = Path(item["b"])
        html = target.parent / f"{target.stem}.diff.html"
        html_path, pdf_path = write_diff_sheet(r, html, pdf=job["pdf"])
        d = diff_to_dict(r)
        json_path = html.with_suffix(".json")
        json_path.write_text(json.dumps(d, indent=2), encoding="utf-8")
        stamp, cls = diff_verdict(r)
        with self._lock:
            item.update(
                state="done",
                summary=describe(r),
                verdict=stamp,
                verdict_class=cls,
                nulls=bool(r.identical or r.residual_dbfs < -60),
                result=d,
                sheet=str(html_path),
                pdf=str(pdf_path) if pdf_path else None,
                pdf_error=NO_PDF if job["pdf"] and not pdf_path else None,
                json=str(json_path),
            )

    # ---- the watch folder ----------------------------------------------------------------------------

    def watch_start(
        self,
        folder: str,
        spec: str,
        pdf: bool = False,
        out_dir: str | None = None,
        stable_s: float = 5.0,
        interval_s: float = 2.0,
        redo: bool = False,
    ) -> dict:
        if self._watch is not None and self._watch.is_alive():
            return {"ok": False, "error": "already watching; stop it first"}
        f = Path(str(folder).rstrip("/\\")).expanduser()
        if not f.is_dir():
            return {"ok": False, "error": f"{f} is not a folder"}
        try:
            profile = get(spec)
        except ProfileNotFound as e:
            return {"ok": False, "error": _profile_error(e, spec)}
        out = Path(out_dir) if out_dir else None
        log_csv = (out or f) / "cumple-log.csv"
        watcher = Watcher(
            f, profile, stable_s=float(stable_s), pdf=bool(pdf), out_dir=out, log_csv=log_csv, redo=bool(redo)
        )
        self._watch = _WatchThread(watcher, float(interval_s), spec)
        self._watch.start()
        return {"ok": True, "folder": str(f), "log_csv": str(log_csv)}

    def watch_status(self) -> dict:
        if self._watch is None:
            return {"ok": True, "running": False, "rows": [], "processed": 0, "pending": 0}
        return {"ok": True, **self._watch.snapshot()}

    def watch_stop(self) -> dict:
        if self._watch is not None:
            self._watch.stop.set()
        return {"ok": True}

    def shutdown(self) -> None:
        """Called from the window's closing event: stop everything, join nothing (the threads are daemons)."""
        with self._lock:
            for job in self._jobs.values():
                job["_cancel"].set()
        if self._watch is not None:
            self._watch.stop.set()
        self._queue.put(None)


class _WatchThread(threading.Thread):
    """Owns its Watcher: only this thread touches it, and it publishes an immutable snapshot after each poll."""

    def __init__(self, watcher: Watcher, interval_s: float, spec: str):
        super().__init__(name="cumple-watch", daemon=True)
        self.watcher = watcher
        self.interval = max(0.05, interval_s)
        self.spec = spec
        self.stop = threading.Event()
        self.rows: list[dict] = []
        self._errors_seen = 0
        self._snapshot: dict = {
            "running": False,
            "folder": str(watcher.folder),
            "spec": spec,
            "log_csv": str(watcher.log_csv) if watcher.log_csv else None,
            "processed": 0,
            "pending": 0,
            "rows": [],
        }

    def run(self) -> None:
        self._publish(running=True)
        while not self.stop.is_set():
            try:
                results = self.watcher.poll()
            except Exception as e:  # the folder vanished, a permissions change
                log.exception("watch poll failed")
                self._publish(running=False, error=str(e))
                return
            for p, report, html_path, pdf_path in results:
                m = report.measurement
                self.rows.append(
                    {
                        "time": _now(),
                        "file": p.name,
                        "verdict": report.verdict,
                        "integrated_lufs": _fmt(m.loudness.integrated, 1),
                        "true_peak_dbtp": _fmt(m.peaks.true_peak_dbtp, 1, signed=True),
                        "failed": [f.what for f in report.findings if f.status is Status.FAIL],
                        "sheet": str(pdf_path or html_path),
                        "html": str(html_path),
                    }
                )
            for p, msg in self.watcher.errors[self._errors_seen :]:
                self.rows.append(
                    {"time": _now(), "file": p.name, "verdict": "ERROR", "error": msg, "failed": [], "sheet": None}
                )
            self._errors_seen = len(self.watcher.errors)
            self._publish(running=True)
            self.stop.wait(self.interval)
        self._publish(running=False)

    def _publish(self, **fields) -> None:
        self._snapshot = {
            **self._snapshot,
            "processed": self.watcher.processed,
            "pending": len(self.watcher.pending()),
            "rows": list(self.rows[-200:]),
            **fields,
        }

    def snapshot(self) -> dict:
        return self._snapshot
