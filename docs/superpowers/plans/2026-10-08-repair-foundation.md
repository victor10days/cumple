# Repair foundation (build 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Two plan skeptics have read this plan (`docs/graph-runs/2026-10-08-rx-parity-landscape/03b-plan-skeptic.md`, `03c-plan-skeptic-second-read.md`); this is the version amended from their findings on 2026-10-08.

**Goal:** `cumple repair <file> --chain "declick(),declip()" --out <copy>` writes a repaired PCM copy through a Rust core ported from cathar, with a sidecar receipt, and `docs/REPAIR.md` scores De-click and De-clip against ffmpeg and cathar on synthetic damage with a held clean reference, with RX 8 columns that read "not run" until Victor's Batch Processing outputs land.

**Architecture:** A Cargo workspace at the repository root with `crates/cumple-dsp` (pure Rust: streaming STFT on realfft, a module trait with `context_frames`, `latency_frames`, `process`, `flush`, `report`, and the De-click, Interpolate and De-clip ports) and `crates/cumple-dsp-py` (PyO3 abi3 bindings, maturin, distribution `cumple-dsp`, import `cumple_dsp`), behind the extra `cumple[repair]`. `src/cumple/repair/` holds pydantic parameters, chain parsing, the streaming runner on `iter_blocks`, the receipt and the metrics. `cli.py` gains `repair`. The harness is `scripts/make_repair_set.py`, `scripts/benchmark_repair.py`, `docs/REPAIR.md`, `docs/repair/rx8-recipe.md` and `tests/test_repair_numbers.py`. No meter, check, profile or report changes.

