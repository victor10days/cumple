from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import soundfile as sf


@pytest.fixture
def make_wav(tmp_path: Path):
    """Write a sine WAV and return its path. Amplitude is linear (1.0 = full scale)."""

    def _make(
        name: str = "tone.wav",
        sr: int = 48000,
        channels: int = 2,
        seconds: float = 1.0,
        freq: float = 1000.0,
        amplitude: float = 0.5,
        subtype: str = "PCM_24",
    ) -> Path:
        n = int(round(sr * seconds))
        t = np.arange(n) / sr
        tone = amplitude * np.sin(2 * np.pi * freq * t)
        data = np.repeat(tone[:, None], channels, axis=1)
        path = tmp_path / name
        sf.write(str(path), data, sr, subtype=subtype)
        return path

    return _make
