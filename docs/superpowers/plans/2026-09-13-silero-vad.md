# Silero VAD dialogue-gate backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `cumple check --vad silero` (or `CUMPLE_VAD=silero`) runs Silero VAD v6.2 through onnxruntime for the speech mask behind dialogue-gated loudness, the heuristic stays the default, every report surface names which backend made the mask, and `docs/DIALOGUE.md` measures both on the same two open films.

**Architecture:** One new module `src/cumple/meters/vad.py` with `SileroDetector`, which has the same `feed` and `result` interface as `SpeechDetector`, composes one `SpeechDetector` for the per-frame levels, resamples the picked channel to 16 kHz in overlapping chunks, runs the model in 512-sample windows with carried state, maps the 32 ms decisions onto the heuristic's 20 ms grid and dilates them with the same rule (moved to `dialogue.dilate_mask`). `SpeechResult` gains `backend`. `measure()` takes `vad=`; the engine and the sheet describe the backend through one `describe_backend()`; JSON carries `speech_backend`. The model (2.3 MB, MIT) ships as package data under `src/cumple/models/`; onnxruntime is the `vad` extra and a dev dependency so CI runs the tests on all three runners. `scripts/dialogue_benchmark.py` uses the detector instead of its own inference.

**Tech Stack:** Python 3.12, numpy, scipy (`resample_poly`), onnxruntime 1.30 (optional), pytest, ruff. Model: Silero VAD v6.2 ONNX (the file at upstream tags v6.2 and v6.2.1; v5.1.2 is a different file), sha256 prefix `1a153a22f4509e29`, at `~/.cache/cumple/silero_vad.onnx` on this Mac (fetched by `scripts/fetch_real_dialogue.sh`).

**Spec:** `docs/graph-runs/2026-09-13-silero-vad/01-frame.md`.

## Global Constraints

