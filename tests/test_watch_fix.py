from __future__ import annotations

import csv

import numpy as np
import soundfile as sf

from cumple.checks import evaluate
from cumple.fix import fix_file, plan
from cumple.meters.measure import measure
from cumple.specs import get
from cumple.watch import Watcher, watch
from tests.test_engine import tone_file


def test_watch_waits_for_a_file_to_stop_growing(tmp_path):
    folder = tmp_path / "bounces"
    folder.mkdir()
    ready = tone_file(folder / "done.wav", dbfs=-23.0, seconds=3)
    growing = folder / "growing.wav"
    sr = 48000
    t = np.arange(sr * 3) / sr
    data = np.repeat((10 ** (-23 / 20) * np.sin(2 * np.pi * 1000 * t))[:, None], 2, axis=1)
    fh = sf.SoundFile(str(growing), "w", samplerate=sr, channels=2, subtype="PCM_24")
    fh.write(data[:sr])
    fh.flush()

    clock = {"t": 1000.0}
    w = Watcher(folder, get("ebu-r128"), stable_s=5.0, log_csv=folder / "cumple-log.csv", clock=lambda: clock["t"])
    assert w.poll() == []  # first sight: sizes recorded, nothing measured
    clock["t"] += 6
    fh.write(data[sr:])  # the bounce keeps growing
    fh.flush()
    got = w.poll()  # done.wav has held still for 6 s; growing.wav changed, so its clock restarts
    assert [(p.name, r.verdict) for p, r, _, _ in got] == [("done.wav", "PASS")]
    fh.close()  # closing rewrites the WAV header: the file changed again, so its clock restarts
    clock["t"] += 3
    assert w.poll() == []  # changed on close, seen again now
    clock["t"] += 3
    assert w.poll() == []  # held still for only 3 s
    clock["t"] += 3
    got = w.poll()
    assert [(p.name, r.verdict) for p, r, _, _ in got] == [("growing.wav", "PASS")]
    assert sf.info(str(growing)).frames == sr * 3  # measured only once complete, and untouched
    assert (folder / "done.qc.html").exists() and (folder / "growing.qc.json").exists()
    rows = list(csv.DictReader((folder / "cumple-log.csv").open()))
    assert [r["file"] for r in rows] == ["done.wav", "growing.wav"] and all(r["verdict"] == "PASS" for r in rows)
    # a fresh watcher skips files that already have a sheet
    w2 = Watcher(folder, get("ebu-r128"), stable_s=5.0, clock=lambda: clock["t"])
    assert w2.poll() == [] and w2.pending() == []
    # and the one-pass entry point ends by itself
    assert watch(folder, get("ebu-r128"), once=True, clock=lambda: clock["t"], sleep=lambda s: clock.__setitem__("t", clock["t"] + s)) == 0
    assert ready.exists()


def test_fix_raises_a_quiet_file_and_refuses_when_headroom_is_missing(tmp_path):
    quiet = tone_file(tmp_path / "quiet.wav", dbfs=-30.0)
    fp, dst, after = fix_file(quiet, get("ebu-r128"))
    assert fp.gain_db is not None and abs(fp.gain_db - 7.0) < 0.1
    assert dst is not None and dst.name == "quiet.ebu-r128.wav"
    assert abs(after.loudness.integrated + 23.0) < 0.1
    assert evaluate(get("ebu-r128"), after).passed
    # a -0.4 dBFS tone is at -0.4 LUFS: to reach -23 it must drop 22.6 dB, which is fine for peaks;
    # but a file that is quiet AND already peaking cannot be raised
    sr = 48000
    t = np.arange(sr * 8) / sr
    x = 0.02 * np.sin(2 * np.pi * 1000 * t)
    x[sr : sr + 480] = 0.99  # a burst that already touches full scale
    sf.write(str(tmp_path / "spiky.wav"), np.repeat(x[:, None], 2, axis=1), sr, subtype="PCM_24")
    fp2 = plan(get("ebu-r128"), measure(tmp_path / "spiky.wav"))
    assert fp2.gain_db is None and "headroom" in fp2.reason
