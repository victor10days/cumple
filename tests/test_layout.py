from __future__ import annotations

import numpy as np
import soundfile as sf

from cumple.checks import Status, evaluate
from cumple.meters.layout import LayoutMeter
from cumple.meters.measure import measure
from cumple.specs import get

FS = 48000


def band_noise(seconds: float, lo: float | None, hi: float | None, rms_dbfs: float, seed: int) -> np.ndarray:
    """Gaussian noise band-limited by FFT masking, scaled to an RMS level."""
    rng = np.random.default_rng(seed)
    n = int(FS * seconds)
    spec = np.fft.rfft(rng.normal(size=n))
    freqs = np.fft.rfftfreq(n, 1 / FS)
    mask = np.ones_like(freqs, dtype=bool)
    if lo is not None:
        mask &= freqs >= lo
    if hi is not None:
        mask &= freqs <= hi
    x = np.fft.irfft(spec * mask, n)
    x *= 10 ** (rms_dbfs / 20) / np.sqrt(np.mean(x * x))
    return x


def five_one(tmp_path, name, order="smpte", lfe_full_range=False, lfe_silent=False):
    seconds = 4.0
    full = [band_noise(seconds, 40, 16000, -26.0, s) for s in range(5)]
    lfe = (
        np.zeros(int(FS * seconds))
        if lfe_silent
        else (band_noise(seconds, 40, 16000, -30.0, 9) if lfe_full_range else band_noise(seconds, 20, 100, -30.0, 9))
    )
    if order == "smpte":
        chans = [full[0], full[1], full[2], lfe, full[3], full[4]]
    else:  # film: L C R Ls Rs LFE
        chans = [full[0], full[2], full[1], full[3], full[4], lfe]
    path = tmp_path / name
    sf.write(str(path), np.stack(chans, 1), FS, subtype="PCM_24")
    return path


def test_layout_meter_finds_the_lfe():
    x = np.stack([band_noise(2, 40, 16000, -20, 1), band_noise(2, 20, 100, -20, 2)], 1)
    m = LayoutMeter(FS, 2)
    for i in range(0, len(x), 5000):
        m.feed(x[i : i + 5000])
    r = m.result()
    assert r.lfe_like == 1
    assert r.hf_ratio_db[0] > -1.0 and r.hf_ratio_db[1] < -20.0


def test_smpte_file_passes_apple_lfe_and_order_rules(tmp_path):
    p = five_one(tmp_path, "smpte.wav")
    r = evaluate(get("apple-tv"), measure(p))
    c = {f.code: f for f in r.findings}
    assert c["format.lfe_band"].status is Status.PASS
    assert c["format.channel_order"].status is Status.PASS


def test_full_range_lfe_fails_apple(tmp_path):
    p = five_one(tmp_path, "fullrange.wav", lfe_full_range=True)
    r = evaluate(get("apple-tv"), measure(p))
    c = {f.code: f for f in r.findings}
    assert c["format.lfe_band"].status is Status.FAIL
    assert "low-pass" in c["format.lfe_band"].fix


def test_film_order_is_caught(tmp_path):
    p = five_one(tmp_path, "film.wav", order="film")
    r = evaluate(get("netflix-5.1"), measure(p))
    c = {f.code: f for f in r.findings}
    assert c["format.channel_order"].status is Status.FAIL
    assert "Film order" in c["format.channel_order"].note


def test_silent_lfe_is_reported_not_failed(tmp_path):
    p = five_one(tmp_path, "silentlfe.wav", lfe_silent=True)
    r = evaluate(get("apple-tv"), measure(p))
    c = {f.code: f for f in r.findings}
    assert c["format.lfe_band"].status is Status.INFO
    assert c["signal.silent_channels"].status is Status.WARN and "LFE" in c["signal.silent_channels"].measured


def test_lfe_band_check_follows_the_profile_corner(tmp_path):
    from scipy.signal import butter, sosfilt

    from cumple.meters.measure import measure_args

    rng = np.random.default_rng(3)
    n = FS * 6
    beds = [band_noise(6, 80, 12000, -30.0, k) for k in range(5)]
    lfe = sosfilt(butter(8, 130, btype="low", fs=FS, output="sos"), rng.normal(size=n))
    lfe *= 10 ** (-20 / 20) / np.sqrt(np.mean(lfe * lfe))  # an LFE low-passed at 130 Hz, 48 dB/octave
    x = np.stack([beds[0], beds[1], beds[2], lfe, beds[3], beds[4]], axis=1)
    p = tmp_path / "mix51.wav"
    sf.write(str(p), x, FS, subtype="PCM_24")
    netflix = get("netflix-5.1")  # 120 Hz corner: the check looks above 240 Hz
    r = evaluate(netflix, measure(p, **measure_args(netflix)))
    assert {f.code: f.status for f in r.findings}["format.lfe_band"] is Status.PASS
    strict = netflix.model_copy(deep=True)
    strict.format.lfe_lowpass_hz = 60.0  # now the check looks above 120 Hz, where this LFE is still busy
    r2 = evaluate(strict, measure(p, **measure_args(strict)))
    assert {f.code: f.status for f in r2.findings}["format.lfe_band"] is Status.FAIL
