#!/usr/bin/env python
"""Check the dialogue gate on real programmes and write docs/DIALOGUE.md.

cumple approximates Dolby Dialogue Intelligence with a heuristic speech detector
(src/cumple/meters/dialogue.py). This script measures how far that approximation sits
from two references on real material:

1. Films that publish a music-and-effects (M&E) version of their mix. Sintel and Tears of
   Steel (Blender Foundation, CC BY 3.0) ship the finished stereo mix and the same mix
   without dialogue. Where the mix carries more speech-band energy than its dialogue-free
   twin, dialogue is present; that mask is ground truth no detector can argue with, and it
   does not need a phase-accurate null (the two files were limited separately, so a plain
   subtraction does not cancel). The reference dialogue-gated loudness is the BS.1770-1
   loudness of the mix over the blocks that mask marks, computed by the same
   LoudnessMeter.dialogue_gated the product uses, so the only thing that differs between
   the reference and the product is the mask.
2. Silero VAD (Silero Team, MIT licence), the standard open voice-activity model, as an
   independent design. It needs `onnxruntime` (run with `uv run --with onnxruntime ...`) and
   the 2.3 MB model that scripts/fetch_real_dialogue.sh places in ~/.cache/cumple/. It is
   optional; the report says when it was absent. Its mask is dilated over one second the way
   the product's detector dilates its own, so the two are compared on the same terms.

It also runs clean speech, music-only and dialogue-driven programmes through the detector
to show the speech share each regime produces, because Netflix and Disney+ switch rules at
15 % dialogue and a music programme that reads as speech would be judged by the wrong rule.

The recordings come from scripts/fetch_real_dialogue.sh into ~/.cache/cumple/real-dialogue/
and are not redistributed. Compressed sources (MP3, MP4) are decoded once with ffmpeg.
"""

from __future__ import annotations

import argparse
import datetime as dt
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, fftconvolve, resample_poly, sosfilt

from cumple import __version__
from cumple.diff.align import estimate_offset
from cumple.io.reader import iter_blocks
from cumple.meters.bs1770 import SUB_HOP_S, LoudnessMeter, default_roles
from cumple.meters.dialogue import BAND_HI, BAND_LO, CONTEXT_MIN_DENSITY, CONTEXT_S, FRAME_S, SILENCE_DBFS
from cumple.meters.measure import measure

try:
    import onnxruntime as ort
except ImportError:  # the second opinion is optional
    ort = None

CACHE = Path.home() / ".cache" / "cumple" / "real-dialogue"
DOC = Path(__file__).resolve().parents[1] / "docs" / "DIALOGUE.md"
ABOVE_ME_DB = 3.0  # dialogue is present when the mix sits this far above its M&E in the speech band
ABOVE_ME_DBS = (2.0, 3.0, 6.0)  # the reference is also shown at these, to show its sensitivity
BASELINE_PERCENTILE = 10  # the mix-minus-M&E level offset in frames without dialogue
VAD_FS = 16000
SILERO_MODEL = Path.home() / ".cache" / "cumple" / "silero_vad.onnx"  # fetched by fetch_real_dialogue.sh
SILERO_CHUNK, SILERO_CONTEXT, SILERO_THRESHOLD = 512, 64, 0.5  # the model's own frame and default threshold
AGREE_LU = 1.0  # a dialogue-gated reading within this of the reference counts as agreeing
NETFLIX = (-27.0, 2.0)

# EBU Tech 3253 (SQAM) track numbers used here: the six speech tracks, a few solo instruments
# that carry syllable-rate rhythm or a voice-like band, and two sung pieces. Singing is neither
# dialogue nor music for a speech gate, so it gets its own regime and no mark.
SQAM_TRACKS: dict[int, tuple[str, str]] = {
    49: ("SQAM 49, female speech, English", "speech"),
    50: ("SQAM 50, male speech, English", "speech"),
    51: ("SQAM 51, female speech, French", "speech"),
    52: ("SQAM 52, male speech, French", "speech"),
    53: ("SQAM 53, female speech, German", "speech"),
    54: ("SQAM 54, male speech, German", "speech"),
    27: ("SQAM 27, castanets", "no dialogue"),
    55: ("SQAM 55, trumpet (Haydn)", "no dialogue"),
    58: ("SQAM 58, guitar (Sarasate)", "no dialogue"),
    59: ("SQAM 59, violin (Ravel)", "no dialogue"),
    60: ("SQAM 60, piano (Schubert)", "no dialogue"),
    61: ("SQAM 61, soprano (Mozart)", "singing"),
    64: ("SQAM 64, choir (Orff)", "singing"),
}


