"""The PDF printer and the sheet's destination, exercised without a browser."""

from __future__ import annotations

import subprocess
from pathlib import Path

from cumple.report import qc_sheet
from cumple.report.qc_sheet import chrome_candidates, find_chrome, sheet_target, to_pdf


def test_sheet_target_matches_the_cli_convention(tmp_path):
    f = tmp_path / "mix.wav"
    assert sheet_target(f) == tmp_path / "mix.qc.html"
    assert sheet_target(f).with_suffix(".json") == tmp_path / "mix.qc.json"
    d = tmp_path / "EP101_delivery"
    d.mkdir()
    assert sheet_target(d) == d / "EP101_delivery.qc.html"
    out = tmp_path / "out"
    assert sheet_target(f, out) == out / "mix.qc.html"
    assert sheet_target(d, out) == out / "EP101_delivery.qc.html"


def test_chrome_candidates_prefer_chrome_over_edge_per_platform():
    mac = chrome_candidates("Darwin", {})
    assert "Google Chrome" in mac[0] and mac[-1].endswith("Microsoft Edge")
    win = chrome_candidates(
        "Windows",
        {
            "LOCALAPPDATA": r"C:\Users\v\AppData\Local",
            "PROGRAMFILES": r"C:\Program Files",
            "PROGRAMFILES(X86)": r"C:\Program Files (x86)",
        },
    )
    assert win[0] == r"C:\Users\v\AppData\Local\Google\Chrome\Application\chrome.exe"
    assert win[1] == r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    assert win[-1] == r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    assert all("Chrome" in p for p in win[:3])
    assert chrome_candidates("Windows", {}) == []  # no roots, no guesses
    linux = chrome_candidates("Linux", {})
    assert linux[0] == "/opt/google/chrome/chrome" and linux[-1].endswith("msedge")


def test_find_chrome_falls_back_to_the_path_and_then_to_none(monkeypatch):
    monkeypatch.setattr(qc_sheet, "chrome_candidates", lambda *a, **k: ["/nowhere/chrome"])
    monkeypatch.setattr(qc_sheet.shutil, "which", lambda name: None)
    assert find_chrome() is None
    monkeypatch.setattr(
        qc_sheet.shutil,
        "which",
        lambda name: "/usr/bin/google-chrome-stable" if name == "google-chrome-stable" else None,
    )
    assert find_chrome() == "/usr/bin/google-chrome-stable"


def test_to_pdf_prints_headless_with_no_throwaway_profile(monkeypatch, tmp_path):
    seen = {}

    def fake_run(cmd, check, capture_output, timeout):
        seen["cmd"] = cmd
        out = next(a for a in cmd if a.startswith("--print-to-pdf=")).split("=", 1)[1]
        Path(out).write_bytes(b"%PDF-1.4 fake")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(qc_sheet, "find_chrome", lambda: "/fake/chrome")
    monkeypatch.setattr(qc_sheet.subprocess, "run", fake_run)
    html = tmp_path / "mix.qc.html"
    html.write_text("<html></html>")
    pdf = tmp_path / "mix.qc.pdf"
    assert to_pdf(html, pdf) is True
    cmd = seen["cmd"]
    assert cmd[0] == "/fake/chrome" and "--headless" in cmd and "--no-pdf-header-footer" in cmd
    assert "--virtual-time-budget=5000" in cmd and cmd[-1] == html.resolve().as_uri()
    assert not any(a.startswith("--user-data-dir") for a in cmd)  # a fresh profile makes Chrome hang after printing
    assert pdf.read_bytes().startswith(b"%PDF")


def test_to_pdf_reports_failure_when_nothing_is_written(monkeypatch, tmp_path):
    html = tmp_path / "mix.qc.html"
    html.write_text("<html></html>")
    monkeypatch.setattr(qc_sheet, "find_chrome", lambda: "/fake/chrome")
    monkeypatch.setattr(qc_sheet.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a, 0))
    assert to_pdf(html, tmp_path / "mix.qc.pdf") is False
    monkeypatch.setattr(qc_sheet, "find_chrome", lambda: None)
    assert to_pdf(html, tmp_path / "mix.qc.pdf") is False
