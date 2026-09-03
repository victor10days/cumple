"""Programme loudness per ITU-R BS.1770 and EBU Tech 3341/3342.

The meter is streaming: feed it blocks of any size and ask for the result at the end.
It keeps only 100 ms energies, so a two-hour file costs a few hundred kilobytes.

Numbers you can check against the standard:
- K-weighting = a high shelf (+4 dB above about 1.7 kHz) followed by a high-pass at
  about 38 Hz. BS.1770 prints the coefficients for 48 kHz only; here they are derived
  from the filter design parameters so any sample rate works, and a test asserts the
  48 kHz result matches the printed table.
- Loudness of a block = -0.691 + 10 log10(sum_i G_i z_i), z_i the mean square of the
  K-weighted channel i, G_i = 1 for L/R/C, 1.41 (+1.5 dB) for surrounds, 0 for LFE.
- Momentary = 400 ms blocks, 75 % overlap (100 ms hop). Short-term = 3 s.
- Integrated = mean over blocks that pass an absolute gate at -70 LKFS and, from
  BS.1770-2 on, a relative gate 10 LU below the absolute-gated mean. BS.1770-1 has no
  relative gate, which is why Netflix cites it for dialogue-gated measurement.
- Loudness range (Tech 3342) = 95th minus 10th percentile of short-term values after
  an absolute gate at -70 and a relative gate 20 LU below their mean.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.signal import lfilter

ABSOLUTE_GATE_LKFS = -70.0
RELATIVE_GATE_LU = -10.0
LRA_RELATIVE_GATE_LU = -20.0
LOUDNESS_OFFSET = -0.691
HOP_S = 0.1
MOMENTARY_HOPS = 4  # 400 ms
SHORT_TERM_HOPS = 30  # 3 s

# Design parameters behind the printed 48 kHz coefficients (pre-filter and RLB filter).
_SHELF_F0 = 1681.974450955533
_SHELF_GAIN_DB = 3.999843853973347
_SHELF_Q = 0.7071752369554196
_HIGHPASS_F0 = 38.13547087602444
_HIGHPASS_Q = 0.5003270373238773

# The coefficients as printed in BS.1770 for 48 kHz, used by the tests.
BS1770_48K_SHELF = dict(b0=1.53512485958697, b1=-2.69169618940638, b2=1.19839281085285, a1=-1.69065929318241, a2=0.73248077421585)
BS1770_48K_HIGHPASS = dict(b0=1.0, b1=-2.0, b2=1.0, a1=-1.99004745483398, a2=0.99007225036621)

# Channel weights G_i by role. Surrounds get +1.5 dB; LFE is excluded.
ROLE_WEIGHT: dict[str, float] = {
    "L": 1.0, "R": 1.0, "C": 1.0, "M": 1.0, "Lt": 1.0, "Rt": 1.0, "Lc": 1.0, "Rc": 1.0,
    "LFE": 0.0,
    "Ls": 1.41, "Rs": 1.41, "Lss": 1.41, "Rss": 1.41, "Lrs": 1.41, "Rrs": 1.41,
}


def default_roles(channels: int) -> list[str]:
    """Channel roles assumed from the channel count alone (SMPTE order for 5.1 and 7.1)."""
    table = {
        1: ["M"],
        2: ["L", "R"],
        3: ["L", "R", "C"],
        4: ["L", "R", "Ls", "Rs"],
        5: ["L", "R", "C", "Ls", "Rs"],
        6: ["L", "R", "C", "LFE", "Ls", "Rs"],
        8: ["L", "R", "C", "LFE", "Ls", "Rs", "Lrs", "Rrs"],
    }
    return table.get(channels, ["L"] * channels)


def channel_weights(channels: int, roles: list[str] | None = None) -> np.ndarray:
    roles = roles or default_roles(channels)
    if len(roles) != channels:
        raise ValueError(f"{len(roles)} roles for {channels} channels")
    return np.array([ROLE_WEIGHT.get(r, 1.0) for r in roles], dtype=np.float64)


def _high_shelf(fs: float, f0: float, gain_db: float, q: float) -> tuple[np.ndarray, np.ndarray]:
    """Pre-filter (high shelf). Bilinear form that reproduces the printed 48 kHz table exactly.

    The exponent on Vb is the one that makes the printed coefficients come out; it is
    not a typo. See B. De Man, "Evaluation of implementations of the EBU R128 loudness
    measurement", AES 145 (2018).
    """
    k = np.tan(np.pi * f0 / fs)
    vh = 10 ** (gain_db / 20)
    vb = vh ** 0.4996667741545416
    a0 = 1 + k / q + k * k
    b = np.array([(vh + vb * k / q + k * k) / a0, 2 * (k * k - vh) / a0, (vh - vb * k / q + k * k) / a0])
    a = np.array([1.0, 2 * (k * k - 1) / a0, (1 - k / q + k * k) / a0])
    return b, a


def _high_pass(fs: float, f0: float, q: float) -> tuple[np.ndarray, np.ndarray]:
    """RLB filter (high pass). BS.1770 prints b = [1, -2, 1] unnormalised, so do the same."""
    k = np.tan(np.pi * f0 / fs)
    a0 = 1 + k / q + k * k
    b = np.array([1.0, -2.0, 1.0])
    a = np.array([1.0, 2 * (k * k - 1) / a0, (1 - k / q + k * k) / a0])
    return b, a


def k_weighting(fs: float) -> list[tuple[np.ndarray, np.ndarray]]:
    """The two K-weighting stages as (b, a) pairs for this sample rate."""
    return [
        _high_shelf(fs, _SHELF_F0, _SHELF_GAIN_DB, _SHELF_Q),
        _high_pass(fs, _HIGHPASS_F0, _HIGHPASS_Q),
    ]


def loudness_from_energy(weighted_energy: np.ndarray | float) -> np.ndarray | float:
    """-0.691 + 10 log10(energy), with -inf for zero energy instead of a warning."""
    e = np.asarray(weighted_energy, dtype=np.float64)
    with np.errstate(divide="ignore"):
        out = LOUDNESS_OFFSET + 10.0 * np.log10(np.where(e > 0, e, np.nan))
    out = np.where(np.isnan(out), -np.inf, out)
    return float(out) if out.ndim == 0 else out


@dataclass
class LoudnessResult:
    integrated: float  # LUFS/LKFS, -inf if nothing passed the gates
    momentary_max: float
    short_term_max: float
    lra: float  # LU
    momentary: np.ndarray = field(repr=False)  # one value per 100 ms hop, block ends at t
    short_term: np.ndarray = field(repr=False)
    hop_s: float = HOP_S
    relative_gate: bool = True
    blocks_total: int = 0
    blocks_gated: int = 0  # blocks that counted toward the integrated value
    duration_s: float = 0.0

    def momentary_times(self) -> np.ndarray:
        return (np.arange(len(self.momentary)) + MOMENTARY_HOPS) * self.hop_s

    def short_term_times(self) -> np.ndarray:
        return (np.arange(len(self.short_term)) + SHORT_TERM_HOPS) * self.hop_s


class LoudnessMeter:
    """Streaming BS.1770 meter. feed() blocks of shape (frames, channels), then result()."""

    def __init__(
        self,
        samplerate: int,
        channels: int,
        roles: list[str] | None = None,
        weights: np.ndarray | None = None,
        relative_gate: bool = True,
    ):
        self.fs = int(samplerate)
        self.channels = int(channels)
        self.weights = np.asarray(weights, dtype=np.float64) if weights is not None else channel_weights(channels, roles)
        self.relative_gate = relative_gate
        self.hop = int(round(self.fs * HOP_S))
        self._stages = k_weighting(self.fs)
        self._zi = [np.zeros((2, self.channels)) for _ in self._stages]
        self._pending = np.empty((0, self.channels))
        self._hop_energy: list[np.ndarray] = []  # mean square per channel, per hop
        self._frames = 0

    def feed(self, block: np.ndarray) -> None:
        x = np.asarray(block, dtype=np.float64)
        if x.ndim == 1:
            x = x[:, None]
        if x.shape[1] != self.channels:
            raise ValueError(f"expected {self.channels} channels, got {x.shape[1]}")
        self._frames += x.shape[0]
        for i, (b, a) in enumerate(self._stages):
            x, self._zi[i] = lfilter(b, a, x, axis=0, zi=self._zi[i])
        x = np.concatenate([self._pending, x]) if self._pending.size else x
        n_hops = x.shape[0] // self.hop
        if n_hops:
            whole = x[: n_hops * self.hop].reshape(n_hops, self.hop, self.channels)
            self._hop_energy.extend(np.mean(whole * whole, axis=1))
        self._pending = x[n_hops * self.hop :]

    # ----- derived quantities -----

    def _hop_energies(self) -> np.ndarray:
        if not self._hop_energy:
            return np.empty((0, self.channels))
        return np.vstack(self._hop_energy)

    def _windowed(self, hops: int) -> np.ndarray:
        """Weighted energy of every window of `hops` consecutive hops (sliding by one hop)."""
        e = self._hop_energies() @ self.weights
        if len(e) < hops:
            return np.empty(0)
        c = np.concatenate([[0.0], np.cumsum(e)])
        return (c[hops:] - c[:-hops]) / hops

    def momentary_energies(self) -> np.ndarray:
        return self._windowed(MOMENTARY_HOPS)

    def short_term_energies(self) -> np.ndarray:
        return self._windowed(SHORT_TERM_HOPS)

    def integrated(self) -> tuple[float, int, int]:
        """(integrated loudness, blocks total, blocks that passed the gates)."""
        energies = self.momentary_energies()
        if energies.size == 0:
            return -np.inf, 0, 0
        levels = loudness_from_energy(energies)
        keep = levels > ABSOLUTE_GATE_LKFS
        if not keep.any():
            return -np.inf, len(energies), 0
        if self.relative_gate:
            threshold = loudness_from_energy(energies[keep].mean()) + RELATIVE_GATE_LU
            keep &= levels > threshold
            if not keep.any():
                return -np.inf, len(energies), 0
        return loudness_from_energy(energies[keep].mean()), len(energies), int(keep.sum())

    def loudness_range(self) -> float:
        """EBU Tech 3342: percentiles of the gated short-term distribution."""
        energies = self.short_term_energies()
        if energies.size == 0:
            return 0.0
        levels = loudness_from_energy(energies)
        keep = levels > ABSOLUTE_GATE_LKFS
        if not keep.any():
            return 0.0
        threshold = loudness_from_energy(energies[keep].mean()) + LRA_RELATIVE_GATE_LU
        keep &= levels > threshold
        kept = np.sort(levels[keep])
        if kept.size < 2:
            return 0.0
        lo, hi = np.percentile(kept, [10, 95])
        return float(hi - lo)

    def result(self) -> LoudnessResult:
        momentary = loudness_from_energy(self.momentary_energies())
        short_term = loudness_from_energy(self.short_term_energies())
        integrated, total, gated = self.integrated()
        return LoudnessResult(
            integrated=float(integrated),
            momentary_max=float(momentary.max()) if momentary.size else -np.inf,
            short_term_max=float(short_term.max()) if short_term.size else -np.inf,
            lra=self.loudness_range(),
            momentary=np.asarray(momentary),
            short_term=np.asarray(short_term),
            hop_s=self.hop / self.fs,
            relative_gate=self.relative_gate,
            blocks_total=total,
            blocks_gated=gated,
            duration_s=self._frames / self.fs,
        )
