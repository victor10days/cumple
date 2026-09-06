from __future__ import annotations

import math
import re

from cumple.checks import evaluate
from cumple.meters.measure import measure
from cumple.report import render_html, write_sheet
from cumple.report.style import FONTS, document_css, tokens_css
from cumple.specs import get
from tests.test_engine import tone_file


def test_sheet_renders_findings_timeline_and_sources(tmp_path):
    p = tone_file(tmp_path / "hot.wav", dbfs=-0.4, seconds=12)
    report = evaluate(get("netflix-2.0"), measure(p))
    html = render_html(report)
    assert "FAIL" in html and "Netflix stereo" in html
    assert "<svg" in html and "integrated" in html
    assert "true peak" in html and "lower by" in html
    assert "studiopartner.netflix.net" in html
    out, pdf = write_sheet(report, tmp_path / "hot.qc.html")
    assert out.exists() and out.stat().st_size > 5000 and pdf is None


def test_sheet_stacks_on_phones_and_labels_its_figure(tmp_path):
    p = tone_file(tmp_path / "hot.wav", dbfs=-0.4, seconds=12)
    html = render_html(evaluate(get("netflix-2.0"), measure(p)))
    assert 'name="viewport"' in html
    assert html.count('data-h="Measured"') >= 8 and html.count('data-h="Limit"') >= 8
    # the timeline's tick labels are HTML positioned over the SVG, not text inside it
    assert 'class="lab y"' in html and 'class="lab x"' in html
    assert "<text" not in html.split("<svg")[1].split("</svg>")[0]


def test_duration_rounds_before_splitting_minutes():
    from cumple.report.qc_sheet import _mmss

    assert _mmss(59.97) == "1:00.0"
    assert _mmss(119.98) == "2:00.0"
    assert _mmss(12.0) == "0:12.0"
    assert _mmss(0.04) == "0:00.0"


def test_fonts_travel_inside_the_document():
    css = document_css()
    assert css.count("@font-face") == len(FONTS) == 5
    assert css.count("data:font/woff2;base64,") == 5
    for family in ("Barlow Condensed", "IBM Plex Sans", "IBM Plex Mono"):
        assert f'font-family: "{family}"' in css


def test_no_colour_outside_the_token_block():
    """Every colour in the document CSS is a var(); hex or oklch literals live only in tokens.css."""
    css = document_css()
    rules = css.replace(tokens_css(), "")
    rules = re.sub(r"@font-face\s*\{[^}]*\}", "", rules)  # the embedded faces name themselves, once each
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", rules)
    assert "oklch(" not in rules and "rgb(" not in rules
    assert re.search(r"font-family:\s*\"", rules) is None  # faces only through var(--font-*)


# --- contrast of the token pairs the sheets actually render -------------------------------------


def _oklch_to_luminance(L: float, C: float, h_deg: float) -> float:
    h = math.radians(h_deg)
    a, b = C * math.cos(h), C * math.sin(h)
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    lu, mu, su = l_**3, m_**3, s_**3
    r = 4.0767416621 * lu - 3.3077115913 * mu + 0.2309699292 * su
    g = -1.2684380046 * lu + 2.6097574011 * mu - 0.3413193965 * su
    bl = -0.0041960863 * lu - 0.7034186147 * mu + 1.7076147010 * su
    r, g, bl = (min(max(x, 0.0), 1.0) for x in (r, g, bl))
    return 0.2126 * r + 0.7152 * g + 0.0722 * bl


def _light_tokens() -> dict[str, float]:
    root = tokens_css().split(":root")[1].split("\n}")[0]
    out = {}
    for name, L, C, h in re.findall(r"--color-([a-z0-9-]+):\s*oklch\(([\d.]+)%\s+([\d.]+)\s+([\d.]+)\)", root):
        out[name] = _oklch_to_luminance(float(L) / 100, float(C), float(h))
    return out


def _ratio(y1: float, y2: float) -> float:
    hi, lo = max(y1, y2), min(y1, y2)
    return (hi + 0.05) / (lo + 0.05)


def test_token_pairs_clear_wcag():
    y = _light_tokens()
    small_text = [("ink", "paper"), ("ink-2", "paper"), ("muted", "paper"), ("muted", "paper-2"), ("accent", "paper")]
    small_text += [(f"{s}-ink", f"{s}-tint") for s in ("pass", "fail", "warn", "info")]
    for fg, bg in small_text:
        assert _ratio(y[fg], y[bg]) >= 4.5, (fg, bg, _ratio(y[fg], y[bg]))
    for fill in ("pass", "fail", "accent"):  # the stamp: display-size text, 3:1 is the bar
        assert _ratio(y["accent-ink"], y[fill]) >= 3.0, fill
    assert _ratio(y["focus"], y["paper"]) >= 3.0
