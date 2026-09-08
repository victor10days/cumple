"""The desktop app's Python side, headless: jobs, diff, the watch thread, settings, the CLI hint and the window build.

pywebview is never imported for real; the window test installs a stub module and checks what the app asks of it.
"""

from __future__ import annotations

import csv
import re
import sys
import time
import types
from pathlib import Path

import numpy as np
import soundfile as sf
from typer.testing import CliRunner

import cumple
from cumple.app import desktop, selftest
from cumple.app.api import FAMILY_ORDER, Api, expand_paths
from cumple.cli import app as cli
from cumple.report.style import tokens_css
from cumple.specs import load_all
from tests.test_engine import tone_file

runner = CliRunner()
UI = Path(cumple.__file__).parent / "app" / "ui"


def wait_for(cond, timeout=90.0, step=0.05):
    end = time.time() + timeout
    while time.time() < end:
        if cond():
            return True
        time.sleep(step)
    return False


def finished(api, job_id):
    return wait_for(lambda: api.job(job_id)["state"] in ("done", "cancelled"))


def noise(path, seed, seconds=3.0, gain=0.1, sr=48000):
    x = np.random.default_rng(seed).standard_normal((int(sr * seconds), 2)) * gain
    sf.write(path, x, sr, subtype="PCM_24")
    return x


def test_profiles_are_grouped_by_family_with_grades():
    rows = Api().profiles()["profiles"]
    assert len(rows) == len(load_all())
    order = [FAMILY_ORDER.index(r["family"]) for r in rows]
    assert order == sorted(order)
    for fam in {r["family"] for r in rows}:
        ids = [r["id"] for r in rows if r["family"] == fam]
        assert ids == sorted(ids)
    assert all(r["grade"] and r["name"] and "loudness" in r for r in rows)


def test_explain_returns_rules_clauses_and_sources():
    e = Api().explain("netflix-2.0")
    assert e["ok"] and e["clauses"] and e["rules"] and e["grade"] == "READ"
    assert all(s["grade"] and s["retrieved"] and s["role"] for s in e["provenance"])
    assert "Did you mean" in Api().explain("netflx")["error"]


def test_start_checks_writes_the_sheet_and_reports_findings(tmp_path):
    hot = tmp_path / "hot.wav"
    tone_file(hot, dbfs=-0.4)
    api = Api()
    r = api.start_checks([str(hot)], "netflix-2.0")
    assert r["ok"] and r["items"] == 1 and finished(api, r["job"])
    j = api.job(r["job"])
    item = j["items"][0]
    assert j["state"] == "done" and item["state"] == "done" and item["verdict"] == "FAIL"
    assert item["sheet"].endswith("hot.qc.html") and Path(item["sheet"]).is_file() and Path(item["json"]).is_file()
    assert {"code", "status", "what", "measured", "limit"} <= set(item["findings"][0])
    assert item["failed"] and item["fixes"] and item["layout"] == "stereo"
    assert "Netflix" in api.sheet_html(item["sheet"])["html"]
    assert api.sheet_html(str(hot))["ok"] is False
    assert api.start_checks([str(hot)], "netflx")["ok"] is False
    assert api.start_checks([str(tmp_path / "nothing.wav")], "ebu-r128")["ok"] is False


def test_a_folder_of_bounces_expands_but_a_package_stays_one_item(tmp_path):
    bounces = tmp_path / "bounces"
    bounces.mkdir()
    tone_file(bounces / "a.wav")
    tone_file(bounces / "b.wav")
    (bounces / ".DS_Store").write_bytes(b"\0")
    (bounces / "c.wav.part").write_bytes(b"\0")
    (bounces / "notes.txt").write_text("x")
    items = expand_paths([str(bounces) + "/"])
    assert [i["name"] for i in items] == ["a.wav", "b.wav"] and all(i["kind"] == "file" for i in items)
    pkg = tmp_path / "EP_delivery"
    pkg.mkdir()
    tone_file(pkg / "EP_L.wav", channels=1)
    tone_file(pkg / "EP_R.wav", channels=1)
    items = expand_paths([str(pkg), str(pkg / "EP_L.wav"), str(pkg / "EP_L.wav")])
    assert [i["kind"] for i in items] == ["package", "file"]
    api = Api()
    r = api.start_checks([str(pkg)], "ebu-r128")
    assert finished(api, r["job"])
    item = api.job(r["job"])["items"][0]
    assert item["state"] == "done" and item["sheet"] == str(pkg / "EP_delivery.qc.html")