- No new dependency in the base install. `pyproject.toml` gains `vad = ["onnxruntime>=1.17"]` under `[project.optional-dependencies]` and `"onnxruntime>=1.17"` in the `dev` dependency group; nothing else in `dependencies`.
- The model is bundled at `src/cumple/models/silero_vad.onnx` with `src/cumple/models/__init__.py` (empty, one docstring line) and `src/cumple/models/SILERO_LICENSE` (the MIT licence text with Silero Team's copyright line); never downloaded at run time. `CUMPLE_SILERO_MODEL` may point at another file.
- Streaming: the detector keeps at most one 10 s chunk of the picked channel plus one model window in memory.
- The word "heuristic" and the phrase "Silero VAD" reach the engine notes, the sheet footer and the JSON through `describe_backend()` and `SpeechResult.backend` only; no report string names a backend on its own.
- Test fixture: `tests/fixtures/speech-librivox-3s.wav`, 16 kHz mono 16-bit, 3 s cut from LibriVox "William Again" chapter 1 (public domain), made by the command in Task 1; `tests/fixtures/NOTICE.md` states the provenance. No other audio is committed.
- Tests that need onnxruntime use `needs_onnx = pytest.mark.skipif(importlib.util.find_spec("onnxruntime") is None, reason=...)`; with the dev group carrying onnxruntime they run in CI.
- `uv run pytest` alone, never piped, once in full before each commit; re-pin the five documented counts (README `**Tests**: N,` and `runs N-29 of them on Ubuntu`, CONTRIBUTING `# N tests;`, docs/QA.md `` `uv run pytest`, N tests``, AI_USAGE `N tests, including`, site/index.html `N tests with 91 %`) from `uv run pytest --collect-only 2>/dev/null | grep 'tests collected'`; README's "G fewer on macOS" and "G+1 fewer on Windows" stay at 19 and 20 unless a new test is gated on ffmpeg (none in this plan is).
- `uv run ruff check src tests scripts && uv run ruff format src tests scripts` clean before each commit.
- No em or en dashes in prose, comments or docstrings; the phrase "not checked" never appears.
- Commit messages: one plain imperative sentence, a blank line, then exactly:
  Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_01Mbp3Bc2YHhHX3z5bC28aha
- Work from `/Users/Victor/Code/cumple-wt/loop-03-vad`; never `cd` to `~/Code/cumple`.

---

### Task 1: The detector, the model, the extra

**Files:**
- Modify: `src/cumple/meters/dialogue.py` (add `dilate_mask`, `describe_backend`, `SpeechResult.backend`; rename `_channel` to `pick_channel`)
- Create: `src/cumple/meters/vad.py`, `src/cumple/models/__init__.py`, `src/cumple/models/silero_vad.onnx`, `src/cumple/models/SILERO_LICENSE`, `tests/fixtures/speech-librivox-3s.wav`, `tests/fixtures/NOTICE.md`
- Modify: `pyproject.toml` (extra and dev group)
- Test: `tests/test_vad.py`

**Interfaces:**
- Consumes: `SpeechDetector`, `SpeechResult`, `FRAME_S`, `SILENCE_DBFS`, `CONTEXT_S`, `CONTEXT_MIN_DENSITY` from `dialogue.py`.
- Produces: `dialogue.dilate_mask(voiced: np.ndarray) -> np.ndarray`; `dialogue.describe_backend(backend: str) -> str` ("heuristic speech gate" or "Silero VAD v6.2 gate"; the licence and the words "neural speech detector" live in the README and the module docstring, not in a note); `SpeechResult.backend: str = "heuristic"`; `SpeechDetector.pick_channel(x)`; `vad.BACKENDS = ("heuristic", "silero")`; `vad.VadUnavailable(RuntimeError)`; `vad.model_path() -> Path`; `vad.load_session()`; `vad.SileroDetector(samplerate, channels, roles=None, session=None)` with `feed(block)` and `result() -> SpeechResult` whose `backend == "silero"`.

- [ ] **Step 1: Bring in the model, the licence, the fixture, the extra**

```bash
mkdir -p src/cumple/models tests/fixtures
cp ~/.cache/cumple/silero_vad.onnx src/cumple/models/silero_vad.onnx
shasum -a 256 src/cumple/models/silero_vad.onnx   # must start 1a153a22f4509e29; record the full hash for the test
printf '"""Bundled model files. silero_vad.onnx is Silero VAD v6.2, Silero Team, MIT (see SILERO_LICENSE)."""\n' > src/cumple/models/__init__.py
curl -fsSL https://raw.githubusercontent.com/snakers4/silero-vad/master/LICENSE -o src/cumple/models/SILERO_LICENSE
ffmpeg -y -nostdin -v error -ss 12 -t 3 -i ~/.cache/cumple/real-dialogue/librivox/william_again_ch01.mp3 -ac 1 -ar 16000 -c:a pcm_s16le tests/fixtures/speech-librivox-3s.wav
```

If the curl fails, write `SILERO_LICENSE` by hand as the MIT licence text with the first line `MIT License` and the copyright line `Copyright (c) 2020-present Silero Team`. Check the downloaded file says MIT; if it does not, stop and report.

`tests/fixtures/NOTICE.md`:

```markdown
# Test fixtures

`speech-librivox-3s.wav`: three seconds (12 s to 15 s) of LibriVox, "William Again" by Richmal Crompton, chapter 1, read for LibriVox, whose recordings are in the public domain in the United States (the text is by Richmal Crompton, who died in 1969, so the text's status differs elsewhere); 16 kHz mono 16-bit, made with ffmpeg by the command in `docs/superpowers/plans/2026-09-13-silero-vad.md`. It is the one audio file in the repository and exists so the speech detectors have a real voice to be tested on in CI.
```

In `pyproject.toml`, under `[project.optional-dependencies]` add `vad = ["onnxruntime>=1.17"]` after `app-qt`, and in `[dependency-groups] dev` add `"onnxruntime>=1.17",` after `"loudcheck>=0.3.2",`. Run `uv sync --group dev` and `uv run python -c "import onnxruntime; print(onnxruntime.__version__)"`.

- [ ] **Step 2: Write the failing tests**

```python
"""Silero VAD as the second speech detector: same grid, same dilation, a different mask."""

from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from cumple.meters.dialogue import FRAME_S, SpeechDetector, SpeechResult, describe_backend, dilate_mask
from cumple.meters.vad import BACKENDS, SileroDetector, VadUnavailable, load_session, model_path

FIXTURE = Path(__file__).parent / "fixtures" / "speech-librivox-3s.wav"
MODEL_SHA256 = "1a153a22f4509e29"  # replace with the full 64-character hash from Step 1
needs_onnx = pytest.mark.skipif(importlib.util.find_spec("onnxruntime") is None, reason="onnxruntime is not installed")


def test_dilate_mask_fills_a_pause_inside_dialogue_and_leaves_an_isolated_frame_alone():
    voiced = np.zeros(200, dtype=bool)
    voiced[50:70] = True
    voiced[75:95] = True  # a 100 ms pause between two phrases
    voiced[150] = True  # one frame on its own
    mask = dilate_mask(voiced)
    assert mask[70:75].all()
    assert mask[50:95].all()
    assert not mask[110:140].any()  # the rule dilates ten frames past a phrase, not forty
    assert mask[150] and not mask[130:149].any()


def test_describe_backend_names_both_and_refuses_others():
    assert describe_backend("heuristic") == "heuristic speech gate"
    assert describe_backend("silero").startswith("Silero VAD v6.2")
    with pytest.raises(ValueError):
        describe_backend("dolby")
    assert BACKENDS == ("heuristic", "silero")


def test_speech_result_defaults_to_the_heuristic_backend():
    r = SpeechResult(FRAME_S, np.zeros(0, bool), np.zeros(0, bool), np.zeros(0), None)
    assert r.backend == "heuristic"


def test_the_bundled_model_is_the_known_file():
    p = model_path()
    assert p.name == "silero_vad.onnx" and p.is_file()
    assert p.stat().st_size == 2327524
    assert hashlib.sha256(p.read_bytes()).hexdigest() == MODEL_SHA256
    assert (p.parent / "SILERO_LICENSE").read_text(encoding="utf-8").startswith("MIT License")


def test_model_path_honours_the_override(monkeypatch, tmp_path):
    monkeypatch.setenv("CUMPLE_SILERO_MODEL", str(tmp_path / "other.onnx"))
    assert model_path() == tmp_path / "other.onnx"


def test_without_onnxruntime_the_error_names_the_extra(monkeypatch):
    monkeypatch.setitem(sys.modules, "onnxruntime", None)  # import raises ImportError
    with pytest.raises(VadUnavailable) as e:
        load_session()
    assert 'cumple[vad]' in str(e.value)


@needs_onnx
def test_a_missing_model_file_is_reported_not_swallowed(monkeypatch, tmp_path):
    monkeypatch.setenv("CUMPLE_SILERO_MODEL", str(tmp_path / "missing.onnx"))
    with pytest.raises(VadUnavailable) as e:
        load_session()
    assert "missing.onnx" in str(e.value)


def _feed(det, data: np.ndarray, block: int) -> SpeechResult:
    for i in range(0, len(data), block):
        det.feed(data[i : i + block])
    return det.result()


@needs_onnx
def test_silero_finds_speech_on_the_librivox_excerpt():
    x, fs = sf.read(str(FIXTURE), dtype="float64", always_2d=True)
    assert fs == 16000 and x.shape[1] == 1
    r = _feed(SileroDetector(fs, 1), x, 4096)
    assert r.backend == "silero"
    assert r.fraction is not None and r.fraction > 0.6
    assert len(r.mask) == len(r.level_db) == int(len(x) / fs / FRAME_S)


@needs_onnx
def test_silero_reads_no_speech_on_white_noise_at_48k():
    rng = np.random.default_rng(1)
    x = (0.05 * rng.standard_normal((48000 * 3, 2))).astype(np.float64)
    r = _feed(SileroDetector(48000, 2), x, 8192)
    assert r.fraction is not None and r.fraction < 0.05
    assert len(r.mask) == int(3 / FRAME_S)


@needs_onnx
def test_chunked_resampling_gives_the_unchunked_decisions(monkeypatch):
    """Three 10 s chunks with the carried tail must decide like one resample of the whole signal."""
    from scipy.signal import resample_poly

    import cumple.meters.vad as mod

    x16, _ = sf.read(str(FIXTURE), dtype="float64", always_2d=True)
    x441 = resample_poly(np.tile(x16[:, 0], 9), 441, 160)[:, None]  # 27 s at 44.1 kHz, pauses at the joins
    chunked = _feed(SileroDetector(44100, 1), x441, 1024).mask  # CHUNK_S 10: three resample calls, the tail path runs
    monkeypatch.setattr(mod, "CHUNK_S", 1000.0)  # one resample of everything at result(): the reference
    whole = _feed(SileroDetector(44100, 1), x441, 1024).mask
    assert len(chunked) == len(whole) == int(27 / FRAME_S)
    assert int((chunked != whole).sum()) <= 2  # a doubled or dropped tail shifts the windows and dozens of frames differ


@needs_onnx
def test_silero_uses_the_centre_channel_when_there_is_one():
    x16, _ = sf.read(str(FIXTURE), dtype="float64", always_2d=True)
    rng = np.random.default_rng(2)
    noise = 0.05 * rng.standard_normal((len(x16), 6))
    six = noise.copy()
    six[:, 2] = x16[:, 0]  # speech on C only, roles L R C LFE Ls Rs
    r = _feed(SileroDetector(16000, 6, roles=["L", "R", "C", "LFE", "Ls", "Rs"]), six, 4096)
    assert r.fraction is not None and r.fraction > 0.6


def test_the_heuristic_still_uses_dilate_mask(monkeypatch):
    """The refactor must leave the heuristic's result on the shared rule."""
    called = {"n": 0}
    import cumple.meters.dialogue as mod

    real = mod.dilate_mask

    def spy(v):
        called["n"] += 1
        return real(v)

    monkeypatch.setattr(mod, "dilate_mask", spy)
    x, fs = sf.read(str(FIXTURE), dtype="float64", always_2d=True)
    _feed(SpeechDetector(fs, 1), x, 4096)
    assert called["n"] == 1
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `uv run pytest tests/test_vad.py -v`
Expected: FAIL at import (`cumple.meters.vad` missing; `dilate_mask` and `describe_backend` missing).

- [ ] **Step 4: The shared pieces in dialogue.py**

In `src/cumple/meters/dialogue.py`:

Add `backend: str = "heuristic"` as the last field of `SpeechResult`, with the comment `# "heuristic" or "silero": which detector made the mask`.

Rename `_channel` to `pick_channel` (definition and its one use in `feed`).

Add, after the constants and before `SpeechResult`:

```python
BACKEND_NAMES = {
    "heuristic": "heuristic speech gate",
    "silero": "Silero VAD v6.2 gate",
}


def describe_backend(backend: str) -> str:
    """The words every report uses for the detector that made the speech mask."""
    try:
        return BACKEND_NAMES[backend]
    except KeyError:
        raise ValueError(f"unknown speech detector {backend!r}; choose one of {', '.join(BACKEND_NAMES)}") from None


def dilate_mask(voiced: np.ndarray) -> np.ndarray:
    """Dialogue regions, not just voiced frames: a frame counts as speech when at least
    CONTEXT_MIN_DENSITY of the frames within CONTEXT_S around it are voiced. A pause inside
    dialogue is still dialogue."""
    w = max(int(CONTEXT_S / FRAME_S), 1)
    c = np.concatenate([[0.0], np.cumsum(voiced.astype(float))])
    idx = np.arange(len(voiced))
    lo = np.maximum(idx - w // 2, 0)
    hi = np.minimum(idx + w // 2, len(voiced))
    density = (c[hi] - c[lo]) / np.maximum(hi - lo, 1)
    return voiced | (density >= CONTEXT_MIN_DENSITY)
```

In `SpeechDetector.result()`, replace the block from the comment `# Dialogue regions, not just voiced frames` through `mask = voiced | (density >= CONTEXT_MIN_DENSITY)` with `mask = dilate_mask(voiced)`.

- [ ] **Step 5: The detector module**

`src/cumple/meters/vad.py`:

```python
"""Silero VAD as a second speech detector for dialogue-gated loudness, behind the `vad` extra.

Silero VAD v6.2 (Silero Team, MIT) is a small neural voice-activity model. It runs offline through
onnxruntime on 16 kHz mono in 512-sample windows. This detector resamples the picked channel in
overlapping chunks, carries the model's state across windows, and returns the same SpeechResult
the heuristic does, on the same 20 ms grid, dilated by the same rule, so the meter and the engine
cannot tell which backend made the mask except by its name. It is not Dolby's algorithm either.
"""

from __future__ import annotations

import os
from importlib import resources
from pathlib import Path

import numpy as np
from scipy.signal import resample_poly

from .dialogue import BACKEND_NAMES, FRAME_S, SILENCE_DBFS, SpeechDetector, SpeechResult, dilate_mask

BACKENDS = tuple(BACKEND_NAMES)  # the one list, kept in dialogue.py
VAD_FS = 16000
WINDOW = 512  # the model's frame at 16 kHz: 32 ms
CONTEXT = 64  # samples of the previous window the model wants in front of each input
THRESHOLD = 0.5  # the model's documented default
CHUNK_S = 10.0  # resample this much at a time: about 4 MB of float64 at 48 kHz, whatever the programme length
OVERLAP_S = 0.05  # native samples carried into the next chunk so the resampler's edge is clean


class VadUnavailable(RuntimeError):
    """onnxruntime or the model is missing; the message says what to install."""


def model_path() -> Path:
    override = os.environ.get("CUMPLE_SILERO_MODEL")
    if override:
        return Path(override)
    return Path(str(resources.files("cumple.models") / "silero_vad.onnx"))


def load_session():
    """An onnxruntime session on the bundled model, single-threaded and quiet."""
    try:
        import onnxruntime as ort
    except ImportError as e:
        raise VadUnavailable(
            "the silero backend needs onnxruntime: uv tool install --python 3.12 "
            '"cumple[vad] @ git+https://github.com/victor10days/cumple" (a checkout: uv sync --extra vad)'
        ) from e
    path = model_path()
    if not path.is_file():
        raise VadUnavailable(f"Silero VAD model not found at {path}")
    opts = ort.SessionOptions()
    opts.inter_op_num_threads = 1
    opts.intra_op_num_threads = 1
    opts.log_severity_level = 3
    return ort.InferenceSession(str(path), opts, providers=["CPUExecutionProvider"])


class SileroDetector:
    """Same feed and result as SpeechDetector; the levels come from one, the mask from the model."""

    def __init__(self, samplerate: int, channels: int, roles: list[str] | None = None, session=None):
        self.fs = int(samplerate)
        self._levels = SpeechDetector(samplerate, channels, roles=roles)
        self._session = session if session is not None else load_session()
        self._state = np.zeros((2, 1, 128), dtype=np.float32)
        self._context = np.zeros((1, CONTEXT), dtype=np.float32)
        self._sr = np.array(VAD_FS, dtype=np.int64)
        g = int(np.gcd(VAD_FS, self.fs))
        self._up, self._down = VAD_FS // g, self.fs // g
        self._chunk = int(self.fs * CHUNK_S)
        self._overlap = int(self.fs * OVERLAP_S)
        self._native = np.empty(0, dtype=np.float64)  # picked channel awaiting resampling
        self._tail = np.empty(0, dtype=np.float64)  # the end of the previous chunk, for the resampler
        self._pending = np.empty(0, dtype=np.float32)  # 16 kHz samples awaiting a full window
        self._probs: list[float] = []

    def feed(self, block: np.ndarray) -> None:
        self._levels.feed(block)
        x = self._levels.pick_channel(np.asarray(block, dtype=np.float64))
        self._native = np.concatenate([self._native, x]) if self._native.size else x
        while self._native.size >= self._chunk:
            self._resample(self._native[: self._chunk])
            self._native = self._native[self._chunk :]

    def _resample(self, x: np.ndarray) -> None:
        if self.fs == VAD_FS:
            y = x.astype(np.float32)
        else:
            joined = np.concatenate([self._tail, x])
            y = resample_poly(joined, self._up, self._down).astype(np.float32)
            skip = int(round(len(self._tail) * self._up / self._down))
            y = y[skip:]
            self._tail = x[-self._overlap :] if x.size >= self._overlap else x
        self._pending = np.concatenate([self._pending, y]) if self._pending.size else y
        n = len(self._pending) // WINDOW
        for i in range(n):
            self._infer(self._pending[i * WINDOW : (i + 1) * WINDOW])
        self._pending = self._pending[n * WINDOW :]

    def _infer(self, window: np.ndarray) -> None:
        inp = np.concatenate([self._context, window[None, :]], axis=1)
        out, self._state = self._session.run(None, {"input": inp, "state": self._state, "sr": self._sr})
        self._probs.append(float(out[0, 0]))
        self._context = inp[:, -CONTEXT:]

    def result(self) -> SpeechResult:
        if self._native.size:
            self._resample(self._native)
            self._native = np.empty(0, dtype=np.float64)
        base = self._levels.result()
        n20 = len(base.level_db)
        if n20 == 0:
            return SpeechResult(FRAME_S, base.mask, base.active, base.level_db, None, backend="silero")
        if not self._probs:
            voiced = np.zeros(n20, dtype=bool)
        else:
            probs = np.asarray(self._probs)
            idx = np.minimum(np.arange(n20) * round(FRAME_S * VAD_FS) // WINDOW, len(probs) - 1)  # 320 and 512, exact
            voiced = probs[idx] > THRESHOLD
        mask = dilate_mask(voiced)
        programme = (base.level_db > SILENCE_DBFS) | mask
        fraction = float(mask[programme].mean()) if programme.any() else 0.0
        return SpeechResult(FRAME_S, mask, base.active, base.level_db, fraction, backend="silero")
```

Note for the implementer: `resources.files("cumple.models")` needs `src/cumple/models/__init__.py` to exist (Step 1). Also add `"onnxruntime"` to the `excludes` list in `packaging/cumple.spec` (a local build from the dev venv would otherwise bundle a 20 MB runtime the frame keeps out of the frozen apps this iteration; the release job installs no dev group, so CI is unaffected). The 44.1 kHz test drives the `_tail` path; the 16 kHz fixture drives the `fs == VAD_FS` path.

- [ ] **Step 6: Run the tests, lint, build, the whole suite**

Run: `uv run pytest tests/test_vad.py tests/test_dialogue_leqm_acx.py tests/test_engine.py -v` (the heuristic's own tests must not move). Then `uv run ruff check src tests && uv run ruff format src tests`, then `uv build -q && unzip -l dist/cumple-*.whl | grep -E "silero_vad.onnx|SILERO_LICENSE"` (both must be in the wheel; if not, hatchling needs `[tool.hatch.build.targets.wheel] include` adjusted, report it). Then `uv run pytest` once; re-pin the counts.

- [ ] **Step 7: Commit**

```bash
git add src/cumple/meters/dialogue.py src/cumple/meters/vad.py src/cumple/models tests/fixtures tests/test_vad.py pyproject.toml uv.lock packaging/cumple.spec README.md CONTRIBUTING.md docs/QA.md AI_USAGE.md site/index.html
git commit -m "Add Silero VAD as a second speech detector behind the vad extra"
```

---

### Task 2: Choosing the backend, and saying which one made the mask

**Files:**
- Modify: `src/cumple/meters/measure.py` (`measure`, `measure_package`, `_run` gain `vad: str = "heuristic"`)
- Modify: `src/cumple/cli.py` (`check` gains `--vad`; `CUMPLE_VAD` env)
- Modify: `src/cumple/checks/engine.py` (three notes through `describe_backend`)
- Modify: `src/cumple/report/json_out.py` (`speech_backend`), `src/cumple/report/qc_sheet.py` (footer line)
- Test: `tests/test_vad.py` (append)

**Interfaces:**
- Consumes: `SileroDetector`, `VadUnavailable`, `BACKENDS` from `vad.py`; `describe_backend` from `dialogue.py`.
- Produces: `measure(path, ..., vad="heuristic")`; `check --vad {heuristic,silero}`; JSON `measurement.speech_backend`; notes containing `describe_backend(...)`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_vad.py` (add `from typer.testing import CliRunner`, `from cumple.checks.engine import evaluate`, `from cumple.cli import app`, `from cumple.meters.measure import measure`, `from cumple.report import render_html`, `from cumple.report.json_out import report_to_dict`, `from cumple.specs import load_all`, and `import json` to the top import block; `runner = CliRunner()` after `needs_onnx`):

```python
@pytest.fixture
def speech_wav(tmp_path):
    """The excerpt as a 48 kHz stereo WAV, eight seconds long, so the meters have enough programme."""
    from scipy.signal import resample_poly

    x16, _ = sf.read(str(FIXTURE), dtype="float64", always_2d=True)
    x48 = resample_poly(x16[:, 0], 3, 1)
    x48 = np.tile(x48, 3)[: 48000 * 8]
    path = tmp_path / "speech.wav"
    sf.write(str(path), np.repeat(x48[:, None], 2, axis=1), 48000, subtype="PCM_24")
    return path


def test_measure_defaults_to_the_heuristic_and_refuses_an_unknown_backend(speech_wav):
    m = measure(speech_wav)
    assert m.speech is not None and m.speech.backend == "heuristic"
    with pytest.raises(ValueError, match="heuristic, silero"):
        measure(speech_wav, vad="dolby")


@needs_onnx
def test_measure_with_silero_reports_the_backend_everywhere(speech_wav):
    profiles = load_all()
    m = measure(speech_wav, vad="silero")
    assert m.speech is not None and m.speech.backend == "silero"
    report = evaluate(profiles["netflix-2.0"], m)
    doc = report_to_dict(report)
    assert doc["measurement"]["speech_backend"] == "silero"
    notes = " ".join(f.note or "" for f in report.findings)
    assert "Silero VAD v6.2" in notes and "heuristic" not in notes
    html = render_html(report)
    assert "Silero VAD v6.2" in html and "heuristic speech" not in html


def test_the_heuristic_report_still_says_heuristic(speech_wav):
    profiles = load_all()
    report = evaluate(profiles["netflix-2.0"], measure(speech_wav))
    notes = " ".join(f.note or "" for f in report.findings)
    assert "heuristic speech gate" in notes and "Silero" not in notes
    assert report_to_dict(report)["measurement"]["speech_backend"] == "heuristic"
    assert "heuristic speech gate" in render_html(report)


@needs_onnx
def test_check_takes_vad_from_the_flag_and_from_the_environment(speech_wav, monkeypatch):
    result = runner.invoke(app, ["check", str(speech_wav), "--spec", "netflix-2.0", "--vad", "silero", "--json"])
    assert result.exit_code in (0, 1), result.output
    assert json.loads(result.output)["measurement"]["speech_backend"] == "silero"
    monkeypatch.setenv("CUMPLE_VAD", "silero")
    result = runner.invoke(app, ["check", str(speech_wav), "--spec", "netflix-2.0", "--json"])
    assert json.loads(result.output)["measurement"]["speech_backend"] == "silero"
    monkeypatch.delenv("CUMPLE_VAD")
    result = runner.invoke(app, ["check", str(speech_wav), "--spec", "netflix-2.0", "--json"])
    assert json.loads(result.output)["measurement"]["speech_backend"] == "heuristic"


def test_check_without_onnxruntime_exits_two_and_names_the_extra(speech_wav, monkeypatch):
    import cumple.meters.vad as vad_mod

    def refuse():
        raise VadUnavailable('the silero backend needs onnxruntime: uv tool install "cumple[vad] @ git+https://github.com/victor10days/cumple"')

    monkeypatch.setattr(vad_mod, "load_session", refuse)
    result = runner.invoke(app, ["check", str(speech_wav), "--spec", "netflix-2.0", "--vad", "silero"])
    assert result.exit_code == 2
    assert "cumple[vad]" in result.output


def test_check_refuses_an_unknown_vad_name(speech_wav):
    result = runner.invoke(app, ["check", str(speech_wav), "--spec", "netflix-2.0", "--vad", "dolby"])
    assert result.exit_code == 2 and "heuristic" in result.output and "silero" in result.output
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_vad.py -v -k "measure or check or heuristic_report"`
Expected: FAIL (`measure()` has no `vad`; `check` has no `--vad`; JSON has no `speech_backend`).

- [ ] **Step 3: Implement**

`src/cumple/meters/measure.py`:
- import `describe_backend` from `.dialogue`; `measure(...)` signature gains `vad: str = "heuristic",` after `lfe_corner_hz`; the docstring gains one line: `vad chooses the speech detector for dialogue-gated rules: "heuristic" (default) or "silero" (needs the vad extra).` It passes `vad=vad` to `measure_package(...)` and `_run(...)`.
- `measure_package(...)` gains the same parameter and passes it to `_run`.
- `_run(...)` gains `vad: str = "heuristic"` and replaces `speech = SpeechDetector(fs, channels, roles=roles)` with:

```python
    describe_backend(vad)  # raises ValueError naming the choices for anything unknown
    if vad == "silero":
        from .vad import SileroDetector  # onnxruntime is imported only when asked for

        speech = SileroDetector(fs, channels, roles=roles)
    else:
        speech = SpeechDetector(fs, channels, roles=roles)
```

`src/cumple/cli.py`, the `check` command: add after `out`:

```python
    vad: str | None = typer.Option(
        None,
        "--vad",
        help='Speech detector for dialogue-gated rules: "heuristic" (default) or "silero" (needs the vad extra). CUMPLE_VAD sets the default.',
    ),
```

and change `m = measure(path, **measure_args(profile))` to `m = measure(path, vad=vad or os.environ.get("CUMPLE_VAD", "heuristic"), **measure_args(profile))` (add `import os` to the imports). The surrounding `try` prints the exception and exits 2; check that a `ValueError` from an unknown name and a `VadUnavailable` both reach that branch (read the `except` clause; if it catches a narrower type, widen it to `Exception` the way the `fix` command does). Rich consumes `[vad]` as a style tag, so that `console.print` must pass the message through `rich.markup.escape` (`from rich.markup import escape`; `console.print(f"[red]cannot measure {path}:[/] {escape(str(e))}")`), the way the `app` command escapes its own `cumple\\[app]` hint (cli.py around line 479); do the same for any other `console.print` in `check` that interpolates an exception.

`src/cumple/checks/engine.py`: import `describe_backend` from `..meters.dialogue`; add near the top of `evaluate` (after `m` is bound) `gate = describe_backend(m.speech.backend if m.speech is not None else "heuristic")`; then:
- the speech-share INFO note (around line 130): `note=f"{gate}, an approximation of Dolby Dialogue Intelligence",`
- the dialogue-gated note (around line 149): `note = f"approximation of Dialogue Intelligence: {gate}, {m.loudness.dialogue_blocks} speech blocks, BS.1770-1 (no relative gate)"`
- the false-pass WARN (around line 229): `f"the {gate} reads low on dense mixes (docs/DIALOGUE.md), so this pass "`
Grep the file for any other "heuristic" and route it through `gate` the same way.

`src/cumple/report/json_out.py`: after `"speech_fraction": _num(m.speech_fraction),` add `"speech_backend": m.speech.backend if m.speech is not None else "heuristic",`.

`src/cumple/report/qc_sheet.py`: import `describe_backend`; the footer sentence `Dialogue-gated rules use a heuristic speech detector, an approximation of Dolby Dialogue Intelligence, and say so above.` becomes `Dialogue-gated rules use the {gate}, an approximation of Dolby Dialogue Intelligence, and say so above.` with `gate = describe_backend(m.speech.backend if m.speech is not None else "heuristic")` computed beside the other footer values (the sentence is inside an f-string or a `.format`; read how the footer is built and follow it).

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_vad.py tests/test_engine.py tests/test_cli_edges.py tests/test_qc_sheet.py tests/test_app.py -v`, then ruff, then `uv run pytest` once; re-pin the counts.

- [ ] **Step 5: Commit**

```bash
git add src/cumple/meters/measure.py src/cumple/cli.py src/cumple/checks/engine.py src/cumple/report/json_out.py src/cumple/report/qc_sheet.py tests/test_vad.py README.md CONTRIBUTING.md docs/QA.md AI_USAGE.md site/index.html
git commit -m "Let check choose the speech detector, and name it in every report"
```

---

### Task 3: One implementation in the benchmark, the measurement, the docs

**Files:**
- Modify: `scripts/dialogue_benchmark.py` (use `SileroDetector` and `dilate_mask`; drop its own inference and the 16 kHz intermediates)
- Regenerate: `docs/DIALOGUE.md`
- Modify: `README.md` (the `check` section gains the `--vad` paragraph; the dialogue bullet in Honest limits gains Silero's measured sentence; the install line mentions the extra), `CONTRIBUTING.md` (extras), `site/index.html` (the dialogue note near line 340 and the honest-limits list item that mention the heuristic, if any; the JSON-LD twin rule applies only to FAQ answers), `AI_USAGE.md` (new section), `docs/ROADMAP.md` (R1 status `building`)
- Test: existing `tests/test_site_numbers.py` (derives the dialogue errors from DIALOGUE.md), `tests/test_site.py`, `tests/test_counts.py`

- [ ] **Step 1: The script uses the detector**

In `scripts/dialogue_benchmark.py`:
- Replace the `try: import onnxruntime ... ort = None` block, `SILERO_MODEL`, `SILERO_CHUNK, SILERO_CONTEXT, SILERO_THRESHOLD`, `silero_available()`, `vad_mask()`, `dilate()` and the `mono16k` intermediate (the `-ar 16000` ffmpeg step around line 127 and its callers) with:

```python
from cumple.io.reader import iter_blocks, probe
from cumple.meters.dialogue import dilate_mask
from cumple.meters.vad import THRESHOLD as SILERO_THRESHOLD
from cumple.meters.vad import SileroDetector, VadUnavailable, load_session


_SESSION = None  # one onnxruntime session for the whole run


def silero_available() -> bool:
    global _SESSION
    if _SESSION is None:
        try:
            _SESSION = load_session()
        except VadUnavailable:
            return False
    return True


def vad_mask(path: Path) -> np.ndarray | None:
    """Silero VAD decisions on the detector's 20 ms grid, from the same detector `check --vad silero` runs."""
    if not silero_available():
        return None
    info = probe(path)
    det = SileroDetector(info.samplerate, info.channels, roles=default_roles(info.channels), session=_SESSION)
    for block in iter_blocks(path, info=info):
        det.feed(block)
    return det.result().mask
```

Every `dilate(...)` call becomes `dilate_mask(...)`; every `vad_mask(mono16k(...))` becomes `vad_mask(path)` with the file's own path. The sentence at line 491 becomes `f"Silero VAD, the detector behind check --vad silero (threshold {SILERO_THRESHOLD}), is shown beside the heuristic."` and the `else` branch `"Silero VAD was not available (onnxruntime missing), so its columns read n/a."`. Keep everything else. Run `uv run ruff check scripts && uv run ruff format scripts`.

- [ ] **Step 2: Regenerate DIALOGUE.md**

Run, in the foreground: `uv run python scripts/dialogue_benchmark.py` (it writes `docs/DIALOGUE.md`; the previous run took under ten minutes on this machine; if the tool's ten-minute cap is hit, report BLOCKED with how far it got and the controller runs it). Then `git diff docs/DIALOGUE.md`: the heuristic's numbers must be identical to the committed ones (the detector did not change); the Silero columns may move by rounding at most; the header date and the sentence about Silero change. If a heuristic number moved, stop and report.

- [ ] **Step 3: README, CONTRIBUTING, page, AI_USAGE, ROADMAP**

README, the `check` section (around line 110): after the paragraph that introduces the command, add:

```markdown
`--vad silero` (or `CUMPLE_VAD=silero`) swaps the heuristic speech detector for
Silero VAD v6.2 (Silero Team, MIT), a small neural voice-activity model that ships
with cumple and runs offline through onnxruntime: install with
`uv tool install --python 3.12 "cumple[vad] @ git+https://github.com/victor10days/cumple"`.
Only `check` takes the flag; `watch` and the desktop app keep the heuristic.
Every report names which detector made the mask. Neither is Dolby's algorithm;
[docs/DIALOGUE.md](docs/DIALOGUE.md) measures both on the same films.
```

README, Honest limits, the dialogue bullet: after `Silero VAD, the standard open voice detector, is more precise and no better on the quiet dialogue.` replace that sentence with the measured one, taking the numbers from the regenerated DIALOGUE.md (the Silero speech shares on the M&E versions, its dialogue-gated error on Tears of Steel and on Sintel), for example: `Silero VAD, available as \`--vad silero\`, reads 0 % speech on the music-and-effects versions and comes within X LU on Tears of Steel, but misses Sintel's quiet dialogue under music by about Y LU.` with X and Y from the report, not from memory; and where the sentence compares them, say it plainly: on Sintel Silero is worse than the heuristic (the report's two deltas, one decimal each). Then extend `tests/test_site_numbers.py::test_dialogue_gate_errors_in_the_note` (the one test the loop's boundary lets grow, it already parses DIALOGUE.md) to also derive Silero's two deltas from the pair table (header row starting `| programme | integrated (BS.1770-4) |`): parse the leading number of the `Silero-gated` cell and of the `dialogue-gated: reference` cell (both cells may carry a block count in parentheses; take the first float), delta = Silero minus reference, and assert README's Silero sentence carries `abs(delta)` for each film at one decimal as `X.X LU` (README says how far under the reference Silero reads, so the sign is dropped).

README install section (the `uv tool install` line, around line 25): add one sentence naming the extra: `add \`[vad]\` for the Silero speech detector.`

CONTRIBUTING.md: where `uv sync --group dev` is explained, add that the dev group carries onnxruntime so the Silero tests run.

`site/index.html`: the note near line 340 ("The dialogue gate is a labelled approximation of Dolby's algorithm ...") gains one sentence at its end: `A second detector, Silero VAD, is one flag away and is measured in the same report.` (keep the derived figures untouched; `tests/test_site_numbers.py` pins them). If the honest-limits list item about the dialogue gate exists, leave it unless it says something now false.

`AI_USAGE.md`: append

```markdown
## A second speech detector (13 September)

The roadmap's first item by the landscape's count. Silero VAD had been a
second opinion inside the benchmark script since 5 September; now it is a
detector cumple can run, behind an extra, with the model bundled under its
MIT licence and the same 20 ms grid and dilation rule as the heuristic, so
the meter cannot tell them apart except by name, and every report says the
name. The benchmark script runs the same detector instead of its own copy of
the inference, so there is one implementation to be wrong. The default did
not change: the heuristic installs in seconds and is measured; Silero is
more precise on clean speech and worse on quiet dialogue under music,
and the README carries both numbers from the same run. On Sintel, whose
dialogue sits under an orchestral score, Silero reads further under the
reference than the heuristic does; the README says by how much.
```

`docs/ROADMAP.md`: R1 status `building` (the main session sets `merged` with the PR number at the receipt).

- [ ] **Step 4: Tests, counts, dashes, commit**

Run `uv run pytest` once (the site-numbers tests re-derive the dialogue figures from the regenerated DIALOGUE.md; if one fails it names the page cell, update it to the true value and say so), ruff, re-pin counts, `grep -n '[—–]' README.md CONTRIBUTING.md site/index.html AI_USAGE.md docs/ROADMAP.md docs/DIALOGUE.md scripts/dialogue_benchmark.py` (DIALOGUE.md is generated; if the generator prints a dash, report it).

```bash
git add scripts/dialogue_benchmark.py docs/DIALOGUE.md README.md CONTRIBUTING.md site/index.html AI_USAGE.md docs/ROADMAP.md docs/QA.md
git commit -m "Run the benchmark through the shipped detector, and say what Silero measures"
```
