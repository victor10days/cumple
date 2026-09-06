"""Rebuild the font subsets the documents embed (src/cumple/report/fonts/).

Run:  uv run python scripts/build_fonts.py

Fetches the five faces from the google/fonts repository (SIL Open Font License), instances the
variable IBM Plex Sans at weights 400 and 600, and subsets every face to Latin plus the symbols a
QC sheet uses (± ≤ ≥ − × · – — … ′ ″) as woff2. About 80 KB in total; the sheets inline them as
base64 so they open offline and print to PDF the same on any machine. Needs the dev group
(fonttools with brotli).
"""

from __future__ import annotations

import sys
import tempfile
import urllib.request
from pathlib import Path

RAW = "https://raw.githubusercontent.com/google/fonts/main/ofl"
OUT = Path(__file__).resolve().parents[1] / "src" / "cumple" / "report" / "fonts"
UNICODES = (
    "U+0020-007E,U+00A0-00FF,U+0100-017F,U+2010-2027,U+2030-203A,U+2044,U+2122,U+2190-2195,U+2212,U+2215,U+2260-2265"
)
STATIC = {
    "BarlowCondensed-SemiBold": "barlowcondensed/BarlowCondensed-SemiBold.ttf",
    "BarlowCondensed-Bold": "barlowcondensed/BarlowCondensed-Bold.ttf",
    "IBMPlexMono-Regular": "ibmplexmono/IBMPlexMono-Regular.ttf",
}
PLEX_SANS_VF = "ibmplexsans/IBMPlexSans%5Bwdth%2Cwght%5D.ttf"
LICENCES = {"OFL-Barlow.txt": "barlowcondensed/OFL.txt", "OFL-IBM-Plex.txt": "ibmplexsans/OFL.txt"}


def fetch(rel: str, to: Path) -> Path:
    with urllib.request.urlopen(f"{RAW}/{rel}", timeout=120) as r:  # noqa: S310 (fixed https host)
        to.write_bytes(r.read())
    return to


def main() -> int:
    from fontTools import subset
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer

    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        sources: dict[str, Path] = {name: fetch(rel, tmp / f"{name}.ttf") for name, rel in STATIC.items()}
        vf = fetch(PLEX_SANS_VF, tmp / "IBMPlexSans-VF.ttf")
        for wght, name in ((400, "IBMPlexSans-Regular"), (600, "IBMPlexSans-SemiBold")):
            inst = instancer.instantiateVariableFont(TTFont(vf), {"wght": wght, "wdth": 100})
            inst.save(tmp / f"{name}.ttf")
            sources[name] = tmp / f"{name}.ttf"
        for name, src in sources.items():
            out = OUT / f"{name}.woff2"
            subset.main(
                [
                    str(src),
                    f"--unicodes={UNICODES}",
                    "--flavor=woff2",
                    "--layout-features=kern,liga,tnum,pnum,lnum,onum,ss01",
                    "--no-hinting",
                    "--desubroutinize",
                    f"--output-file={out}",
                ]
            )
            print(f"{out.name}: {out.stat().st_size} B")
        for name, rel in LICENCES.items():
            fetch(rel, OUT / name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
