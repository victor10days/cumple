"""Render the app icon from the design tokens with the local Chrome, then the icns and ico the packagers need.

Usage: uv run python scripts/make_icons.py
Writes src/cumple/app/ui/icon.png (512), icon.icns (macOS, via iconutil) and icon.ico (Windows, PNG
entries at 16, 32, 48 and 256 px, no Pillow needed). The 1024 px master is rendered to a temp dir.
"""

from __future__ import annotations

import struct
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cumple.report.qc_sheet import find_chrome  # noqa: E402
from cumple.report.style import font_faces_css, tokens_css  # noqa: E402

UI = ROOT / "src" / "cumple" / "app" / "ui"

HTML = """<!doctype html><html><head><meta charset="utf-8"><style>
{tokens}
{fonts}
html, body {{ margin: 0; background: transparent; width: 1024px; height: 1024px; overflow: hidden; }}
.tile {{ position: absolute; inset: 60px; border-radius: 232px; background: var(--color-accent);
  display: flex; flex-direction: column; justify-content: center; align-items: center; }}
.word {{ font-family: var(--font-display); font-weight: 700; font-size: 272px; line-height: 1;
  letter-spacing: -0.02em; color: var(--color-accent-ink); margin-top: -24px; }}
.rule {{ width: 540px; height: 14px; background: var(--color-accent-ink); margin: 40px 0 30px; }}
.qc {{ font-family: var(--font-display); font-weight: 600; font-size: 118px; line-height: 1;
  letter-spacing: 0.14em; color: var(--color-accent-ink); }}
</style></head><body><div class="tile"><div class="word">cumple</div><div class="rule"></div><div class="qc">QC</div></div></body></html>
"""


def sips(src: Path, px: int, out: Path) -> None:
    subprocess.run(["sips", "-z", str(px), str(px), str(src), "--out", str(out)], check=True, capture_output=True)


def write_ico(entries: list[tuple[int, bytes]], out: Path) -> None:
    ico = bytearray(struct.pack("<HHH", 0, 1, len(entries)))
    offset = 6 + 16 * len(entries)
    for px, data in entries:
        dim = 0 if px >= 256 else px
        ico += struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32, len(data), offset)
        offset += len(data)
    for _, data in entries:
        ico += data
    out.write_bytes(bytes(ico))


def main() -> int:
    chrome = find_chrome()
    if chrome is None:
        print("no Chrome, Chromium or Edge found; the icon needs one to render", file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory(prefix="cumple-icon-") as d:
        work = Path(d)
        src = work / "icon.html"
        src.write_text(HTML.format(tokens=tokens_css(), fonts=font_faces_css()), encoding="utf-8")
        master = work / "icon-1024.png"
        subprocess.run(
            [
                chrome,
                "--headless",
                "--disable-gpu",
                "--hide-scrollbars",
                "--no-first-run",
                "--default-background-color=00000000",
                "--window-size=1024,1024",
                f"--screenshot={master}",
                src.as_uri(),
            ],
            check=True,
            capture_output=True,
            timeout=90,
        )
        sips(master, 512, UI / "icon.png")
        iconset = work / "cumple.iconset"
        iconset.mkdir()
        for size in (16, 32, 128, 256, 512):
            for scale in (1, 2):
                sips(master, size * scale, iconset / f"icon_{size}x{size}{'@2x' if scale == 2 else ''}.png")
        if sys.platform == "darwin":
            subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(UI / "icon.icns")], check=True)
        entries = []
        for px in (16, 32, 48, 256):
            out = work / f"ico-{px}.png"
            sips(master, px, out)
            entries.append((px, out.read_bytes()))
        write_ico(entries, UI / "icon.ico")
    for name in ("icon.png", "icon.icns", "icon.ico"):
        p = UI / name
        print(f"{name}: {p.stat().st_size} bytes" if p.exists() else f"{name}: not written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
