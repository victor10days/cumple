from __future__ import annotations

import numpy as np
import pytest
import soundfile as sf
from scipy.signal import freqz

from cumple.checks import Status, evaluate
from cumple.io.reader import read_metadata
from cumple.meters.dialogue import SpeechDetector
from cumple.meters.leqm import TASA_M_WEIGHTING, LeqmMeter, m_weighting_fir
from cumple.meters.measure import measure
from cumple.specs import get
from tests.bwf import add_bext
from tests.test_layout import band_noise

FS = 48000


def speech_like(seconds: float, level_db: float, seed: int = 21) -> np.ndarray:
    """Band-limited noise with 4 Hz syllabic bursts: what the heuristic calls speech."""
    x = band_noise(seconds, 200, 3000, level_db, seed)
    t = np.arange(len(x)) / FS
    env = 0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 4 * t))  # 125 ms on, 125 ms off
    env = np.convolve(env, np.ones(480) / 480, mode="same")
    y = x * env
    return y * 10 ** (level_db / 20) / np.sqrt(np.mean(y * y))


def music_like(seconds: float, level_db: float, seed: int = 22) -> np.ndarray:
    return band_noise(seconds, 40, 16000, level_db, seed)


def stereo(x: np.ndarray) -> np.ndarray:
    return np.repeat(x[:, None], 2, axis=1)


def detect(x: np.ndarray) -> float:
    d = SpeechDetector(FS, x.shape[1])
    for i in range(0, len(x), 100000):
        d.feed(x[i : i + 100000])
    return d.result().fraction


def test_speech_like_and_music_like_are_told_apart():
    assert detect(stereo(speech_like(8, -27))) > 0.8
    assert detect(stereo(music_like(8, -20))) < 0.2


def test_dialogue_gated_reads_the_speech_not_the_music(tmp_path):
    speech = [stereo(speech_like(10, -32)), stereo(speech_like(10, -32, seed=23))]
    x = np.concatenate([speech[0], stereo(music_like(10, -18)), speech[1]])
    sf.write(str(tmp_path / "prog.wav"), x, FS, subtype="PCM_24")
    sf.write(str(tmp_path / "speech-only.wav"), np.concatenate(speech), FS, subtype="PCM_24")
    m = measure(tmp_path / "prog.wav")
    reference = measure(tmp_path / "speech-only.wav").loudness.integrated_ungated
    assert 0.5 < m.speech_fraction < 0.8
    assert m.loudness.dialogue_gated == pytest.approx(
        reference, abs=1.0
    )  # reads the dialogue, not the music (boundary blocks carry a little music)
    assert m.loudness.integrated > m.loudness.dialogue_gated + 3  # the music pulls the integrated value up
    assert -29 < m.loudness.dialogue_gated < -25  # inside Netflix's window, by construction
    r = evaluate(get("netflix-2.0"), m)
    f = {x.code: x for x in r.findings}
    assert f["loudness.dialogue_gated"].status is Status.PASS
    assert "speech gate" in f["loudness.dialogue_gated"].note


def test_music_only_programme_flips_netflix_to_the_minus_24_rule(tmp_path):
    sf.write(str(tmp_path / "music.wav"), stereo(music_like(12, -30)), FS, subtype="PCM_24")  # about -24 LUFS
    m = measure(tmp_path / "music.wav")
    assert m.speech_fraction < 0.15
    r = evaluate(get("netflix-2.0"), m)
    codes = {x.code: x for x in r.findings}
    assert codes["loudness.integrated"].status is Status.PASS and "-24" in codes["loudness.integrated"].limit
    assert "loudness.dialogue_gated" not in codes


def test_m_weighting_response_is_inside_the_tasa_tolerances():
    h = m_weighting_fir(FS)
    freqs = [f for f, _, _ in TASA_M_WEIGHTING if f < FS / 2]
    _, resp = freqz(h, worN=freqs, fs=FS)
    for (f, target, tol), r in zip([t for t in TASA_M_WEIGHTING if t[0] < FS / 2], resp, strict=True):
        got = 20 * np.log10(abs(r))
        assert abs(got - target) <= max(tol, 0.15), (f, got, target, tol)


def tone(freq: float, rms_dbfs: float, seconds: float = 4.0) -> np.ndarray:
    t = np.arange(int(FS * seconds)) / FS
    return np.sqrt(2) * 10 ** (rms_dbfs / 20) * np.sin(2 * np.pi * freq * t)


def leqm_of(x: np.ndarray, roles: list[str]) -> float:
    m = LeqmMeter(FS, x.shape[1], roles=roles)
    for i in range(0, len(x), 70000):
        m.feed(x[i : i + 70000])
    return m.result().leqm_db


def test_leqm_calibration_and_channel_weights():
    n = int(FS * 4)
    x = np.zeros((n, 6))
    x[:, 0] = tone(2000, -20)
    assert leqm_of(x, ["L", "R", "C", "LFE", "Ls", "Rs"]) == pytest.approx(85.0, abs=0.2)
    y = np.zeros((n, 6))
    y[:, 4] = tone(2000, -20)
    assert leqm_of(y, ["L", "R", "C", "LFE", "Ls", "Rs"]) == pytest.approx(82.0, abs=0.2)
    z = np.zeros((n, 6))
    for i in (0, 1, 2, 4, 5):
        z[:, i] = tone(2000, -20)
    assert leqm_of(z, ["L", "R", "C", "LFE", "Ls", "Rs"]) == pytest.approx(85 + 10 * np.log10(3 + 2 * 0.5), abs=0.2)


