"""Build the damaged-audio set that scripts/benchmark_repair.py scores repair tools on.

Run: uv run python scripts/make_repair_set.py
Needs the references scripts/fetch_real_dialogue.sh leaves under ~/.cache/cumple/real-dialogue/ (the
EBU SQAM tracks and the LibriVox chapter); the 3-second fixture tests/fixtures/speech-librivox-3s.wav is
always a reference too, so its pinned rows exist. Writes to ~/.cache/cumple/repair/ (CUMPLE_REPAIR_SET
overrides), outside the repository: the damaged audio is never committed.

Where the choices come from, read 2026-10-08:
- The seven input-SDR levels (1, 3, 5, 7, 10, 15, 20 dB) are the declipping survey's: Zaviska, Rajmic,
  Ozerov, Rencker, "A survey and an extensive evaluation of popular audio declipping methods", IEEE JSTSP
  2021 (open access), and its companion page rajmic.github.io/declipping2020. The survey repository's
  README (rajmic/declipping2020_codes, GPL, read only, never cloned) names neither the levels nor the
  excerpts.
- The ten SQAM tracks are the file names in that repository's Sounds folder: a08 violin, a16 clarinet,
  a18 bassoon, a25 harp, a35 glockenspiel, a41 celesta, a42 accordion, a58 guitar, a60 piano, a66 wind
  ensemble. SQAM is fetched under the EBU's terms (research use only; see fetch_real_dialogue.sh) and
  nothing from it is committed.
- Three 30-second LibriVox excerpts at 60 s, 600 s and 1,200 s stand in for speech. The whole chapter is
  133,603 A-SPADE frames, about 2.04 GiB per complex128 frame array, per level and tool.

Layout of the set:
  references/<name>.wav       the clean reference, mono, 32-bit float
  damaged/<name>.clip<sdr>.wav, <name>.impulse<seed>.wav, <name>.burst<seed>.wav
  rx8-input/...               the same files for iZotope RX 8 (clips scaled so the plateau sits at 0.95)
  manifest.json               hashes, thresholds, click lists and scales
Every damaged file is 32-bit float: at gain 32 about 40 % of the fixture's clicks peak above full scale
(03e: 801 of 2,000), and PCM would clip them.
"""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

from cumple.io.reader import read
from cumple.repair import damage

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "speech-librivox-3s.wav"
REAL = Path(os.environ.get("CUMPLE_CACHE", Path.home() / ".cache" / "cumple")) / "real-dialogue"
SQAM = {
    "a08-violin": "08",
    "a16-clarinet": "16",
    "a18-bassoon": "18",
    "a25-harp": "25",
    "a35-glockenspiel": "35",
    "a41-celesta": "41",
    "a42-accordion": "42",
    "a58-guitar": "58",
    "a60-piano": "60",
    "a66-wind-ensemble": "66",
}
LIBRIVOX = REAL / "librivox" / "william_again_ch01.mp3"
EXCERPT_OFFSETS_S = (60, 600, 1200)
EXCERPT_S = 30
# ffmpeg's adeclip does not finish a 71 s SQAM track at 3 dB or below inside any sensible budget (measured
# 2026-10-08: over 91 s each), so each SQAM track is cut to 20 s starting at 2 s, or kept whole when shorter.
SQAM_START_S = 2
SQAM_LENGTH_S = 20
LEVELS = (1, 3, 5, 7, 10, 15, 20)  # input SDR in dB, from the survey
IMPULSE_SEED = 11
BURST_SEED = 12
CLICKS_PER_MINUTE = 120
RX_PLATEAU = 0.95  # the level RX 8's De-clip is shown the clip plateau at


def set_dir() -> Path:
    return Path(os.environ.get("CUMPLE_REPAIR_SET") or Path.home() / ".cache" / "cumple" / "repair")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mono(data: np.ndarray) -> np.ndarray:
    """(frames, channels) to float64 mono by averaging the channels, rounded to float32 so the stored reference is exact."""
    return data.mean(axis=1).astype(np.float32).astype(np.float64)