@dataclass
class Item:
    name: str
    src: Path  # what fetch_real_dialogue.sh wrote: a PCM file, a compressed file, or a directory
    regime: str  # "speech", "no dialogue", "singing", "mixed", "package"
    source: str
    me: Path | None = None  # music-and-effects version of the same mix, when one exists

    def available(self) -> bool:
        if not self.src.exists() or self.src.with_suffix(self.src.suffix + ".part").exists():
            return False
        return self.me is None or (self.me.exists() and not self.me.with_suffix(self.me.suffix + ".part").exists())

    def path(self) -> Path:
        """The file to measure: compressed sources are decoded to PCM once."""
        if self.src.is_dir() or self.src.suffix.lower() in {".wav", ".aif", ".aiff", ".flac"}:
            return self.src
        out = ffmpeg_decode(self.src, CACHE / "decoded" / (self.src.stem + ".wav"), "-c:a", "pcm_s24le")
        return out or self.src


# ----------------------------------------------------------------------------- helpers


def ffmpeg_decode(src: Path, out: Path, *extra: str) -> Path | None:
    """Decode src to PCM once; None when ffmpeg or the source is missing."""
    if out.exists():
        return out
    if not src.exists() or shutil.which("ffmpeg") is None:
        return None
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-loglevel", "error", "-y", "-i", str(src), "-vn", *extra, str(out)]
    subprocess.run(cmd, check=True)
    return out


def mono16k(src: Path) -> Path | None:
    return ffmpeg_decode(
        src, CACHE / "vad16k" / (src.stem + ".wav"), "-ac", "1", "-ar", str(VAD_FS), "-c:a", "pcm_s16le"
    )


def frame_levels(m: np.ndarray, fs: int) -> np.ndarray:
    """Level per 20 ms frame of a mono signal, in dBFS, on the detector's grid."""
    n = int(round(fs * FRAME_S))
    k = len(m) // n
    e = np.mean(m[: k * n].reshape(k, n).astype(np.float64) ** 2, axis=1)
    with np.errstate(divide="ignore"):
        return np.where(e > 0, 10 * np.log10(np.maximum(e, 1e-30)), -np.inf)


def speech_band(m: np.ndarray, fs: int) -> np.ndarray:
    sos = butter(4, [BAND_LO, BAND_HI], btype="bandpass", fs=fs, output="sos")
    return sosfilt(sos, m.astype(np.float64))