def test_tasa_profile_fails_a_hot_trailer_and_passes_a_quiet_one(tmp_path):
    n = int(FS * 6)
    hot = np.zeros((n, 6))
    for i in (0, 1, 2):
        hot[:, i] = tone(2000, -16, seconds=6)  # three screen channels at -16: 89 + 4.8 dB
    sf.write(str(tmp_path / "hot.wav"), hot, FS, subtype="PCM_24")
    r = evaluate(get("tasa-trailer"), measure(tmp_path / "hot.wav", leqm=True))
    f = {x.code: x for x in r.findings}
    assert f["leqm.level"].status is Status.FAIL and "lower the whole mix" in f["leqm.level"].fix
    quiet = hot * 10 ** (-12 / 20)
    sf.write(str(tmp_path / "quiet.wav"), quiet, FS, subtype="PCM_24")
    r = evaluate(get("tasa-trailer"), measure(tmp_path / "quiet.wav", leqm=True))
    assert {x.code: x for x in r.findings}["leqm.level"].status is Status.PASS


def test_acx_rms_and_noise_floor(tmp_path):
    voice = speech_like(20, -20)
    floor = band_noise(20, 50, 8000, -70, 5)
    x = (voice + floor)[:, None]
    sf.write(str(tmp_path / "chapter.wav"), x, 44100, subtype="PCM_16")
    m = measure(tmp_path / "chapter.wav")
    assert -23.5 < m.rms_dbfs < -17.5
    assert m.noise_floor_dbfs < -60
    r = evaluate(get("acx"), m)
    f = {x.code: x for x in r.findings}
    assert (
        f["rms.level"].status is Status.PASS
        and f["rms.noise_floor"].status is Status.PASS
        and f["duration.max"].status is Status.PASS
    )
    loud = (voice * 10 ** (6 / 20) + floor)[:, None]
    sf.write(str(tmp_path / "loud.wav"), loud, 44100, subtype="PCM_16")
    r = evaluate(get("acx"), measure(tmp_path / "loud.wav"))
    assert {x.code: x for x in r.findings}["rms.level"].status is Status.FAIL


def test_bext_loudness_metadata_is_checked_against_the_measurement(tmp_path):
    from tests.test_engine import tone_file

    honest = tone_file(tmp_path / "honest.wav", dbfs=-23.0)
    add_bext(honest, loudness_value=-2300, loudness_range=0)
    meta = read_metadata(honest)
    assert "bext" in meta and meta["bext"].get("loudness_value") in (-2300, -23.0)
    r = evaluate(get("ebu-r128"), measure(honest))
    assert {x.code: x for x in r.findings}["metadata.bext_loudness"].status is Status.PASS
    liar = tone_file(tmp_path / "liar.wav", dbfs=-23.0)
    add_bext(liar, loudness_value=-2500)
    r = evaluate(get("ebu-r128"), measure(liar))
    f = {x.code: x for x in r.findings}["metadata.bext_loudness"]
    assert f.status is Status.FAIL and "re-write" in f.fix
    unset = tone_file(tmp_path / "unset.wav", dbfs=-23.0)
    add_bext(unset)  # 7FFFh everywhere
    r = evaluate(get("ebu-r128"), measure(unset))
    assert {x.code: x for x in r.findings}["metadata.bext_loudness"].status is Status.INFO


def test_json_output_survives_bwf_metadata_bytes(tmp_path):
    import json

    from cumple.report import report_to_dict

    p = tmp_path / "bwf.wav"
    sf.write(str(p), stereo(music_like(3, -23)), FS, subtype="PCM_24")
    add_bext(p, loudness_value=-2300)
    m = measure(p)
    assert m.info is not None and m.info.bext  # wavinfo hands the UMID back as bytes
    text = json.dumps(report_to_dict(evaluate(get("ebu-r128"), m)))
    assert '"bext"' in text


def test_a_file_too_short_for_the_speech_detector_says_so(tmp_path):
    p = tmp_path / "sting.wav"
    sf.write(str(p), stereo(speech_like(1.0, -27)), FS, subtype="PCM_24")
    m = measure(p)
    assert m.speech_fraction is None
    r = evaluate(get("netflix-2.0"), m)
    speech = next(f for f in r.findings if f.code == "loudness.speech")
    assert "not measurable" in speech.measured
    longer = tmp_path / "long.wav"
    sf.write(str(longer), stereo(speech_like(3.0, -27)), FS, subtype="PCM_24")
    assert measure(longer).speech_fraction > 0.8


def test_leqm_weighs_a_partial_second_by_its_length():
    t1 = np.arange(FS) / FS
    quiet = 10 ** (-40 / 20) * np.sin(2 * np.pi * 2000 * t1)
    loud = 10 ** (-20 / 20) * np.sin(2 * np.pi * 2000 * t1[: FS // 2])
    short = np.concatenate([quiet, loud])[:, None]  # 1.0 s quiet + 0.5 s loud
    same_mix_no_partial = np.concatenate([quiet, quiet, loud, loud])[:, None]  # 2 s + 1 s: whole seconds only
    a, b = LeqmMeter(FS, 1, roles=["L"]), LeqmMeter(FS, 1, roles=["L"])
    a.feed(short)
    b.feed(same_mix_no_partial)
    ra, rb = a.result(), b.result()
    assert ra.leqm_db == pytest.approx(rb.leqm_db, abs=0.1)  # the half second must not count as a whole one
    assert len(ra.per_second_db) == 2 and len(rb.per_second_db) == 3


def test_leqm_reports_the_calibration_it_was_given():
    m = LeqmMeter(FS, 1, roles=["L"], calibration_dbfs=-18.0, calibration_db=82.0)
    m.feed(np.zeros((FS, 1)))
    r = m.result()
    assert (r.calibration_dbfs, r.calibration_db) == (-18.0, 82.0)
