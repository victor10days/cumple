"""Write a small set of synthetic demo files so cumple can be tried without any real audio.

Run:  uv run python scripts/make_demo.py ~/cumple-demo

Then, for example:
  cumple check ~/cumple-demo/hot.wav --spec netflix-2.0 --sheet
  cumple check ~/cumple-demo/r128-ok.wav --spec ebu-r128 --clauses
  cumple watch ~/cumple-demo/bounces --spec ebu-r128 --once
  cumple diff ~/cumple-demo/v12.wav ~/cumple-demo/v13.wav
  cumple diff ~/cumple-demo/stems/DX.wav ~/cumple-demo/stems/MX.wav ~/cumple-demo/stems/FX.wav --against ~/cumple-demo/stems/PM.wav
  cumple check ~/cumple-demo/EP101_delivery --spec amazon-5.1-package
  cumple fix ~/cumple-demo/spiky.wav --spec ebu-r128 --out ~/cumple-demo/spiky.r128.wav

Everything is seeded noise and tones (no music, no dialogue, no client audio), 48 kHz / 24-bit.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

FS = 48000
rng = np.random.default_rng(2026)


def dbfs(db: float) -> float:
    return 10 ** (db / 20)


def rms_to(x: np.ndarray, db: float) -> np.ndarray:
    return x * dbfs(db) / max(np.sqrt(np.mean(x * x)), 1e-12)


def fade(x: np.ndarray, ms: float = 20.0) -> np.ndarray:
    k = int(FS * ms / 1000)
    ramp = 0.5 - 0.5 * np.cos(np.pi * np.arange(k) / k)
    x = x.copy()
    x[:k] *= ramp[:, None] if x.ndim == 2 else ramp
    x[-k:] *= (ramp[::-1])[:, None] if x.ndim == 2 else ramp[::-1]
    return x


def band_noise(seconds: float, lo: float, hi: float, order: int = 4) -> np.ndarray:
    x = rng.standard_normal(int(FS * seconds))
    sos = butter(order, [lo, hi], btype="band", fs=FS, output="sos")
    return sosfilt(sos, x)


def speech_like(seconds: float) -> np.ndarray:
    """Band-limited noise with syllabic modulation and pauses: what the speech gate calls dialogue."""
    t = np.arange(int(FS * seconds)) / FS
    x = band_noise(seconds, 200, 3400)
    env = 0.5 + 0.5 * np.sin(2 * np.pi * 4.3 * t)
    gate = (np.sin(2 * np.pi * 0.35 * t) > -0.3).astype(float)
    return x * env * gate


def music_like(seconds: float) -> np.ndarray:
    t = np.arange(int(FS * seconds)) / FS
    x = band_noise(seconds, 40, 16000)
    return x * (0.8 + 0.2 * np.sin(2 * np.pi * 0.25 * t))


def fx_like(seconds: float) -> np.ndarray:
    t = np.arange(int(FS * seconds)) / FS
    x = band_noise(seconds, 100, 8000)
    bursts = (np.sin(2 * np.pi * 0.7 * t + 1.0) > 0.6).astype(float)
    return x * (0.15 + bursts)


def tone(seconds: float, db: float, freq: float = 1000.0) -> np.ndarray:
    t = np.arange(int(FS * seconds)) / FS
    return dbfs(db) * np.sin(2 * np.pi * freq * t)


def stereo(x: np.ndarray) -> np.ndarray:
    return np.stack([x, x], axis=1)


def peaking_eq(x: np.ndarray, f0: float, gain_db: float, q: float = 1.0) -> np.ndarray:
    """Audio EQ cookbook peaking filter, applied per channel."""
    a = 10 ** (gain_db / 40)
    w0 = 2 * np.pi * f0 / FS
    alpha = np.sin(w0) / (2 * q)
    b = np.array([1 + alpha * a, -2 * np.cos(w0), 1 - alpha * a])
    aa = np.array([1 + alpha / a, -2 * np.cos(w0), 1 - alpha / a])
    from scipy.signal import lfilter

    return lfilter(b / aa[0], aa / aa[0], x, axis=0)


def write(path: Path, x: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), np.clip(x, -1.0, 1.0), FS, subtype="PCM_24")


def make_demo(out: Path) -> list[Path]:
    out = Path(out)
    written: list[Path] = []

    def put(rel: str, x: np.ndarray) -> None:
        p = out / rel
        write(p, fade(x))
        written.append(p)

    # A bounce that is far too hot for any destination, and one that sits on EBU R 128.
    put("hot.wav", stereo(tone(12, -0.4)))
    put("r128-ok.wav", stereo(tone(12, -23.0)))
    put("bounces/hot.wav", stereo(tone(12, -0.4)))
    put("bounces/r128-ok.wav", stereo(tone(12, -23.0)))

    # Stems and the printmaster they sum to (the stems null against PM exactly).
    dx = rms_to(speech_like(20), -27.0)
    mx = rms_to(music_like(20), -30.0)
    fx = rms_to(fx_like(20), -33.0)
    pm = dx + mx + fx
    put("stems/DX.wav", stereo(dx))
    put("stems/MX.wav", stereo(mx))
    put("stems/FX.wav", stereo(fx))
    put("stems/PM.wav", stereo(pm))

    # Two versions of the same mix: v13 is v12 at -1.4 dB, 23 samples late, with a +3 dB bell at 2.5 kHz.
    v12 = stereo(pm)
    v13 = peaking_eq(v12, 2500.0, 3.0) * dbfs(-1.4)
    v13 = np.concatenate([np.zeros((23, 2)), v13[:-23]])
    put("v12.wav", v12)
    put("v13.wav", v13)

    # A 5.1 delivery as discrete mono files, roles in the filename suffixes (how Amazon asks for it).
    c = rms_to(speech_like(20), -31.0)
    lr = [rms_to(music_like(20), -36.0) for _ in range(2)]
    surr = [rms_to(music_like(20), -44.0) for _ in range(2)]
    lfe = sosfilt(butter(4, 80, btype="low", fs=FS, output="sos"), rng.standard_normal(20 * FS))
    lfe = rms_to(lfe, -34.0)
    for name, x in [("L", lr[0]), ("R", lr[1]), ("C", c), ("LFE", lfe), ("Ls", surr[0]), ("Rs", surr[1])]:
        put(f"EP101_delivery/EP101_PM_51_{name}.wav", x)

    # Quiet programme with one loud click: gain alone cannot make it comply, so `fix` refuses.
    q = rms_to(band_noise(12, 100, 8000), -32.0)
    q[5 * FS : 5 * FS + 48] += np.hanning(48) * 0.7
    put("spiky.wav", stereo(q))
    return written


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    files = make_demo(Path(argv[1]).expanduser())
    print(f"wrote {len(files)} files under {Path(argv[1]).expanduser()}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