def test_an_unreadable_file_is_an_error_row_not_a_dead_job(tmp_path):
    bad = tmp_path / "garbage.wav"
    bad.write_bytes(b"RIFF" + b"\0" * 100)
    tone_file(tmp_path / "fine.wav")
    api = Api()
    r = api.start_checks([str(bad), str(tmp_path / "fine.wav")], "ebu-r128")
    assert finished(api, r["job"])
    j = api.job(r["job"])
    assert j["state"] == "done" and {i["name"]: i["state"] for i in j["items"]} == {
        "garbage.wav": "error",
        "fine.wav": "done",
    }
    assert "cannot measure garbage.wav" in next(i["error"] for i in j["items"] if i["state"] == "error")


def test_cancel_skips_the_queued_items(tmp_path):
    paths = []
    for i in range(4):
        p = tmp_path / f"t{i}.wav"
        tone_file(p, seconds=30.0)
        paths.append(str(p))
    api = Api()
    r = api.start_checks(paths, "ebu-r128")
    assert api.cancel(r["job"])["ok"]
    assert finished(api, r["job"])
    j = api.job(r["job"])
    assert j["state"] == "cancelled" and any(i["state"] == "skipped" for i in j["items"])
    assert api.cancel("nope")["ok"] is False and api.job("nope")["ok"] is False


def test_out_dir_moves_the_sheet(tmp_path):
    tone_file(tmp_path / "m.wav")
    api = Api()
    r = api.start_checks([str(tmp_path / "m.wav")], "ebu-r128", out_dir=str(tmp_path / "out"))
    assert finished(api, r["job"])
    item = api.job(r["job"])["items"][0]
    assert Path(item["sheet"]) == tmp_path / "out" / "m.qc.html" and Path(item["json"]).is_file()


def test_diff_in_words_and_stems_null(tmp_path):
    a = noise(tmp_path / "v12.wav", 1)
    sf.write(tmp_path / "v13.wav", a * 10 ** (-1.5 / 20), 48000, subtype="PCM_24")
    api = Api()
    r = api.diff(str(tmp_path / "v12.wav"), str(tmp_path / "v13.wav"))
    assert r["ok"] and finished(api, r["job"])
    item = api.job(r["job"])["items"][0]
    assert item["state"] == "done" and "dB" in item["summary"]
    assert item["verdict"] in {"IDENTICAL", "SAME MIX", "SAME MATERIAL", "DIFFERENT"}
    assert Path(item["sheet"]).name == "v13.diff.html" and Path(item["sheet"]).is_file()
    dx = noise(tmp_path / "DX.wav", 2, gain=0.05)
    mx = noise(tmp_path / "MX.wav", 3, gain=0.05)
    fx = noise(tmp_path / "FX.wav", 4, gain=0.05)
    sf.write(tmp_path / "PM.wav", dx + mx + fx, 48000, subtype="PCM_24")
    r = api.stems([str(tmp_path / n) for n in ("DX.wav", "MX.wav", "FX.wav")], str(tmp_path / "PM.wav"))
    assert r["ok"] and finished(api, r["job"])
    item = api.job(r["job"])["items"][0]
    assert item["verdict"] == "NULLS" and item["nulls"] and Path(item["sheet"]).name == "PM.diff.html"
    assert api.stems([], str(tmp_path / "PM.wav"))["ok"] is False
    assert api.diff(str(tmp_path / "v12.wav"), str(tmp_path / "missing.wav"))["ok"] is False