def references() -> tuple[list[tuple[str, np.ndarray, int, str]], list[str]]:
    """(name, samples, samplerate, source) for each reference present, and the names of the ones absent."""
    found: list[tuple[str, np.ndarray, int, str]] = []
    absent: list[str] = []
    data, fs = read(FIXTURE)
    found.append(("fixture", mono(data), fs, "tests/fixtures/speech-librivox-3s.wav"))
    for name, number in SQAM.items():
        path = REAL / "sqam" / "flac" / f"{number}.flac"
        if path.is_file():
            data, fs = read(path)
            if len(data) > (SQAM_START_S + SQAM_LENGTH_S) * fs:
                data = data[SQAM_START_S * fs : (SQAM_START_S + SQAM_LENGTH_S) * fs]
                source = f"EBU SQAM track {number}, {SQAM_LENGTH_S} s from {SQAM_START_S} s"
            else:
                source = f"EBU SQAM track {number}, whole"
            found.append((name, mono(data), fs, source))
        else:
            absent.append(name)
    if LIBRIVOX.is_file():
        data, fs = read(LIBRIVOX)
        for offset in EXCERPT_OFFSETS_S:
            part = data[offset * fs : (offset + EXCERPT_S) * fs]
            found.append(
                (f"librivox-{offset}s", mono(part), fs, f"LibriVox William Again ch. 1, {EXCERPT_S} s from {offset} s")
            )
    else:
        absent += [f"librivox-{o}s" for o in EXCERPT_OFFSETS_S]
    return found, absent


def write(path: Path, x: np.ndarray, fs: int) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(path, x, fs, subtype="FLOAT")
    return sha256(path)


def add(
    manifest: damage.Manifest,
    out: Path,
    name: str,
    fs: int,
    kind: str,
    label: str,
    y: np.ndarray,
    scale: float,
    **fields,
) -> None:
    """Write one damaged file and its RX 8 input twin, and record both in the manifest."""
    stem = f"{name}.{label}"
    file = f"damaged/{stem}.wav"
    rx = f"rx8-input/{stem}.wav"
    manifest.damaged.append(
        damage.Damaged(name=stem, reference=name, kind=kind, file=file, sha256=write(out / file, y, fs), **fields)
    )
    manifest.rx_input.append(damage.RxInput(name=stem, file=rx, sha256=write(out / rx, y * scale, fs), scale=scale))


def main() -> None:
    refs, absent = references()
    if len(refs) == 1:  # only the fixture: the fetched references are the point of the set
        sys.exit("no fetched reference found under " + str(REAL) + "; run scripts/fetch_real_dialogue.sh first")
    out = set_dir()
    manifest = damage.Manifest(references=[], damaged=[], rx_input=[])
    for name, x, fs, source in refs:
        manifest.references.append(
            damage.Reference(
                name=name,
                file=f"references/{name}.wav",
                sha256=write(out / "references" / f"{name}.wav", x, fs),
                samplerate=fs,
                source=source,
            )
        )

        for level in LEVELS:
            y, thr, _ = damage.clip_to_sdr(x, float(level))
            add(
                manifest, out, name, fs, "clip", f"clip{level}", y, RX_PLATEAU / thr, sdr_db=float(level), threshold=thr
            )
        for kind, seed, preset in (("impulse", IMPULSE_SEED, damage.IMPULSE), ("burst", BURST_SEED, damage.BURST)):
            y, clicks, _ = damage.add_clicks(x, fs, seed, CLICKS_PER_MINUTE, **preset)
            records = [damage.ClickRecord(position=c.position, width=c.width, gain=c.gain) for c in clicks]
            add(
                manifest,
                out,
                name,
                fs,
                kind,
                f"{kind}{seed}",
                y,
                1.0,
                seed=seed,
                per_minute=float(CLICKS_PER_MINUTE),
                clicks=records,
            )
        print(f"{name}: {len(x) / fs:.1f} s at {fs} Hz", file=sys.stderr)
    (out / "manifest.json").write_text(manifest.model_dump_json(indent=1) + "\n", encoding="utf-8")
    print(f"wrote {len(manifest.damaged)} damaged files from {len(refs)} references to {out}", file=sys.stderr)
    if absent:
        print("absent references: " + ", ".join(absent), file=sys.stderr)


if __name__ == "__main__":
    main()