**Tech Stack:** Rust stable (edition 2024, `rust-version` 1.87, as cathar), `rustfft` 6, `realfft` 3, `pyo3` and `numpy` crates at their current releases pinned by `Cargo.lock` (pyo3 0.29 at the time of writing: the GIL release call is `py.detach`), maturin 1.9.4 or newer, `cargo-deny`; Python 3.12, numpy, scipy (`ShortTimeFFT` as the oracle), soundfile, pydantic, pyyaml, typer; the ffmpeg on the machine (`adeclick`, `adeclip`; 9.0.1 on Victor's Mac, 6.1.1 on the Ubuntu runner, none on the other two, version printed where it runs) and a cathar CLI built at commit `f2c2842f89084589d069e5a8a0b61311aa70d928` (it writes 32-bit float WAV) as subprocess baselines.

**Spec:** `docs/superpowers/specs/2026-10-08-repair-foundation-design.md` (amended). Research: `docs/graph-runs/2026-10-08-rx-parity-landscape/`.

## Global Constraints

- The base install does not change: `pyproject.toml` `dependencies` stay as they are; the new extra is `repair = ["cumple-dsp"]` with `[tool.uv.workspace]` and `[tool.uv.sources]` wiring; the dev group does not carry the extension, so `uv sync` works without Rust. CI syncs `--extra repair` after `dtolnay/rust-toolchain@stable` and `Swatinem/rust-cache@v2`.
- uv does not rebuild a workspace member when its Rust sources change. After every edit to a `.rs` file or a `Cargo.toml`, run `uv sync --extra repair --reinstall-package cumple-dsp` before any `uv run pytest`; the member's `tool.uv.cache-keys` (Task 2) is meant to make that automatic, and Task 2 verifies it with a deliberate edit before the constraint is relaxed. A mutation check that does not first rebuild proves nothing.
- Every test that needs the core uses `needs_core = pytest.mark.skipif(importlib.util.find_spec("cumple_dsp") is None, reason="cumple-dsp is not built; uv sync --extra repair")`; nothing in the suite requires Rust. Tests that need ffmpeg skip as `test_ffmpeg_io.py` does; tests that need the cathar binary skip unless `find_cathar()` finds it (`CUMPLE_CATHAR` or PATH); CI's Linux runner builds cathar (Task 2) so the fidelity tests run there.
- Ported Rust carries, at the top of each file, `// Ported from cathar (github.com/vbasky/cathar) <path> at commit f2c2842f, MIT OR Apache-2.0, used under MIT; see crates/cumple-dsp/THIRD_PARTY.md.` No GPL or AGPL source is read while porting (Audacity, GWC, IPOL, the survey's MATLAB).
- f64 throughout the core; numpy arrays are `float64`, shape `(frames, channels)`, C order; a block never exceeds `DEFAULT_BLOCK_FRAMES + 2 * context_frames`.
- Writes follow `fix.apply` and `fix_file`: same subtype and format, a temporary name beside the destination (`.<name>.cumple-tmp`), `os.replace`, refuse `dst.resolve() == src.resolve()`, refuse a directory, refuse a file ffmpeg decoded. The receipt is written after the copy is in place.
- The phrase "not checked" never appears; tables say "not run" with a reason. No em or en dash in prose, comments, docstrings, YAML or Rust doc comments.
- `uv run ruff check src tests scripts && uv run ruff format --check src tests scripts`, `cargo fmt --all -- --check`, `cargo clippy --workspace --all-targets -- -D warnings`, `cargo test -p cumple-dsp`, `cargo deny check licenses` clean before each commit. `uv run pytest` alone, never piped, in full before each commit; re-pin the five documented counts (README `**Tests**: N,` and `runs N-29 of them on Ubuntu`, CONTRIBUTING `# N tests;`, docs/QA.md `` `uv run pytest`, N tests``, AI_USAGE `N tests, including`, site/index.html `N tests with 91 %`) from `uv run pytest --collect-only 2>/dev/null | grep 'tests collected'`. README's "19 fewer on macOS" counts the items gated on ffmpeg (there is no ffmpeg on the macOS and Windows runners) and "20 fewer on Windows" adds the one `win32` skip; a test gated on ffmpeg and the core counts once; the cathar-gated tests run on Linux and skip on macOS and Windows, so they count like the ffmpeg-gated ones. Each task below says what it adds.
- Commit after every task: one plain imperative sentence, a blank line, then the attribution lines the session reminder gives. No model identifier anywhere else in the repository.
- Work on the branch the executing session names; never `cd` to Victor's main checkout; never push to main. A Rust toolchain on the executing machine is a precondition (Victor installed rustup on his Mac on 2026-10-08; a cloud session installs it in the setup step).

---

### Task 1: The harness first: damage, metrics, the ffmpeg and cathar baselines

The first measured number arrives before any new DSP is written (receipt ruling). Nothing here imports the core.

**Files:**
- Create: `src/cumple/repair/__init__.py` (only `available()`, `require()`, `RepairUnavailable` for now), `src/cumple/repair/metrics.py`, `src/cumple/repair/damage.py`, `scripts/make_repair_set.py`, `scripts/benchmark_repair.py`, `docs/repair/rx8-recipe.md`, `docs/REPAIR.md` (first version: baselines only; the cumple columns read "not run: build 1 Task 5")
- Test: `tests/test_repair_metrics.py`, `tests/test_repair_baselines.py`

**Interfaces:**
- Consumes: `cumple.io.reader.read`, `cumple.io.ffmpeg.find_ffmpeg`, `tests/fixtures/speech-librivox-3s.wav` (48,000 samples at 16 kHz, peak 0.232, RMS 0.041).
- Produces: `metrics.sdr_db(ref, est) -> float`; `metrics.delta_sdr(ref, damaged, est, mask=None) -> float`; `metrics.residual_clicks(ref, est, positions, widths, threshold, window=64) -> tuple[int, int]` (missed, false); `metrics.peak_error_db(ref, est, mask) -> float`; `damage.clip_to_sdr(x, target_sdr_db) -> tuple[np.ndarray, float, np.ndarray]` (clipped, threshold as the float32 repr of the stored value, mask); `damage.add_clicks(x, samplerate, seed, per_minute, widths, gains) -> tuple[np.ndarray, list[Click], np.ndarray]` with two presets `IMPULSE = dict(widths=(1, 8), gains=(8, 16))` and `BURST = dict(widths=(9, 64), gains=(8, 16))`; `damage.dilate(mask, n)`; `damage.Manifest` (pydantic, `extra="forbid"`: references with SHA-256, damaged files with SHA-256, per-file threshold or click list, seed, and for the RX input folder the scale per file); `benchmark_repair.run_ffmpeg(tools, src, dst, filter)`, `benchmark_repair.run_cathar(binary, src, dst, module, threshold)`, `benchmark_repair.find_cathar() -> Path | None`.

- [ ] **Step 1: Pin the survey's levels and names from the right sources**

The survey repository's README (`rajmic/declipping2020_codes`, GPL, read only, never cloned) names neither the levels nor the excerpts. The seven input-SDR levels (1, 3, 5, 7, 10, 15, 20 dB) come from the paper (Záviška, Rajmic, Ozerov, Rencker, "A survey and an extensive evaluation of popular audio declipping methods", IEEE JSTSP 2021, open access) and its companion page `rajmic.github.io/declipping2020`; the ten SQAM tracks are the file names in the repository's `Sounds` folder (a08 violin, a16 clarinet, a18 bassoon, a25 harp, a35 glockenspiel, a41 celesta, a42 accordion, a58 guitar, a60 piano, a66 wind ensemble). Record both in `scripts/make_repair_set.py`'s docstring with the read date. The SQAM set itself is already fetched by `scripts/fetch_real_dialogue.sh` (line 49, under the EBU terms its line 12 records: research use only); nothing new is downloaded and nothing is committed.

- [ ] **Step 2: Write the failing metric and damage tests**

```python
"""Metrics and synthetic damage with known answers; nothing here needs the Rust core."""

from __future__ import annotations

import numpy as np

from cumple.repair import damage, metrics

FS = 48000


def tone(seconds=120.0, hz=440.0):
    t = np.arange(int(seconds * FS)) / FS
    return 0.5 * np.sin(2 * np.pi * hz * t)


def test_sdr_of_a_perfect_estimate_is_infinite_and_of_half_gain_is_six_db():
    x = tone(2.0)
    assert metrics.sdr_db(x, x) == np.inf
    assert abs(metrics.sdr_db(x, 0.5 * x) - 6.02) < 0.01


def test_clip_to_sdr_lands_within_a_tenth_of_a_db_and_returns_the_mask():
    x = tone(2.0)
    y, thr, mask = damage.clip_to_sdr(x, 5.0)
    assert abs(metrics.sdr_db(x, y) - 5.0) < 0.1
    assert mask.dtype == bool and mask.sum() > 0
    assert np.all(np.abs(y[mask]) == thr) and np.all(y[~mask] == x[~mask])
    assert np.float32(thr) == thr  # the manifest stores the float32 repr so |v| >= thr holds on the stored samples


def test_add_clicks_is_seeded_and_only_touches_the_mask():
    x = tone(120.0)  # two minutes at 40 per minute: 80 clicks
    y1, clicks1, mask1 = damage.add_clicks(x, FS, seed=7, per_minute=40, **damage.IMPULSE)
    y2, clicks2, mask2 = damage.add_clicks(x, FS, seed=7, per_minute=40, **damage.IMPULSE)
    assert clicks1 == clicks2 and np.array_equal(y1, y2)
    assert np.all(y1[~mask1] == x[~mask1]) and len(clicks1) == 80
    assert all(1 <= c.width <= 8 for c in clicks1)


def test_impulse_clicks_are_visible_to_the_local_rms_detector():
    """cathar's detector cannot exceed sqrt(window) = 8 at window 64; the IMPULSE preset must sit under it."""
    x = tone(10.0)
    y, clicks, _ = damage.add_clicks(x, FS, seed=1, per_minute=60, **damage.IMPULSE)
    ratios = metrics.local_rms_ratio(y, window=64)
    assert all(ratios[c.position] > 5.0 for c in clicks)  # the detector of record runs at threshold 5


def test_delta_sdr_on_damaged_samples_only_ignores_the_rest():
    x = tone(2.0)
    y, _, mask = damage.clip_to_sdr(x, 3.0)
    assert metrics.delta_sdr(x, y, x, mask=mask) == np.inf
    assert metrics.delta_sdr(x, y, y, mask=mask) == 0.0


def test_residual_clicks_counts_missed_and_false():
    x = tone(10.0)
    y, clicks, _ = damage.add_clicks(x, FS, seed=1, per_minute=60, **damage.IMPULSE)
    pos, wid = [c.position for c in clicks], [c.width for c in clicks]
    missed, false = metrics.residual_clicks(x, y, pos, wid, threshold=5.0)
    assert missed == len(clicks) and false == 0
    missed, false = metrics.residual_clicks(x, x, pos, wid, threshold=5.0)
    assert missed == 0 and false == 0
```

`metrics.local_rms_ratio` is cathar's `local_rms` in numpy (the window of sample `i` is samples `i - 32` to `i + 31`, including `i`) divided into `|x|`; it is the detector the harness uses for residual counting and the one the IMPULSE preset is tuned against. If `test_impulse_clicks_are_visible_to_the_local_rms_detector` fails for a width in the preset, narrow the preset, never the assertion: the preset exists so the detector of record can see every click in the De-click table.

- [ ] **Step 3: Implement `metrics.py` and `damage.py`**

`sdr_db = 10 log10(sum(ref^2) / sum((ref - est)^2))`, `inf` when the residual energy is 0. `clip_to_sdr` bisects the threshold on `[0, max|x|]` until the SDR is within 0.05 dB of the target (at most 60 steps), rounds the threshold to float32, then returns the hard-clipped signal, the threshold and `|x| >= thr`. `add_clicks` draws positions from `numpy.random.default_rng(seed)` at `per_minute * seconds` positions at least 2,048 samples apart, widths uniform in `widths`, each click a half-cosine burst of `gain * local_rms` (local RMS over 64 samples) added with a random sign; returns the list of `Click(position, width, gain)` and the boolean mask. `residual_clicks` runs `local_rms_ratio` on the estimate at `threshold` and counts injected clicks still detected (missed) and detections outside the dilated click mask (false). `peak_error_db` is `20 log10(max|est[mask]| / max|ref[mask]|)`.

- [ ] **Step 4: Write the failing baseline tests**

```python
"""ffmpeg and cathar as subprocess baselines: when they are on the machine, they repair; when not, nothing here runs."""

from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from cumple.io.ffmpeg import find_ffmpeg
from cumple.repair import damage, metrics
from scripts.benchmark_repair import find_cathar, run_cathar, run_ffmpeg  # the repository root is on sys.path under pytest's prepend mode; scripts/ resolves as a namespace package

TOOLS = find_ffmpeg()
CATHAR = find_cathar()
needs_ffmpeg = pytest.mark.skipif(TOOLS is None, reason="ffmpeg is not on PATH")
needs_cathar = pytest.mark.skipif(CATHAR is None, reason="cathar is not on PATH and CUMPLE_CATHAR is unset")
FIXTURE = Path(__file__).parent / "fixtures" / "speech-librivox-3s.wav"


@pytest.fixture
def clipped(tmp_path):
    x, fs = sf.read(FIXTURE, dtype="float64")
    y, thr, mask = damage.clip_to_sdr(x, 5.0)  # lands near 0.036, 16 dB under the fixture's own peak
    p = tmp_path / "clipped.wav"
    sf.write(p, y, fs, subtype="FLOAT")
    return p, x, y, thr, mask


@needs_ffmpeg
def test_ffmpeg_adeclip_improves_sdr_on_a_clipped_voice(clipped, tmp_path):
    p, x, y, thr, mask = clipped
    est, _ = sf.read(run_ffmpeg(TOOLS, p, tmp_path / "out.wav", "adeclip"), dtype="float64")
    assert metrics.delta_sdr(x, y, est) > 0.5  # 03c measured +2.57 dB with ffmpeg 6.1.1 at defaults


@needs_cathar
def test_cathar_declip_improves_sdr_at_the_manifest_threshold(clipped, tmp_path):
    p, x, y, thr, mask = clipped
    est, _ = sf.read(run_cathar(CATHAR, p, tmp_path / "out.wav", "declip", threshold=thr), dtype="float64")
    assert metrics.delta_sdr(x, y, est) > 0.5  # 03c measured +7.71 dB; at cathar's default 0.95 it is exactly 0, which this test must never be allowed to pass
    assert np.array_equal(est[~mask], y[~mask])  # A-SPADE returns every unclipped sample unchanged
```

- [ ] **Step 5: Implement `benchmark_repair.py` and `make_repair_set.py`**

`make_repair_set.py`: reads the references from `~/.cache/cumple/real-dialogue/` (the SQAM FLACs and the LibriVox chapter, as `fetch_real_dialogue.sh` leaves them; `CUMPLE_REPAIR_SET` overrides), decoded through `cumple.io.reader.read`, writes `damaged/<name>.clip<sdr>.wav` at each survey level, `damaged/<name>.impulse<seed>.wav` and `damaged/<name>.burst<seed>.wav`, `rx8-input/<name>.clip<sdr>.wav` scaled so the clip level sits at 0.95 with the scale in the manifest, and `manifest.json`. Refuses to run when no reference is present and prints the fetch script's name.

`benchmark_repair.py`: `run_ffmpeg` builds the argv list the way `io/ffmpeg.py` does (`-nostdin`, `-v error`, `-protocol_whitelist file`, a timeout that kills, stderr capped), filter `adeclick` or `adeclip` at defaults, output `pcm_f32le`. `run_cathar` runs `cathar declick INPUT --out OUT --threshold 5` or `cathar declip INPUT --out OUT --threshold <manifest value>` with the same discipline and records `cathar --version`. For each damaged file and each tool: decode, compute ΔSDR(all), ΔSDR(damaged), residual clicks (impulse and burst tables, at threshold 5), peak error (clip files), wall time. The RX columns read `rx8/<name>` when the folder exists and its manifest hashes match, divide by the recorded scale, else print "not run (RX 8 outputs not present; see docs/repair/rx8-recipe.md)". Writes Markdown to stdout: a header with versions, the references present and the read dates, one table per damage type (clip, impulse, burst) with a row per file and level and a column per tool, and a summary block with the per-tool means that `tests/test_repair_numbers.py` pins in Task 6. Exits with a message and no output if ffmpeg or cathar is missing (`sys.exit`, as `benchmark_meters.py` does at its lines 99 and 147).

- [ ] **Step 6: Build the cathar baseline, run the harness once, write the recipe**

```bash
cargo install --git https://github.com/vbasky/cathar --rev f2c2842f89084589d069e5a8a0b61311aa70d928 cathar-cli --locked   # about two minutes; 03c built it this way
cathar --version   # cathar 0.8.0
uv run python scripts/make_repair_set.py
uv run python scripts/benchmark_repair.py > docs/REPAIR.md
```

`docs/REPAIR.md` at this point has the ffmpeg and cathar columns filled, the cumple columns "not run: build 1 Task 5" and the RX columns "not run". Expect the ffmpeg `adeclick` row to read near zero on the impulse table (03c measured 0.02 dB the wrong way) and record it as measured. Write `docs/repair/rx8-recipe.md`: the two RX 8 modules, the factory preset names as read from the preset XML on Victor's machine (the recipe says which files it read and quotes the parameter names from the 02a report), Batch Processing steps, the input folder (`rx8-input/`, and why it is scaled), the output folder (`rx8/`), the naming RX uses, and the manifest table Victor fills with SHA-256 values.

- [ ] **Step 7: Run the suite, re-pin counts, commit**

This task adds one ffmpeg-gated test (README's macOS and Windows "fewer" figures each go up by one) and one cathar-gated test (it skips on macOS and Windows until Task 2 builds cathar on Linux, so those two figures go up by one more; the Ubuntu sentence stays true once Task 2 lands, and until then the README sentence says "runs N-29 of them on Ubuntu, M fewer until the cathar baseline is built there").

---

### Task 2: The Rust workspace, the STFT, the wheel, CI

**Files:**
- Create: `Cargo.toml` (workspace), `crates/cumple-dsp/Cargo.toml`, `crates/cumple-dsp/src/lib.rs`, `crates/cumple-dsp/src/stft.rs`, `crates/cumple-dsp/src/module.rs`, `crates/cumple-dsp/THIRD_PARTY.md`, `crates/cumple-dsp-py/Cargo.toml`, `crates/cumple-dsp-py/pyproject.toml`, `crates/cumple-dsp-py/src/lib.rs`, `deny.toml`, `rust-toolchain.toml`
- Modify: `pyproject.toml` (extra, uv workspace and sources), `.github/workflows/tests.yml` (toolchain, cache, `--extra repair`, cargo steps, the cathar build on Linux), `.gitignore` (`target/`), `CONTRIBUTING.md` (Rust, `--extra repair`, the reinstall line)
- Test: `crates/cumple-dsp/src/stft.rs` unit tests, `tests/test_repair_core.py`

**Interfaces:**
- Consumes: nothing from Task 1.
- Produces: Rust `Window::{HannPeriodic, HannSymmetric}`, `Stft::new(n_fft, hop, window) -> Stft`, `Stft::n_frames(len) -> usize`, `Stft::analyze(&mut self, x: &[f64], out: &mut [Complex<f64>])` (frames by `n_fft / 2 + 1` bins, row major, no padding: the first frame starts at sample 0, the last frame is the last that fits), `Stft::synthesize(&mut self, spec: &[Complex<f64>], out: &mut [f64])`; trait `Module` with `id`, `version`, `context_frames`, `latency_frames`, `process(&mut self, input: &[f64], output: &mut [f64], edge: Edge)`, `flush`, `report`; `Edge { first: bool, last: bool, padding: usize }`; `Report { events: Vec<Event>, counters: Vec<(String, f64)> }`; a `Chunker` helper that feeds `context + block + context` with the right `Edge` and copies out the centre, and `process_whole` that calls `process` once over a whole signal with `Edge { first: true, last: true, padding: 0 }`; Python `cumple_dsp.__version__`, `cumple_dsp.core_version()`, `cumple_dsp.Stft(n_fft, hop, window="hann")` with `analyze(x: float64[n]) -> complex128[frames, bins]` and `synthesize(spec, length) -> float64[length]`.

- [ ] **Step 1: Workspace, toolchain, deny**

Root `Cargo.toml`: `[workspace] resolver = "3" members = ["crates/cumple-dsp", "crates/cumple-dsp-py"]`, `[workspace.package] edition = "2024" rust-version = "1.87" license = "MIT" repository = "https://github.com/victor10days/cumple"`, `[workspace.dependencies] rustfft = "6" realfft = "3"`, release profile `lto = "thin"`. `rust-toolchain.toml`: stable with `clippy` and `rustfmt`. `deny.toml`: `[licenses] version = 2` and the SPDX allowlist from the spec (`MIT`, `Apache-2.0`, `Apache-2.0 WITH LLVM-exception`, `BSD-2-Clause`, `BSD-3-Clause`, `ISC`, `Unicode-3.0`, `Zlib`); `cargo deny check licenses` must pass, and the first run prints which crate needed each id (expect target-lexicon for the exception and unicode-ident for Unicode-3.0).

- [ ] **Step 2: Write the failing STFT tests in Rust and in Python**

Rust (`stft.rs`, `#[cfg(test)]`): a 4,096-sample 440 Hz sine at 48 kHz through `analyze` at `n_fft = 1024, hop = 256` has its largest bin at round(440 / 48000 * 1024) = 9 in every frame; analyze then synthesize reproduces the input within 1e-10 from sample `n_fft` to `len - n_fft`; a signal shorter than `n_fft` yields zero frames and `synthesize` of zero frames writes zeros; `HannSymmetric` of length 1,024 equals cathar's `hann_window` (0.5 - 0.5 cos(2 pi i / 1023)) at i = 0, 511, 512 and 1023.

Python (`tests/test_repair_core.py`, `needs_core`):

```python
def test_stft_matches_scipy_within_tolerance():
    import cumple_dsp
    from scipy.signal import ShortTimeFFT
    from scipy.signal.windows import hann

    fs, n_fft, hop = 48000, 1024, 256
    rng = np.random.default_rng(0)
    x = rng.standard_normal(fs) * 0.1
    ours = cumple_dsp.Stft(n_fft, hop).analyze(x)  # (frames, bins), frame j covers samples j*hop .. j*hop + n_fft - 1
    # phase_shift=None: scipy's default references each slice's phase to its centre and flips every odd bin against a plain windowed FFT
    sft = ShortTimeFFT(hann(n_fft, sym=False), hop=hop, fs=fs, fft_mode="onesided", phase_shift=None)
    assert sft.p_min == -1, "scipy's first slice index changed; recompute the offset"
    # scipy slice p is centred at p*hop; the slice centred at n_fft//2 = 512 is p = 2, which is column p - p_min = 3
    first = (n_fft // 2) // hop - sft.p_min
    theirs = sft.stft(x)  # (bins, columns)
    common = min(ours.shape[0], theirs.shape[1] - first)
    np.testing.assert_allclose(ours[:common].T, theirs[:, first : first + common], atol=1e-9, rtol=0)
```

03b and 03c both ran this alignment against scipy 1.18.1 and got 2.4e-15; the first version of this plan (`k0 = 2`, default phase) got differences of 9.5 to 12.4 at every offset, which is what a wrong oracle looks like.

- [ ] **Step 3: Implement `stft.rs` and `module.rs`**

Plan the forward and inverse transforms once in `new` (`realfft::RealFftPlanner`), keep scratch buffers, apply the window on analysis and synthesis, and divide by the window-squared overlap sum computed once (constant away from the edges for hop = n_fft / 4; at the edges divide by the partial sum, never by zero). `module.rs` is the trait, `Edge`, the `Report` types, `Chunker` and `process_whole` from the spec.

- [ ] **Step 4: The bindings crate and the wheel**

`crates/cumple-dsp-py/pyproject.toml`: `[build-system] requires = ["maturin>=1.9.4,<2"] build-backend = "maturin"`, `[project] name = "cumple-dsp" version = "0.1.0" requires-python = ">=3.12" dependencies = ["numpy>=2.0"]` (a static version, so `uv lock` never has to run maturin), `[tool.maturin] module-name = "cumple_dsp" features = ["pyo3/abi3-py312"]`, and:

```toml
[tool.uv]
cache-keys = [
  { file = "pyproject.toml" },
  { file = "Cargo.toml" },
  { file = "src/**/*.rs" },
  { file = "../cumple-dsp/Cargo.toml" },
  { file = "../cumple-dsp/src/**/*.rs" },
  { file = "../../Cargo.lock" },
]
```

`Cargo.toml`: `crate-type = ["cdylib"]`, `test = false` on the lib target, `pyo3` with `abi3-py312` and without `extension-module` (deprecated; maturin 1.9.4 links without it), the `numpy` crate, `cumple-dsp = { path = "../cumple-dsp" }`. `src/lib.rs`: `#[pymodule] fn cumple_dsp` with `__version__` (read from the crate version), `core_version()` and `Stft` (`analyze` wraps the transform in `py.detach`, output allocated once as a `PyArray2<Complex64>`).

Root `pyproject.toml`:

```toml
[project.optional-dependencies]
repair = ["cumple-dsp"]

[tool.uv.workspace]
members = ["crates/cumple-dsp-py"]

[tool.uv.sources]
cumple-dsp = { workspace = true }
```

`uv sync --extra repair` then builds the wheel; `uv run python -c "import cumple_dsp; print(cumple_dsp.__version__, cumple_dsp.core_version())"` prints `0.1.0 0.1.0`. Then verify the rebuild rule with a deliberate edit: change a constant in `stft.rs`, run `uv sync --extra repair` and check the import reflects it; if it does not, the global constraint's `--reinstall-package cumple-dsp` line stays in every later step and CONTRIBUTING, and this step records which. Commit `uv.lock`.

- [ ] **Step 5: CI**

`tests.yml`, in the matrix job after `uv sync --group dev`: `dtolnay/rust-toolchain@stable`, `Swatinem/rust-cache@v2`, `uv sync --group dev --extra repair`, then `cargo fmt --all -- --check`, `cargo clippy --workspace --all-targets -- -D warnings`, `cargo test -p cumple-dsp`; on the Ubuntu leg only, `EmbarkStudios/cargo-deny-action` for `cargo deny check licenses` (licences do not vary by runner) and the cathar baseline: `actions/cache` on `~/.cargo/bin/cathar` keyed by the pinned revision (`Swatinem/rust-cache` does not cache `~/.cargo/bin`), then `cargo install --git https://github.com/vbasky/cathar --rev f2c2842f89084589d069e5a8a0b61311aa70d928 cathar-cli --locked` on a miss, and `CUMPLE_CATHAR=~/.cargo/bin/cathar` in the environment of `uv run pytest`. `release.yml` is untouched: its paths trigger it on this pull request (four runners, including macos-15-intel), it syncs `--extra app` only and never sees the extension; Task 7 reads its result too.

- [ ] **Step 6: Run everything, commit**

`cargo fmt`, `cargo clippy`, `cargo test -p cumple-dsp`, `cargo deny`, ruff, `uv run pytest` (the new Python test runs locally with the wheel built), re-pin counts (this task adds one core-gated test, which runs on all three runners once CI builds the extension), commit.

---

### Task 3: De-click and Interpolate, ported from cathar

**Files:**
- Create: `crates/cumple-dsp/src/declick.rs`, `crates/cumple-dsp/src/inpaint.rs`
- Modify: `crates/cumple-dsp/src/lib.rs`, `crates/cumple-dsp-py/src/lib.rs` (the `Declick` class), `crates/cumple-dsp/THIRD_PARTY.md`
- Test: Rust unit tests in both files; `tests/test_repair_declick.py`; `tests/repair_helpers.py` (`chunked`, `boundary_mask` that also covers the file head and tail)

**Interfaces:**
- Consumes: `Module`, `Edge`, `Report`, `Chunker`, `process_whole` from Task 2; `damage`, `metrics` from Task 1; `find_cathar`, `run_cathar` from Task 1.
- Produces: Rust `Declick::new(threshold: f64, window: usize, method: DeclickMethod, iterations: u32) -> Result<Declick, ParamError>` (rejects `threshold >= sqrt(window)`), implementing `Module` with `context_frames() == 16_384`; `inpaint_gap(signal: &mut [f64], start: usize, len: usize, iterations: u32) -> Fill` (`Fill::{Ar, Linear}`), in place; `DeclickMethod::{Ar, Cubic}`; Python `cumple_dsp.Declick(samplerate, threshold=5.0, window=64, method="ar", iterations=3)` with `context_frames`, `latency_frames`, `process(block, edge=...)`, `process_whole(x)`, `flush()`, `report()` (`{"clicks": n, "positions": [...], "widths": [...], "linear_fallbacks": n, "context_fallbacks": n}`).

- [ ] **Step 1: Write the failing Python tests**

```python
"""De-click: the port matches upstream cathar whole-file within tolerance, chunking costs what it costs, and nothing outside the clicks moves."""

CATHAR = find_cathar()


def clicked(seed=3):
    x, fs = sf.read(FIXTURE, dtype="float64")
    y, clicks, mask = damage.add_clicks(x, fs, seed=seed, per_minute=200, **damage.IMPULSE)  # about ten clicks in 3 s
    return x, y, clicks, mask, fs


@needs_core
def test_declick_removes_injected_clicks_and_leaves_the_rest_alone():
    import cumple_dsp
    x, y, clicks, mask, fs = clicked()
    m = cumple_dsp.Declick(fs)
    est = m.process_whole(y)
    missed, false = metrics.residual_clicks(x, est, [c.position for c in clicks], [c.width for c in clicks], threshold=5.0)
    assert missed <= len(clicks) // 10
    dilated = damage.dilate(mask, 8)
    np.testing.assert_allclose(est[~dilated], y[~dilated], atol=1e-9)
    assert metrics.delta_sdr(x, y, est) > 3.0
    assert m.report()["clicks"] >= len(clicks) * 0.9


@needs_core
def test_declick_rejects_a_threshold_the_detector_cannot_reach():
    import cumple_dsp
    with pytest.raises(ValueError, match="sqrt"):
        cumple_dsp.Declick(48000, threshold=8.0, window=64)


@needs_core
@needs_cathar
def test_declick_matches_upstream_cathar_whole_file(tmp_path):
    import cumple_dsp
    x, y, clicks, mask, fs = clicked()
    p = tmp_path / "clicks.wav"; sf.write(p, y, fs, subtype="FLOAT")
    up, _ = sf.read(run_cathar(CATHAR, p, tmp_path / "up.wav", "declick", threshold=5.0), dtype="float64")
    est = cumple_dsp.Declick(fs, threshold=5.0).process_whole(y)
    assert abs(metrics.delta_sdr(x, y, est) - metrics.delta_sdr(x, y, up)) < 0.1
    assert np.max(np.abs(est - up)) < 1e-3  # cathar's f32 running RMS rewrites a few near-silent samples below 1e-3; a wrong gap moves samples by whole units


@needs_core
def test_chunking_cost_is_measured_and_small():
    import cumple_dsp
    x, y, clicks, mask, fs = clicked(seed=5)
    whole = cumple_dsp.Declick(fs).process_whole(y)
    a = chunked(cumple_dsp.Declick(fs), y[:, None], block=8192)[:, 0]
    b = chunked(cumple_dsp.Declick(fs), y[:, None], block=16384)[:, 0]
    np.testing.assert_allclose(a, whole, atol=1e-9)  # every gap here is far shorter than the context covers
    np.testing.assert_allclose(b, whole, atol=1e-9)
```

Note `process_whole` for the fidelity comparison: the fixture is 48,000 samples and the runner's real block is 262,144, so chunking never enters the fidelity rule. The chunked test exercises the `Chunker` at small blocks where it must still match whole-file for short gaps; the long-gap case is a Rust test (Step 3).

- [ ] **Step 2: Port `inpaint.rs`**

Translate cathar's `inpaint_gap`, `estimate_ar_known`, `levinson`, `coef_autocorr`, `solve_gap` and `solve_spd_banded` to f64 slices operating in place, with `AR_ORDER = 32`, `MAX_SOLVE = 2048`, `p = len.clamp(32, 128)`, `ctx = max(4 * len, 8 * p, 1024)` and the linear pre-fill exactly as upstream; the file header names the source. Return `Fill::Linear` when `len > MAX_SOLVE` or when the context would reach past the slice (the module turns that into a context fallback in the report). Rust tests: a gap of 200 samples cut from a 440 Hz sine at 48 kHz is refilled within 1e-3 after 3 iterations; a gap longer than `MAX_SOLVE` is filled linearly and reported as such; out-of-range spans leave the buffer unchanged.

- [ ] **Step 3: Port `declick.rs`**

Translate `declick_with_method`, `local_rms` and `cubic_interpolate` to f64, operating on `input` and writing `output`, then wrap in a `Module` whose `process` runs the whole-chunk algorithm on `context + block + context` (the shoulder pad `half.clamp(2, 8)` and the gap growth stay as upstream; the end-of-file cubic branch runs only when `Edge.last` and the gap reaches the true end), records each gap's start and length into the report, and counts linear and context fallbacks. The constructor rejects `threshold >= sqrt(window)` with a message that names the bound. Rust tests: the same local-RMS values as a direct numpy computation on a short vector (write the expected numbers into the test); a single-sample click at 20 times the clean local RMS in a sine is detected at threshold 5 (its ratio in the window that contains it is about 7.4, which is why 10 never fires) and refilled within 1e-3; a clean sine passes through unchanged; a 1,500-sample gap placed 2,000 samples from a chunk edge is filled identically (within 1e-9) by the chunked and the whole-file calls, which is what `context_frames = 16_384` buys.

- [ ] **Step 4: The Python class, mutation check, commit**

Add `Declick` to the bindings (one `declick::Declick` per channel, `process` and `process_whole` under `py.detach`, output allocated once per call). Prove the fidelity test can fail: temporarily shift the gap start by one sample in the AR path (the method the defaults use; the cubic fill only runs at file edges), run `uv sync --extra repair --reinstall-package cumple-dsp`, run `tests/test_repair_declick.py`, see the upstream comparison fail, revert, rebuild, record the failing figure in the commit message. Run the full checks, commit. Adds two cathar-gated and three core-gated tests; count them.

---

### Task 4: De-clip (A-SPADE and cubic), ported from cathar

**Files:**
- Create: `crates/cumple-dsp/src/declip.rs`
- Modify: `crates/cumple-dsp/src/lib.rs`, `crates/cumple-dsp-py/src/lib.rs` (the `Declip` class), `THIRD_PARTY.md`
- Test: Rust unit tests; `tests/test_repair_declip.py`

**Interfaces:**
- Consumes: `Window::HannSymmetric` (for the test only), `Module`, `Edge` from Task 2; `damage.clip_to_sdr`, `metrics` from Task 1.
- Produces: Rust `Declip::new(threshold: f64, method: DeclipMethod) -> Declip` with `context_frames() == 4096`, `DeclipMethod::{Spade, Cubic}`; Python `cumple_dsp.Declip(samplerate, threshold=0.95, method="spade")`, same surface as `Declick`; `report()` gives `{"runs": n, "longest_run": n, "peak_in": x, "peak_out": x, "iterations": n, "frames": n}`.

- [ ] **Step 1: Write the failing Python tests**

(a) The fixture clipped to 5 dB input SDR, run at the manifest threshold through `process_whole`: ΔSDR(all) at least 2 dB (03c measured +7.56 for a faithful port), every unclipped sample exactly equal to the input (`np.array_equal`, no dilation), the restored peak within 3 dB of the reference's over the mask at 5 dB (measured +1.98; the 1 dB and 3 dB levels are reported in REPAIR.md, not asserted, since the survey's own tables show A-SPADE overshooting there). (b) Upstream: `run_cathar(..., "declip", threshold=thr)` on the same file against `process_whole` at the same threshold: ΔSDR(all) and ΔSDR(clipped) within 0.1 dB (03c: 0.01 dB between the CLI and a faithful f64 port), and `np.array_equal` on unclipped samples; no bound on rebuilt samples (two faithful implementations differ by up to 0.18 there). (c) Chunking cost: `chunked` at 8,192 and at 65,536 against `process_whole`, ΔSDR differences printed and asserted under 0.5 dB (03c measured 0.29 at 8,192), unclipped samples still exactly equal; the harness pins the figure at `DEFAULT_BLOCK_FRAMES` (expected about 0.03 dB) in Task 6. (d) A file with no sample at or above the threshold passes through untouched; a chunk shorter than one frame passes through untouched.

- [ ] **Step 2: Port `declip.rs`**

Translate from the code, not from memory, and keep every one of these as upstream has them (03b and 03c found each one misdescribed in the first version of this plan): `hann_window` symmetric (divide by `L - 1`); `frame_starts` with the flush frame when the length is off the hop grid; a full complex 1,024-point FFT through `rustfft` with the `1/sqrt(L)` scale; `hard_threshold_k` over all 1,024 complex bins keeping ties at the cutoff; `k` starting at 1 and growing by `RELAX_BY = 2` on every iteration; `MAX_ITER = 100`; the residual summed over all bins of every frame against `eps` from the signal energy; `project_gamma` returning every unclipped sample unchanged; the cubic fill with its 4-sample shoulders; the early return when nothing reaches the threshold. The file header says the module keeps its own frame rather than the shared `Stft` and why (the measured 0.11 sample and up to 1.3 dB ΔSDR difference of the one-sided periodic variant). Rust tests: a clipped 440 Hz sine at 0.5 full scale recovers its peak within 1 dB; the no-clip early return; a chunk shorter than one frame; `hard_threshold_k` keeps exactly `k` bins and ties on a hand-built spectrum.

- [ ] **Step 3: The Python class, mutation check, commit**

As Task 3 Step 4. The mutation: drop the clipping-consistency projection for one run, rebuild, and watch the upstream ΔSDR comparison fail by whole dB. Adds one cathar-gated and three core-gated tests; count them.

---

### Task 5: The runner, parameters, chains, presets, receipts, the CLI

**Files:**
- Create: `src/cumple/repair/params.py`, `src/cumple/repair/chain.py`, `src/cumple/repair/runner.py`, `src/cumple/repair/receipt.py`, `src/cumple/repair/presets/declick.yaml`, `src/cumple/repair/presets/declip.yaml`, `src/cumple/repair/presets/declick-declip.yaml`
- Modify: `src/cumple/repair/__init__.py`, `src/cumple/cli.py`, `README.md` (the command list and "Honest limits"), `AI_USAGE.md`
- Test: `tests/test_repair_chain.py`, `tests/test_repair_runner.py`, `tests/test_cli_repair.py`

**Interfaces:**
- Consumes: `cumple_dsp.Declick`, `cumple_dsp.Declip`; `iter_blocks`, `probe`, `DEFAULT_BLOCK_FRAMES` from `io/reader.py`; `measure` from `meters/measure.py`; the write discipline of `fix.py`; `user_dir()` from `specs/registry.py`.
- Produces: `params.DeclickParams(threshold: float = 5.0, window: int = 64 (ge 8, le 1024), method: Literal["ar", "cubic"] = "ar", iterations: int = 3 (ge 1, le 10))` with a validator that rejects `threshold < 1` and `threshold >= sqrt(window)`, naming the bound; `params.DeclipParams(threshold: float = 0.95 (ge 1e-4, le 1.0), method: Literal["spade", "cubic"] = "spade")`, both `extra="forbid"`; `params.MODULES = {"declick": DeclickParams, "declip": DeclipParams}`; `chain.Chain(id, summary, steps: list[ChainStep])`, `chain.parse(text) -> Chain` (one-line form), `chain.load(path) -> Chain` (YAML), `chain.dump(chain) -> str`, `chain.presets() -> dict[str, Chain]`, `chain.resolve(text_or_id) -> Chain`; `runner.repair_file(src, chain, dst, residual=None) -> RepairResult(dst, receipt_path, reports, changed: bool)`; `receipt.write(path, ...)` and `receipt.Receipt` (pydantic); `cli.repair`.

- [ ] **Step 1: Write the failing tests**

Chain: `parse("declick(threshold=6),declip()")` gives two steps with the right params; `parse("declick(foo=1)")` raises `ValueError` naming `foo`; `parse("declick(threshold=9)")` raises naming the sqrt bound; `dump(parse(t))` round-trips through `load`; a preset YAML with an unknown key fails to load with the key named; the three built-in presets load; a user preset under a temporary `XDG_CONFIG_HOME` overrides a built-in with the same id (`specs/registry.py` lines 28 to 30 honour that variable).

Runner (`needs_core`): the clicked fixture through `declick` gives a copy whose SHA-256 differs, a receipt beside it with the chain, the two version strings, the input SHA-256, both `measure()` summaries and one report; `dst == src` raises; `dst` a directory raises; a 2-channel WAV built in the test has each channel repaired independently (clicks injected only in channel 1 leave channel 0 bit-identical); `--residual` output equals input minus output within 1e-9; an input with no clicks gives `changed == False` and no file written; the temporary file never survives a failure (patch the writer to raise mid-way and assert the directory is clean); a two-module chain (`declick(),declip(threshold=thr)`) on a file with both damages, run chunked at 8,192, against the whole-file reference (upstream run twice, or `process_whole` twice): ΔSDR within a measured tolerance recorded in the test, which is the cost of raw right context the spec states; the first block of the file is processed with `Edge.first` and the last with its true length (assert through a module report that no gap was filled with zero context).

CLI (`CliRunner`): `cumple repair clicks.wav --chain "declick()" --out out.wav` exits 0, prints the copy and the receipt path and the click count; with `--preset declick` the same; with a chain naming an unknown module exits 2; with `--out` equal to the input exits 2; on a clean file exits 1 with "nothing to change" (this is the one place the codes differ from `fix`, which exits 0 on a file that already complies; the help text says so); without the extension (monkeypatch `cumple.repair.available` to `False`) exits 2 and the hint contains `uv tool install`, `[repair]` with the brackets intact, and the words "compiles the Rust core"; a path with `[` in its name is printed intact (every interpolated path or exception goes through `rich.markup.escape`); `--list-presets` names the three built-ins.

- [ ] **Step 2: Implement `params.py`, `chain.py`**

The one-line grammar: `name(k=v, k=v)` steps separated by commas, values parsed by pydantic from strings; whitespace free. YAML form:

```yaml
id: declick-declip
summary: Clicks first, then clipped peaks; the clip threshold is for a file clipped at full scale.
steps:
  - module: declick
    params: { threshold: 5.0, window: 64, method: ar, iterations: 3 }
  - module: declip
    params: { threshold: 0.95, method: spade }
```

- [ ] **Step 3: Implement `runner.py` and `receipt.py`**

The block loop: a ring per module holding the last `context_frames` of its own output as left context, a one-block lookahead read ahead from `iter_blocks` as raw right context for every module, `Edge.first` on the first block and `Edge.last` with the padding count on the last, so each `process` call receives `prev_context + block + next_context`; the padding is dropped on write. Open the output with `sf.SoundFile(..., subtype=info.subtype, format=info.container)` as `fix.apply` does; clip to `[-1, 1]` only for integer subtypes. `measure()` runs on the source before and on the copy after, with the default arguments. The receipt is written last; the temporary name and `os.replace` are copied from `fix_file`, not re-invented.

- [ ] **Step 4: Implement `cli.repair`, docs, commit**

Follow `fix`'s structure for options, console output and the re-check, with `escape()` on every interpolated path and exception. README gains `repair` in the command list, a "Repair" section with the install route (it compiles Rust; cargo is needed), the two modules, the detector bound, the chain forms and the receipt, and an "Honest limits" line: two modules, PCM only, no metadata copy, numbers in `docs/REPAIR.md`. AI_USAGE records the run and this build. Run everything, re-pin counts, commit.

---

### Task 6: cumple in the harness, `docs/REPAIR.md` pinned, the roadmap

**Files:**
- Modify: `scripts/benchmark_repair.py` (the cumple columns through `repair_file` and the chunking-cost column through `process_whole`), `docs/REPAIR.md` (regenerated), `docs/ROADMAP.md` (R10 to building, then merged in the receipt)
- Create: `tests/test_repair_numbers.py`, `docs/graph-runs/2026-10-08-rx-parity-landscape/06-build-1-notes.md` (what was measured, the mutation figures, any tolerance that had to move and why)

**Interfaces:**
- Consumes: everything above.
- Produces: `docs/REPAIR.md` with every column filled or "not run" (cumple, cumple chunking cost, ffmpeg, cathar, RX 8 De-click, RX 8 De-clip) across the clip, impulse and burst tables; `tests/test_repair_numbers.py`.

- [ ] **Step 1: Write the failing pin test**

Parse the summary block and the tables as `test_site_numbers.py` does; assert each summary mean equals the mean of its column within 0.005; `needs_core` only (no ffmpeg needed: the re-run is cumple's own): re-run the fixture damaged with seed 3 (impulse preset) through `declick` and assert ΔSDR(all) matches the pinned "fixture" row within 0.05 dB, where the "fixture" row is a row the harness writes for `tests/fixtures/speech-librivox-3s.wav` itself, not for the cache set; assert the chunking-cost column for De-clip at `DEFAULT_BLOCK_FRAMES` is under 0.5 dB on every row; assert the file contains no "not checked" and the RX columns say "not run" or carry numbers.

- [ ] **Step 2: Add the cumple columns, regenerate, pin**

`uv run python scripts/benchmark_repair.py > docs/REPAIR.md`. The header states: versions (cumple, cumple_dsp, ffmpeg, cathar commit), the reference set present, the seeds, the detector of record and its bound, the tolerances from the spec's scoring rule and whether each was met. If a tolerance was not met, the number stays and the build is not done: fix the port or write the reason in `06-build-1-notes.md` and bring it to Victor.

- [ ] **Step 3: Roadmap and notes, commit**

R10 to `building` with the branch name. Run everything, re-pin counts (this task adds one core-gated test), commit.

---

### Task 7: The whole-branch review and the receipt

- [ ] A fresh context reviews the branch diff against the spec's scoring rule and this plan's constraints (as the Silero run's `03b-branch-review.md` did), with the harness output and the mutation figures in hand, and with 03b and 03c open so it can check each concern was closed and not merely edited.
- [ ] Open the pull request from the branch (title: one sentence; body from the receipt's "What shipped"); subscribe to it; drive CI to green on the three test runners and the four release runners (`release.yml` runs on the PR because its paths include `pyproject.toml` and `uv.lock`).
- [ ] After green checks: `docs/graph-runs/2026-10-08-rx-parity-landscape/05-receipt.md` gains the PR link under "What shipped" and a "Build 1" section with what was measured; `docs/ROADMAP.md` R10 to `merged` with the PR number and the receipt path. Commit on the same branch before merge, as the earlier runs did.
