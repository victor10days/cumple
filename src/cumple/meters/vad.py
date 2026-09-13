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
