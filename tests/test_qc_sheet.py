from __future__ import annotations

from cumple.checks import evaluate
from cumple.meters.measure import measure
from cumple.report import render_html, write_sheet
from cumple.specs import get
from tests.test_engine import tone_file


def test_sheet_renders_findings_timeline_and_sources(tmp_path):
    p = tone_file(tmp_path / "hot.wav", dbfs=-0.4, seconds=12)
    report = evaluate(get("netflix-2.0"), measure(p))
    html = render_html(report)
    assert "FAIL" in html and "Netflix stereo" in html
    assert "<svg" in html and "integrated" in html
    assert "true peak" in html and "lower by" in html
    assert "partnerhelp.netflixstudios.com" in html
    out, pdf = write_sheet(report, tmp_path / "hot.qc.html")
    assert out.exists() and out.stat().st_size > 5000 and pdf is None