def test_diff_refuses_files_over_the_memory_cap(tmp_path, monkeypatch):
    import cumple.app.api as api_mod

    tone_file(tmp_path / "a.wav")
    tone_file(tmp_path / "b.wav")
    monkeypatch.setattr(api_mod.sf, "info", lambda p: types.SimpleNamespace(duration=41 * 60))
    r = Api().diff(str(tmp_path / "a.wav"), str(tmp_path / "b.wav"))
    assert r["ok"] is False and "40 minutes" in r["error"]


def test_watch_thread_measures_a_file_that_lands_and_stops(tmp_path):
    folder = tmp_path / "bounces"
    folder.mkdir()
    api = Api()
    assert api.watch_status()["running"] is False
    w = api.watch_start(str(folder), "ebu-r128", stable_s=0.0, interval_s=0.05)
    assert w["ok"] and w["log_csv"] == str(folder / "cumple-log.csv")
    assert api.watch_start(str(folder), "ebu-r128")["ok"] is False
    tone_file(folder / "bounce.wav")
    assert wait_for(lambda: api.watch_status().get("processed", 0) == 1, timeout=30)
    s = api.watch_status()
    row = s["rows"][-1]
    assert s["running"] and row["file"] == "bounce.wav" and row["verdict"] == "PASS" and Path(row["sheet"]).is_file()
    with open(folder / "cumple-log.csv", newline="") as f:
        assert len(list(csv.DictReader(f))) == 1
    api.watch_stop()
    assert wait_for(lambda: api.watch_status()["running"] is False, timeout=5)
    assert api.watch_start(str(tmp_path / "nowhere"), "ebu-r128")["ok"] is False


