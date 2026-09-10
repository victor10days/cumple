"""The landing page in site/: a copy of the design system, real links, honest copy, counts that match the registry."""

from __future__ import annotations

import json
import re
from collections import Counter
from html import unescape
from html.parser import HTMLParser
from pathlib import Path

from cumple.report.style import FONTS, tokens_css
from cumple.specs import load_all

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
PAGE = (SITE / "index.html").read_text(encoding="utf-8")
SITE_URL = "https://cumple-uxa7.onrender.com/"  # Render; the GitHub Pages copy is a mirror


class Walk(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[str] = []
        self.images: list[dict] = []
        self.text: list[str] = []
        self.title = ""
        self.meta: dict[str, str] = {}
        self.jsonld: list[str] = []
        self._in: str | None = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
        if tag in ("link",) and a.get("href"):
            self.links.append(a["href"])
        if tag == "img":
            self.images.append(a)
        if tag == "meta" and a.get("content"):
            self.meta[a.get("name") or a.get("property") or ""] = a["content"]
        if tag == "script" and a.get("type") == "application/ld+json":
            self._in = "jsonld"
        elif tag == "script":
            self._in = "script"
        elif tag == "style":
            self._in = "style"
        elif tag == "title":
            self._in = "title"

    def handle_endtag(self, tag):
        if tag in ("script", "style", "title"):
            self._in = None

    def handle_data(self, data):
        if self._in == "jsonld":
            self.jsonld.append(data)
        elif self._in == "title":
            self.title += data
        elif self._in is None:
            self.text.append(data)


def walk() -> Walk:
    w = Walk()
    w.feed(PAGE)
    return w


def test_tokens_and_fonts_are_verbatim_copies():
    assert (SITE / "tokens.css").read_text(encoding="utf-8") == tokens_css()
    for _, _, name in FONTS:
        assert (SITE / "fonts" / name).read_bytes() == (
            ROOT / "src" / "cumple" / "report" / "fonts" / name
        ).read_bytes()
    assert (SITE / "fonts" / "OFL-Barlow.txt").is_file() and (SITE / "fonts" / "OFL-IBM-Plex.txt").is_file()


def test_every_local_link_and_image_resolves():
    w = walk()
    local = [h for h in w.links if not h.startswith(("http://", "https://", "mailto:", "#"))]
    assert local and all((SITE / h.split("#")[0]).is_file() for h in local), local
    assert w.images and all((SITE / i["src"]).is_file() and i.get("alt") for i in w.images)
    for url in re.findall(r"url\(([^)]+)\)", PAGE):
        assert (SITE / url.strip("\"'")).is_file(), url


def test_copy_has_no_dashes_and_no_unsupported_claims():
    w = walk()
    text = " ".join(w.text)
    assert "–" not in text and "—" not in text
    low = text.lower()
    for phrase in (
        "trusted by",
        "testimonial",
        "field-proven",
        "battle-tested",
        "dolby compatible",
        "our customers",
        "award",
        "not checked",
    ):
        assert phrase not in low, phrase
    assert "not yet run by hand" in text  # the Windows and Linux builds, stated as they are


def test_counts_match_the_registry():
    profiles = load_all()
    assert f'data-count="{len(profiles)}"' in PAGE and f"{len(profiles)} destinations" in PAGE
    fam = Counter(p.family for p in profiles.values())
    rows = re.findall(r'<td class="fam" data-h="Family">([^<]+)</td><td class="num" data-h="Count">(\d+)</td>', PAGE)
    counts = {name: int(n) for name, n in rows}
    assert counts["Streaming"] == fam["streaming"] and counts["Broadcast"] == fam["broadcast"]
    assert counts["Cinema"] == fam["cinema"] and counts["Music"] == fam["music"]
    assert counts["Podcast and audiobook"] == fam["podcast"] + fam["audiobook"]
    grades = Counter(p.grade.value for p in profiles.values())
    assert f"READ {grades['READ']}, COMMUNITY {grades['COMMUNITY']}, SECONDARY {grades['SECONDARY']}" in PAGE
    assert f"{sum(p.has_defaults for p in profiles.values())} profiles carry a stated tool default" in PAGE


def test_json_ld_parses():
    w = walk()
    blocks = [json.loads(b) for b in w.jsonld]
    types = {b["@type"]: b for b in blocks}
    app = types["SoftwareApplication"]
    assert app["name"] == "cumple" and app["offers"]["price"] == "0" and app["isAccessibleForFree"] is True
    assert all(os_ in app["operatingSystem"] for os_ in ("macOS", "Windows", "Linux"))
    assert "aggregateRating" not in app and "review" not in app
    faq = types["FAQPage"]
    assert len(faq["mainEntity"]) == 7 and PAGE.count("<details>") == 7


def test_faq_json_ld_repeats_the_visible_answers():
    w = walk()
    faq = next(b for b in (json.loads(b) for b in w.jsonld) if b["@type"] == "FAQPage")
    visible = re.findall(r"<details><summary>([^<]+)</summary><p>([^<]+)</p></details>", PAGE)
    assert len(visible) == 7
    structured = [(q["name"], q["acceptedAnswer"]["text"]) for q in faq["mainEntity"]]
    assert structured == [(unescape(s), unescape(a)) for s, a in visible]


def test_inline_css_is_token_pure():
    css = re.search(r"<style>(.*?)</style>", PAGE, re.S).group(1)
    rules = re.sub(r"@font-face\s*\{[^}]*\}", "", css)
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", rules)
    assert "oklch(" not in rules and "rgb(" not in rules and "hsl(" not in rules
    assert re.search(r"font-family:\s*\"", rules) is None
    assert re.search(r"html\s*\{[^}]*overflow-x: clip", rules) and re.search(r"body\s*\{[^}]*overflow-x: clip", rules)
    assert '<link rel="stylesheet" href="tokens.css">' in PAGE
    assert "font-style: italic" not in rules


def test_meta_lengths_and_urls():
    w = walk()
    assert 0 < len(w.title.strip()) <= 60 and 0 < len(w.meta["description"]) <= 155
    assert re.search(r'<link rel="canonical" href="' + re.escape(SITE_URL) + '">', PAGE)
    assert w.meta["og:image"].startswith(SITE_URL) and w.meta["og:url"] == SITE_URL


def test_download_links_match_the_release_workflow():
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    assets = re.findall(r"asset: (cumple-[a-z0-9_.-]+)", workflow)
    assert len(assets) == 4
    for asset in assets:
        assert f"https://github.com/victor10days/cumple/releases/latest/download/{asset}" in PAGE, asset
    assert (SITE / "robots.txt").is_file() and (SITE / "sitemap.xml").is_file()


def test_render_blueprint_publishes_the_site_folder():
    import yaml

    blueprint = yaml.safe_load((ROOT / "render.yaml").read_text(encoding="utf-8"))
    (service,) = blueprint["services"]
    assert service["type"] == "web" and service["runtime"] == "static" and service["name"] == "cumple"
    assert service["staticPublishPath"] == "./site" and service["branch"] == "main"
    assert any(e["key"] == "SKIP_INSTALL_DEPS" for e in service["envVars"])


def test_the_untested_build_caveat_is_in_the_download_script():
    assert "nobody has run it by hand on" in PAGE


TABS = [
    ("#features", "What it does"),
    ("#proof", "How we know"),
    ("#destinations", "Destinations"),
    ("#compare", "Compare"),
    ("#questions", "Questions"),
]


class Outline(HTMLParser):
    """Ids, in-page links, the tabs and the header/nav/main order; Walk does not track nesting."""

    def __init__(self):
        super().__init__()
        self.ids: list[str] = []
        self.fragments: list[str] = []
        self.navs: list[dict] = []
        self.tabs: list[tuple[str, str]] = []
        self.order: list[str] = []
        self._in_nav = 0
        self._tab: list[str] | None = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.append(a["id"])
        href = a.get("href") or ""
        if tag == "a" and href.startswith("#"):
            self.fragments.append(href)
        if tag in ("header", "nav", "main"):
            self.order.append(tag)
        if tag == "nav":
            self.navs.append(a)
            self._in_nav += 1
        if tag == "a" and self._in_nav:
            self._tab = [href, ""]

    def handle_endtag(self, tag):
        if tag in ("header", "nav", "main"):
            self.order.append("/" + tag)
        if tag == "nav":
            self._in_nav -= 1
        if tag == "a" and self._tab is not None:
            self.tabs.append((self._tab[0], self._tab[1].strip()))
            self._tab = None

    def handle_data(self, data):
        if self._tab is not None:
            self._tab[1] += data


def outline() -> Outline:
    o = Outline()
    o.feed(PAGE)
    return o


def test_every_in_page_link_points_at_one_existing_id():
    o = outline()
    repeated = sorted(i for i, n in Counter(o.ids).items() if n > 1)
    assert not repeated, repeated
    assert "#main" in o.fragments and "#download" in o.fragments
    missing = sorted({h for h in o.fragments if h[1:] not in o.ids})
    assert not missing, missing
    labelled = re.findall(r'aria-labelledby="([^"]+)"', PAGE)
    assert labelled and all(i in o.ids for i in labelled), labelled


def test_the_section_tabs_are_the_five_agreed_ones_in_order():
    o = outline()
    assert len(o.navs) == 1 and o.navs[0].get("aria-label") == "Sections"
    assert o.tabs == TABS
    positions = [PAGE.index(f' id="{h[1:]}"') for h, _ in TABS]
    assert positions == sorted(positions)  # the tabs run in the page's own order


def test_the_nav_sits_in_the_header_before_main():
    o = outline()
    assert o.order == ["header", "nav", "/nav", "/header", "main", "/main"]


def test_the_bar_is_sticky_and_anchor_jumps_clear_it():
    css = re.search(r"<style>(.*?)</style>", PAGE, re.S).group(1)
    assert re.search(r"\.nav\s*\{[^}]*position: sticky;[^}]*top: 0;", css)
    assert re.search(r"html\s*\{[^}]*scroll-padding-top: calc\(var\(--bar-h\)", css)
    assert re.search(r"\.tabs a\[aria-current\]\s*\{[^}]*var\(--color-accent\)", css)
    assert PAGE.count('setAttribute("aria-current", "true")') == 1 and "IntersectionObserver" in PAGE


def test_the_live_page_is_deployed_by_the_workflow_and_only_when_green():
    """Render cannot deploy itself here, so the push is announced from CI, after the suite passes."""
    import yaml

    workflow = yaml.safe_load((ROOT / ".github" / "workflows" / "tests.yml").read_text(encoding="utf-8"))
    deploy = workflow["jobs"]["deploy"]
    assert set(deploy["needs"]) == {"test", "conformance"}, "a red commit must never reach the live page"
    assert deploy["if"] == "github.event_name == 'push' && github.ref == 'refs/heads/main'"
    (step,) = deploy["steps"]
    assert step["env"]["HOOK"] == "${{ secrets.RENDER_DEPLOY_HOOK }}"
    assert "exit 1" in step["run"], "a missing hook must fail, not pass quietly"
    assert not re.search(r"echo[^\n]*\$HOOK", step["run"]), "the hook URL is a credential; never print it"