def dilate(voiced: np.ndarray) -> np.ndarray:
    """The detector's own rule: a pause inside dialogue is still dialogue."""
    w = max(int(CONTEXT_S / FRAME_S), 1)
    c = np.concatenate([[0.0], np.cumsum(voiced.astype(float))])
    idx = np.arange(len(voiced))
    lo = np.maximum(idx - w // 2, 0)
    hi = np.minimum(idx + w // 2, len(voiced))
    density = (c[hi] - c[lo]) / np.maximum(hi - lo, 1)
    return voiced | (density >= CONTEXT_MIN_DENSITY)


def at_hops(mask20: np.ndarray, n_hops: int) -> np.ndarray:
    """A 20 ms mask resampled onto the meter's 10 ms sub-hop grid."""
    if len(mask20) == 0:
        return np.zeros(n_hops, dtype=bool)
    idx = np.minimum((np.arange(n_hops) * SUB_HOP_S / FRAME_S).astype(int), len(mask20) - 1)
    return mask20[idx]


def meter_over_array(x: np.ndarray, fs: int, roles: list[str], block: int = 480_000) -> LoudnessMeter:
    lm = LoudnessMeter(fs, x.shape[1], roles=roles)
    for i in range(0, len(x), block):
        lm.feed(x[i : i + block].astype(np.float64))
    return lm


def meter_over_file(path: Path) -> LoudnessMeter:
    info = sf.info(str(path))
    lm = LoudnessMeter(info.samplerate, info.channels, roles=default_roles(info.channels))
    for b in iter_blocks(path):
        lm.feed(b)
    return lm


def whole_file_offset(a: np.ndarray, b: np.ndarray, fs: int, max_s: float = 60.0) -> tuple[float, float]:
    """(lag of b behind a in samples, normalised correlation) over the whole programme, decimated."""
    q = max(fs // 4000, 1)
    ad = resample_poly(a.astype(np.float64), 1, q)
    bd = resample_poly(b.astype(np.float64), 1, q)
    n = min(len(ad), len(bd))
    ad, bd = ad[:n] - ad[:n].mean(), bd[:n] - bd[:n].mean()
    c = fftconvolve(bd, ad[::-1], mode="full")
    lags = np.arange(-(n - 1), n)
    keep = np.abs(lags) <= max_s * fs / q
    c, lags = c[keep], lags[keep]
    i = int(np.argmax(np.abs(c)))
    rho = c[i] / np.sqrt((ad * ad).sum() * (bd * bd).sum())
    return float(lags[i] * q), float(rho)


def shift_whole(x: np.ndarray, k: int) -> np.ndarray:
    """x advanced by k samples (k > 0 drops the head; k < 0 pads it)."""
    if k > 0:
        return np.concatenate([x[k:], np.zeros((k, x.shape[1]), x.dtype)])
    if k < 0:
        return np.concatenate([np.zeros((-k, x.shape[1]), x.dtype), x[:k]])
    return x


def silero_available() -> bool:
    return ort is not None and SILERO_MODEL.exists()


def vad_mask(path16k: Path | None) -> np.ndarray | None:
    """Silero VAD decisions on the detector's 20 ms grid, dilated like the detector's own mask."""
    if not silero_available() or path16k is None or not path16k.exists():
        return None
    x, fs = sf.read(str(path16k), dtype="float32", always_2d=False)
    if fs != VAD_FS:
        return None
    sess = ort.InferenceSession(str(SILERO_MODEL), providers=["CPUExecutionProvider"])
    n = len(x) // SILERO_CHUNK
    state = np.zeros((2, 1, 128), dtype=np.float32)
    context = np.zeros((1, SILERO_CONTEXT), dtype=np.float32)
    sr = np.array(VAD_FS, dtype=np.int64)
    probs = np.empty(n, dtype=np.float32)
    for i in range(n):
        inp = np.concatenate([context, x[i * SILERO_CHUNK : (i + 1) * SILERO_CHUNK][None, :]], axis=1)
        out, state = sess.run(None, {"input": inp, "state": state, "sr": sr})
        probs[i] = out[0, 0]
        context = inp[:, -SILERO_CONTEXT:]
    n20 = int(len(x) / VAD_FS / FRAME_S)
    idx = np.minimum((np.arange(n20) * FRAME_S / (SILERO_CHUNK / VAD_FS)).astype(int), max(n - 1, 0))
    return dilate(probs[idx] > SILERO_THRESHOLD) if n else np.zeros(n20, dtype=bool)


def share(mask: np.ndarray | None, programme: np.ndarray) -> float | None:
    if mask is None:
        return None
    n = min(len(mask), len(programme))
    m, p = mask[:n], programme[:n] | mask[:n]
    return float(m[p].mean()) if p.any() else 0.0


def fmt(v: float | None, nd: int = 2, suffix: str = "") -> str:
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return "n/a"
    return f"{v:.{nd}f}{suffix}"


def pct(v: float | None) -> str:
    return "n/a" if v is None else f"{100 * v:.0f} %"


def mmss(seconds: float) -> str:
    s = int(round(seconds))
    return f"{s // 60}:{s % 60:02d}"


def verdict(v: float | None) -> str:
    if v is None or not np.isfinite(v):
        return "n/a"
    lo, hi = NETFLIX[0] - NETFLIX[1], NETFLIX[0] + NETFLIX[1]
    return "PASS" if lo <= v <= hi else "FAIL"


# ----------------------------------------------------------------------------- analyses


@dataclass
class PairResult:
    item: Item
    fs: int
    duration_s: float
    lag_samples: float
    correlation: float
    me_offset_db: float
    integrated: float
    ref_share: float
    heur_share: float | None
    vad_share: float | None
    precision: float
    recall: float
    agreement: float
    ref_gated: float
    ref_blocks: int
    ref_gated_by_db: dict[float, float]
    ref_share_by_db: dict[float, float]
    heur_gated: float
    heur_blocks: int
    vad_gated: float | None


def analyse_pair(item: Item) -> PairResult:
    assert item.me is not None
    mix, fs = sf.read(str(item.path()), dtype="float32", always_2d=True)
    me, fs2 = sf.read(str(item.me), dtype="float32", always_2d=True)
    if fs != fs2 or mix.shape[1] != me.shape[1]:
        raise SystemExit(f"{item.name}: mix and M&E differ in rate or channel count")
    n = min(len(mix), len(me))
    mix, me = mix[:n], me[:n]
    roles = default_roles(mix.shape[1])

    lag, rho = estimate_offset(mix, me, fs, max_offset_s=2.0, analysis_s=120.0)
    if abs(rho) < 0.5:  # the head may differ (leader, titles): look at the whole programme
        lag, rho = whole_file_offset(mix.mean(axis=1), me.mean(axis=1), fs)
    me = shift_whole(me, int(round(lag)))

    mono_mix = mix.mean(axis=1)
    mono_me = me.mean(axis=1)
    lv_mix = frame_levels(mono_mix, fs)
    band_mix = frame_levels(speech_band(mono_mix, fs), fs)
    band_me = frame_levels(speech_band(mono_me, fs), fs)
    programme = lv_mix > SILENCE_DBFS
    d = band_mix - band_me
    usable = programme & np.isfinite(d)
    offset = float(np.percentile(d[usable], BASELINE_PERCENTILE)) if usable.any() else 0.0
    refs = {db: dilate(usable & (d > offset + db)) for db in ABOVE_ME_DBS}
    ref = refs[ABOVE_ME_DB]

    m = measure(item.path())
    heur = m.speech.mask if m.speech is not None else np.zeros(0, bool)
    vad = vad_mask(mono16k(item.path()))

    mix_meter = meter_over_array(mix, fs, roles)
    n_hops = len(mix_meter._hop_energies())
    gated = {db: mix_meter.dialogue_gated(at_hops(mask, n_hops)) for db, mask in refs.items()}
    vad_gated = mix_meter.dialogue_gated(at_hops(vad, n_hops))[0] if vad is not None else None

    L = min(len(ref), len(heur))
    r, h, p = ref[:L], heur[:L], (programme[:L] | ref[:L] | heur[:L])
    tp = float((r & h & p).sum())
    precision = tp / max(float((h & p).sum()), 1.0)
    recall = tp / max(float((r & p).sum()), 1.0)
    agreement = float(((r == h) & p).sum()) / max(float(p.sum()), 1.0)

    return PairResult(
        item=item,
        fs=fs,
        duration_s=n / fs,
        lag_samples=lag,
        correlation=abs(rho),
        me_offset_db=offset,
        integrated=m.loudness.integrated,
        ref_share=share(ref, programme),
        heur_share=m.speech_fraction,
        vad_share=share(vad, programme),
        precision=precision,
        recall=recall,
        agreement=agreement,
        ref_gated=gated[ABOVE_ME_DB][0],
        ref_blocks=gated[ABOVE_ME_DB][1],
        ref_gated_by_db={db: g[0] for db, g in gated.items()},
        ref_share_by_db={db: share(mask, programme) for db, mask in refs.items()},
        heur_gated=m.loudness.dialogue_gated,
        heur_blocks=m.loudness.dialogue_blocks,
        vad_gated=vad_gated,
    )


@dataclass
class FileResult:
    item: Item
    duration_s: float
    channels: int
    integrated: float
    heur_gated: float
    heur_blocks: int
    heur_share: float | None
    vad_share: float | None
    vad_gated: float | None


def analyse_file(item: Item) -> FileResult:
    path = item.path()
    m = measure(path)
    vad_share_v = None
    vad_gated = None
    if path.is_file():
        vad = vad_mask(mono16k(path))
        if vad is not None and m.speech is not None:
            programme = m.speech.level_db > SILENCE_DBFS
            lm = meter_over_file(path)
            vad_gated = lm.dialogue_gated(at_hops(vad, len(lm._hop_energies())))[0]
            vad_share_v = share(vad, programme)
    return FileResult(
        item=item,
        duration_s=m.duration_s,
        channels=m.channels,
        integrated=m.loudness.integrated,
        heur_gated=m.loudness.dialogue_gated,
        heur_blocks=m.loudness.dialogue_blocks,
        heur_share=m.speech_fraction,
        vad_share=vad_share_v,
        vad_gated=vad_gated,
    )


def regime_mark(regime: str, share_v: float | None) -> str:
    if share_v is None:
        return "n/a"
    if regime == "speech":
        return "✓" if share_v >= 0.8 else "✗"
    if regime == "no dialogue":
        return "✓" if share_v < 0.15 else "✗"
    return ""


# ----------------------------------------------------------------------------- catalogue


def sqam_items() -> list[Item]:
    z = CACHE / "sqam" / "TECH3253_SQAM_FLAC.zip"
    folder = CACHE / "sqam" / "flac"
    if z.exists() and not folder.exists() and zipfile.is_zipfile(z):  # a partial download is not a zip yet
        with zipfile.ZipFile(z) as zf:
            zf.extractall(folder)
    items: list[Item] = []
    if not folder.exists():
        return items
    for f in sorted(folder.rglob("*.flac")):
        digits = "".join(ch for ch in f.stem[:3] if ch.isdigit())
        if not digits:
            continue
        num = int(digits)
        if num in SQAM_TRACKS:
            name, regime = SQAM_TRACKS[num]
            items.append(Item(name, f, regime, "EBU SQAM (Tech 3253), R&D use"))
    return items


def catalogue() -> tuple[list[Item], list[Item]]:
    c = CACHE
    bf = "Blender Foundation, CC BY 3.0"
    pairs = [
        Item(
            "Sintel (2010), stereo master",
            c / "sintel/sintel-master-st.flac",
            "mixed",
            bf,
            me=c / "sintel/sintel-m+e-st.flac",
        ),
        Item(
            "Tears of Steel (2012), stereo mix",
            c / "tos/TOS_DVDSTEREOMIX.aif",
            "mixed",
            bf,
            me=c / "tos/TOS_MUSIC+FX_NO_DIALOGUE.aif",
        ),
    ]
    singles = [
        Item(
            "LibriVox, William Again, chapter 1",
            c / "librivox/william_again_ch01.mp3",
            "speech",
            "public domain, LibriVox",
        ),
        Item(
            "NASA, Houston We Have a Podcast, National Lab 15",
            c / "nasa/hwhap_national_lab_15.mp3",
            "speech",
            "NASA, public domain",
        ),
        *sqam_items(),
        Item("Sintel, music and effects (no dialogue)", c / "sintel/sintel-m+e-st.flac", "no dialogue", bf),
        Item(
            "Tears of Steel, music and effects (no dialogue)", c / "tos/TOS_MUSIC+FX_NO_DIALOGUE.aif", "no dialogue", bf
        ),
        Item("Sintel, stereo master", c / "sintel/sintel-master-st.flac", "mixed", bf),
        Item("Sintel, 5.1 master", c / "sintel/sintel-master-51.flac", "mixed", bf),
        Item("Sintel, trailer", c / "sintel/sintel_trailer-audio.flac", "mixed", bf),
        Item("Tears of Steel, stereo mix", c / "tos/TOS_DVDSTEREOMIX.aif", "mixed", bf),
        Item("Tears of Steel, 5.1 discrete package (6 mono AIFF)", c / "tos/surround", "package", bf),
        Item("Sprite Fright (2021)", c / "sprite-fright/sprite_fright_804p.mp4", "mixed", "Blender Studio, CC BY 4.0"),
        Item(
            "His Girl Friday (1940)",
            c / "pd-films/his_girl_friday_1940.mp3",
            "mixed",
            "public domain, Internet Archive",
        ),
        Item(
            "Night of the Living Dead (1968)",
            c / "pd-films/night_of_the_living_dead_1968.mp3",
            "mixed",
            "public domain, Internet Archive",
        ),
    ]
    return pairs, singles


# ----------------------------------------------------------------------------- report


def write_report(pairs: list[PairResult], files: list[FileResult], missing: list[str]) -> str:
    today = dt.date.today().isoformat()
    vad_note = (
        f"Silero VAD (threshold {SILERO_THRESHOLD}) was available and is shown as a second, independent opinion."
        if silero_available()
        else "Silero VAD was not available (onnxruntime or the model missing), so its columns read n/a."
    )
    out: list[str] = []
    out.append(f"# The dialogue gate on real programmes, cumple {__version__}")
    out.append("")
    out.append(
        f"Generated {today} by `scripts/dialogue_benchmark.py`. cumple's dialogue-gated loudness "
        "uses a heuristic speech detector labelled an approximation of Dolby Dialogue Intelligence. "
        "This report measures the approximation against films that publish a music-and-effects "
        "version of their mix, and shows the speech share the detector reports on clean speech, on "
        f"music and effects without dialogue, and on dialogue-driven films. {vad_note} "
        "The recordings are fetched by `scripts/fetch_real_dialogue.sh` and are not redistributed."
    )
    out.append("")
    out.append("## Films with a music-and-effects version as ground truth")
    out.append("")
    out.append(
        "The M&E is aligned to the mix, both are band-passed to the detector's 150 Hz to 4 kHz speech "
        "band, and the level difference per 20 ms frame is taken. Frames without dialogue sit at a "
        f"baseline offset (the {BASELINE_PERCENTILE}th percentile of that difference); a frame is dialogue "
        f"when the mix sits {ABOVE_ME_DB:.0f} dB or more above that baseline, dilated over one second the "
        "way the detector dilates its own frames. The reference dialogue-gated value is BS.1770-1 "
        "(absolute gate only) over the 400 ms blocks that are at least half dialogue by that mask; the "
        "product's value is the same computation with the detector's mask instead. The two files were "
        "limited separately, so a subtraction does not null; the correlation column says how far from "
        "a null they are."
    )
    out.append("")
    out.append("| programme | duration | M&E alignment | correlation | M&E baseline offset |")
    out.append("|---|---|---|---|---|")
    for p in pairs:
        out.append(
            f"| {p.item.name} | {mmss(p.duration_s)} | {p.lag_samples:+.0f} samples | {p.correlation:.2f} | "
            f"{p.me_offset_db:+.2f} dB |"
        )
    out.append("")
    out.append(
        "| programme | speech share: reference | detector | Silero | frame precision | frame recall | frames agreeing |"
    )
    out.append("|---|---|---|---|---|---|---|")
    for p in pairs:
        out.append(
            f"| {p.item.name} | {pct(p.ref_share)} | {pct(p.heur_share)} | {pct(p.vad_share)} | "
            f"{pct(p.precision)} | {pct(p.recall)} | {pct(p.agreement)} |"
        )
    out.append("")
    out.append(
        f"| programme | integrated (BS.1770-4) | dialogue-gated: reference | detector | delta | "
        f"within {AGREE_LU:.0f} LU | Silero-gated | Netflix -27 ±2: reference / detector |"
    )
    out.append("|---|---|---|---|---|---|---|---|")
    for p in pairs:
        delta = p.heur_gated - p.ref_gated
        ok = "✓" if abs(delta) <= AGREE_LU else "✗"
        out.append(
            f"| {p.item.name} | {fmt(p.integrated, 1)} | {fmt(p.ref_gated, 1)} ({p.ref_blocks} blocks) | "
            f"{fmt(p.heur_gated, 1)} ({p.heur_blocks} blocks) | {delta:+.2f} LU | {ok} | {fmt(p.vad_gated, 1)} | "
            f"{verdict(p.ref_gated)} / {verdict(p.heur_gated)} |"
        )
    out.append("")
    out.append("Sensitivity of the reference to how far above the M&E a frame must sit (share, gated value):")
    out.append("")
    out.append("| programme | " + " | ".join(f"{db:.0f} dB" for db in ABOVE_ME_DBS) + " |")
    out.append("|---|" + "---|" * len(ABOVE_ME_DBS))
    for p in pairs:
        cells = [f"{pct(p.ref_share_by_db[db])}, {fmt(p.ref_gated_by_db[db], 2)}" for db in ABOVE_ME_DBS]
        out.append(f"| {p.item.name} | " + " | ".join(cells) + " |")
    out.append("")
    out.append("## Speech share by regime")
    out.append("")
    out.append(
        "Several profiles switch from the dialogue rule to the full-programme rule under 15 % speech. "
        "Clean speech should read high (mark: at least 80 %), music and effects without dialogue "
        "should read under 15 %, and mixed programmes and singing are shown without a mark. The dialogue-gated "
        "value is the detector's; the integrated value is BS.1770-4 for context."
    )
    out.append("")
    out.append(
        "| programme | source | duration | ch | regime | integrated | dialogue-gated (detector) | speech share: detector | Silero | mark |"
    )
    out.append("|---|---|---|---|---|---|---|---|---|---|")
    for f in files:
        out.append(
            f"| {f.item.name} | {f.item.source} | {mmss(f.duration_s)} | {f.channels} | {f.item.regime} | "
            f"{fmt(f.integrated, 1)} | {fmt(f.heur_gated, 1)} ({f.heur_blocks}) | {pct(f.heur_share)} | "
            f"{pct(f.vad_share)} | {regime_mark(f.item.regime, f.heur_share)} |"
        )
    out.append("")
    lines: list[str] = []
    if pairs:
        worst = max(pairs, key=lambda p: abs(p.heur_gated - p.ref_gated))
        n_ok = sum(abs(p.heur_gated - p.ref_gated) <= AGREE_LU for p in pairs)
        lines.append(
            f"**Against the M&E reference the detector's dialogue-gated reading is within {AGREE_LU:.0f} LU on "
            f"{n_ok} of {len(pairs)} programmes.** The largest gap is {worst.heur_gated - worst.ref_gated:+.2f} LU "
            f"on {worst.item.name}, where the detector marks {pct(worst.heur_share)} of the programme as speech "
            f"against the reference's {pct(worst.ref_share)}, but in the wrong places: {pct(worst.precision)} of "
            f"its speech frames are dialogue and it finds {pct(worst.recall)} of the dialogue."
        )
    speech = [f for f in files if f.item.regime == "speech" and f.heur_share is not None]
    nodx = [f for f in files if f.item.regime == "no dialogue" and f.heur_share is not None]
    if speech:
        lines.append(
            f"Clean speech reads {100 * min(x.heur_share for x in speech):.0f} to "
            f"{100 * max(x.heur_share for x in speech):.0f} % speech "
            f"({sum(regime_mark('speech', x.heur_share) == '✓' for x in speech)} of {len(speech)} at or above 80 %)."
        )
    if nodx:
        lines.append(
            f"Material without dialogue reads {100 * min(x.heur_share for x in nodx):.0f} to "
            f"{100 * max(x.heur_share for x in nodx):.0f} % "
            f"({sum(regime_mark('no dialogue', x.heur_share) == '✓' for x in nodx)} of {len(nodx)} under 15 %)."
        )
        sil = [x.vad_share for x in nodx if x.vad_share is not None]
        if sil:
            mx = max(sil)
            lines.append(
                "Silero VAD reads 0 % on all of it."
                if mx < 0.005
                else f"Silero VAD reads at most {100 * mx:.0f} % on it."
            )
    out.append(" ".join(lines))
    if missing:
        out.append("")
        out.append("Not measured because the file was missing: " + ", ".join(missing) + ".")
    out.append("")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", type=Path, default=DOC)
    ap.add_argument("--only", help="run just the items whose name contains this text")
    ap.add_argument("--skip", help="leave out the items whose name contains this text")
    args = ap.parse_args(argv)
    if not CACHE.exists():
        print(f"nothing in {CACHE}; run scripts/fetch_real_dialogue.sh first", file=sys.stderr)
        return 2
    pairs_in, singles_in = catalogue()
    if args.only:
        pairs_in = [i for i in pairs_in if args.only.lower() in i.name.lower()]
        singles_in = [i for i in singles_in if args.only.lower() in i.name.lower()]
    if args.skip:
        pairs_in = [i for i in pairs_in if args.skip.lower() not in i.name.lower()]
        singles_in = [i for i in singles_in if args.skip.lower() not in i.name.lower()]
    missing: list[str] = []
    pairs: list[PairResult] = []
    for item in pairs_in:
        if not item.available():
            missing.append(item.name)
            continue
        print(f"pair    {item.name}", flush=True)
        pairs.append(analyse_pair(item))
        p = pairs[-1]
        print(
            f"        share ref {pct(p.ref_share)} / detector {pct(p.heur_share)} / Silero {pct(p.vad_share)}; "
            f"gated ref {fmt(p.ref_gated, 2)} / detector {fmt(p.heur_gated, 2)} / Silero {fmt(p.vad_gated, 2)}; "
            f"precision {pct(p.precision)} recall {pct(p.recall)}",
            flush=True,
        )
    files: list[FileResult] = []
    for item in singles_in:
        if not item.available():
            missing.append(item.name)
            continue
        print(f"file    {item.name}", flush=True)
        files.append(analyse_file(item))
        f = files[-1]
        print(
            f"        I {fmt(f.integrated, 2)}  DG {fmt(f.heur_gated, 2)}  share {pct(f.heur_share)}  Silero {pct(f.vad_share)}",
            flush=True,
        )
    text = write_report(pairs, files, missing)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