def test_settings_round_trip(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    api = Api()
    api.remember(spec="ebu-r128", pdf=True, out_dir=str(tmp_path / "out"))
    assert desktop.settings_path() == tmp_path / "cumple" / "app.json"
    info = api.info()
    assert info["last_spec"] == "ebu-r128" and info["pdf"] is True and info["out_dir"] == str(tmp_path / "out")
    api.remember(out_dir="")
    assert not api.info()["out_dir"] and api.info()["last_spec"] == "ebu-r128"
    assert info["version"] == cumple.__version__ and info["diff_cap_minutes"] == 40


def test_info_carries_the_initial_paths_and_spec():
    api = Api(initial_paths=[Path("/x/a.wav")], initial_spec="ebu-r128")
    assert api.info()["initial"] == {"paths": [str(Path("/x/a.wav"))], "spec": "ebu-r128"}


def test_reveal_command_per_platform(tmp_path):
    p = str(Path("/x/a.wav"))  # the separator the host uses; the test runs on Windows too
    assert desktop.reveal_command("/x/a.wav", "Darwin") == ["open", "-R", p]
    assert desktop.reveal_command("/x/a.wav", "Windows") == ["explorer", "/select,", p]
    assert desktop.reveal_command(str(tmp_path / "a.wav"), "Linux") == ["xdg-open", str(tmp_path)]
    assert desktop.reveal_command(str(tmp_path), "Linux") == ["xdg-open", str(tmp_path)]


def test_webview2_precheck_reads_both_hives_and_wow6432node():
    def only_hkcu_wow(hive, key, value):
        return "120.0.1" if hive == "HKCU" and "WOW6432Node" in key and value == "pv" else None

    assert desktop.webview2_installed(only_hkcu_wow) is True
    assert desktop.webview2_installed(lambda h, k, v: None) is False
    assert desktop.webview2_installed(lambda h, k, v: "0.0.0.0") is False


def test_selftest_reports_profiles_fonts_and_a_passing_tone():
    r = selftest.run()
    assert r["profiles"] >= 39 and r["fonts"] == 5 and r["verdict"] == "PASS" and selftest.ok(r)


def test_cli_app_hints_when_pywebview_is_missing(monkeypatch):
    monkeypatch.setitem(sys.modules, "webview", None)
    r = runner.invoke(cli, ["app"])
    assert r.exit_code == 2 and "cumple[app]" in r.stdout
    assert runner.invoke(cli, ["app", "--help"]).exit_code == 0
    r = runner.invoke(cli, ["app", "--spec", "netflx"])
    assert r.exit_code == 2 and "Did you mean" in r.stdout


def test_main_run_builds_the_window_with_a_stub_webview(monkeypatch, tmp_path):
    calls = {}

    class Handlers(list):
        def __iadd__(self, h):
            self.append(h)
            return self

    class Events:
        def __init__(self):
            self.__dict__["_h"] = {}

        def __getattr__(self, name):
            return self._h.setdefault(name, Handlers())

        def __setattr__(self, name, value):
            self._h[name] = value

    class Window:
        def __init__(self, title, **kw):
            calls["window"] = dict(kw, title=title)
            self.events = Events()
            self.dom = types.SimpleNamespace(document=types.SimpleNamespace(events=Events()))
            self.js = []

        def run_js(self, code):
            self.js.append(code)

    def create_window(title, **kw):
        calls["w"] = Window(title, **kw)
        return calls["w"]

    def start(func=None, args=None, **kw):
        calls["start"] = kw
        if func is not None:
            func(args)

    stub = types.ModuleType("webview")
    stub.create_window, stub.start, stub.settings = create_window, start, {}
    dom = types.ModuleType("webview.dom")
    dom.DOMEventHandler = lambda fn, *a, **k: fn
    menu = types.ModuleType("webview.menu")
    menu.Menu = lambda title, items=(): ("menu", title, list(items))
    menu.MenuAction = lambda title, fn: ("action", title, fn)
    menu.MenuSeparator = lambda: ("sep",)
    stub.dom, stub.menu = dom, menu
    for name, mod in (("webview", stub), ("webview.dom", dom), ("webview.menu", menu)):
        monkeypatch.setitem(sys.modules, name, mod)
    monkeypatch.setattr(desktop, "log_path", lambda: tmp_path / "app.log")
    from cumple.app import main as app_main

    assert app_main.run([Path("/x/a.wav")], None) == 0
    kw = calls["window"]
    assert kw["title"] == "cumple" and kw["text_select"] is True and kw["min_size"] == (760, 520)
    assert 'id="sheet"' in kw["html"] and tokens_css() in kw["html"] and "/*__" not in kw["html"]
    assert isinstance(kw["js_api"], Api) and kw["js_api"].info()["initial"]["paths"] == [str(Path("/x/a.wav"))]
    assert kw["js_api"].window is calls["w"]
    assert calls["start"]["gui"] is None and Path(calls["start"]["icon"]).is_file()
    assert [m[1] for m in calls["start"]["menu"]] == ["File", "Help"]
    w = calls["w"]
    drop = w.dom.document.events.drop[0]
    drop({"dataTransfer": {"files": [{"name": "a.wav", "pywebviewFullPath": "/x/a.wav/"}, {"name": "b.wav"}]}})
    assert w.js[-1] == 'app.onDrop(["/x/a.wav"], 2)'
    assert w.events.closing[0]() is True
    assert (tmp_path / "app.log").read_text().count("starting") == 1
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "platform", "linux")
    assert app_main.run([], None) == 0
    assert calls["start"]["gui"] == "qt" and calls["start"]["icon"].endswith("icon.png")
    assert app_main.main(["--spec", "ebu-r128", "x.wav", "-psn_0_1"]) == 0
    assert calls["window"]["js_api"].info()["initial"] == {"paths": ["x.wav"], "spec": "ebu-r128"}


def test_ui_assets_follow_the_design_system():
    css = (UI / "app.css").read_text(encoding="utf-8")
    html = (UI / "index.html").read_text(encoding="utf-8")
    js = (UI / "app.js").read_text(encoding="utf-8")
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", css)
    assert "oklch(" not in css and "rgb(" not in css and "hsl(" not in css
    assert re.search(r"font-family:\s*\"", css) is None
    assert "overflow-x: clip" in css
    for marker in ("/*__TOKENS__*/", "/*__FONTS__*/", "/*__APP_CSS__*/", "/*__APP_JS__*/"):
        assert marker in html
    for text in (html, js, css):
        assert "–" not in text and "—" not in text
    assert "pywebviewready" in js and "import " not in js and "require(" not in js
    assert (UI / "icon.png").is_file() and (UI / "icon.icns").is_file() and (UI / "icon.ico").is_file()
