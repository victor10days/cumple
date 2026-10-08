# Repair foundation (build 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. A plan skeptic with no history with this file reads it against the spec and the code before Task 1 runs; its findings are fixed in this file first.

**Goal:** `cumple repair <file> --chain "declick(),declip()" --out <copy>` writes a repaired PCM copy through a Rust core ported from cathar, with a sidecar receipt, and `docs/REPAIR.md` scores De-click and De-clip against ffmpeg and cathar on synthetic damage with a held clean reference, with RX 8 columns that read "not run" until Victor's Batch Processing outputs land.

**Architecture:** A Cargo workspace at the repository root with `crates/cumple-dsp` (pure Rust: streaming STFT on realfft, a module trait with `context_frames`, `latency_frames`, `process`, `flush`, `report`, and the De-click, Interpolate and De-clip ports) and `crates/cumple-dsp-py` (PyO3 abi3 bindings, maturin, distribution `cumple-dsp`, import `cumple_dsp`), behind the extra `cumple[repair]`. `src/cumple/repair/` holds pydantic parameters, chain parsing, the streaming runner on `iter_blocks`, the receipt and the metrics. `cli.py` gains `repair`. The harness is `scripts/make_repair_set.py`, `scripts/benchmark_repair.py`, `docs/REPAIR.md`, `docs/repair/rx8-recipe.md` and `tests/test_repair_numbers.py`. No meter, check, profile or report changes.

**Tech Stack:** Rust stable (edition 2024, `rust-version` 1.87, as cathar), `rustfft` 6, `realfft` 3, `pyo3` and `numpy` crates at their current releases pinned by `Cargo.lock`, maturin, `cargo-deny`; Python 3.12, numpy, scipy (`ShortTimeFFT` as the oracle), soundfile, pydantic, pyyaml, typer; ffmpeg 9.0.1 (`adeclick`, `adeclip`) and a cathar CLI built at commit `f2c2842f89084589d069e5a8a0b61311aa70d928` as subprocess baselines.

**Spec:** `docs/superpowers/specs/2026-10-08-repair-foundation-design.md`. Research: `docs/graph-runs/2026-10-08-rx-parity-landscape/`.

## Global Constraints

- The base install does not change: `pyproject.toml` `dependencies` stay as they are; the new extra is `repair = ["cumple-dsp"]` with `[tool.uv.workspace]` and `[tool.uv.sources]` wiring; the dev group does not carry the extension, so `uv sync` works without Rust. CI syncs `--extra repair` after `dtolnay/rust-toolchain@stable` and `Swatinem/rust-cache`.
- Every test that needs the core uses `needs_core = pytest.mark.skipif(importlib.util.find_spec("cumple_dsp") is None, reason="cumple-dsp is not built; uv sync --extra repair")`; nothing in the suite requires Rust. Tests that need ffmpeg or the cathar binary skip with the reason, as `test_ffmpeg_io.py` does.
- Ported Rust carries, at the top of each file, `// Ported from cathar (github.com/vbasky/cathar) <path> at commit f2c2842f, MIT OR Apache-2.0, used under MIT; see crates/cumple-dsp/THIRD_PARTY.md.` No GPL or AGPL source is read while porting (Audacity, GWC, IPOL, the survey's MATLAB).
- f64 throughout the core; numpy arrays are `float64`, shape `(frames, channels)`, C order; a block never exceeds `DEFAULT_BLOCK_FRAMES + 2 * context_frames`.
- Writes follow `fix.apply` and `fix_file`: same subtype and format, a temporary name beside the destination (`.<name>.cumple-tmp`), `os.replace`, refuse `dst.resolve() == src.resolve()`, refuse a directory, refuse a file ffmpeg decoded. The receipt is written after the copy is in place.
- The phrase "not checked" never appears; tables say "not run" with a reason. No em or en dash in prose, comments, docstrings, YAML or Rust doc comments.
- `uv run ruff check src tests scripts && uv run ruff format --check src tests scripts`, `cargo fmt --all -- --check`, `cargo clippy --workspace --all-targets -- -D warnings`, `cargo test --workspace`, `cargo deny check licenses` clean before each commit. `uv run pytest` alone, never piped, in full before each commit; re-pin the five documented counts (README `**Tests**: N,` and `runs N-29 of them on Ubuntu`, CONTRIBUTING `# N tests;`, docs/QA.md `` `uv run pytest`, N tests``, AI_USAGE `N tests, including`, site/index.html `N tests with 91 %`) from `uv run pytest --collect-only 2>/dev/null | grep 'tests collected'`; README's "19 fewer on macOS" and "20 fewer on Windows" change only if a new test is gated on ffmpeg (Task 1 adds two; count them).
- Commit after every task: one plain imperative sentence, a blank line, then the attribution lines the session reminder gives. No model identifier anywhere else in the repository.
- Work on the branch the executing session names; never `cd` to Victor's main checkout; never push to main.

---

### Task 1: The harness first: damage, metrics, the ffmpeg and cathar baselines

The first measured number arrives before any new DSP is written (receipt ruling). Nothing here imports the core.

**Files:**
- Create: `src/cumple/repair/__init__.py` (only `available()`, `require()`, `RepairUnavailable` for now), `src/cumple/repair/metrics.py`, `src/cumple/repair/damage.py`, `scripts/make_repair_set.py`, `scripts/benchmark_repair.py`, `docs/repair/rx8-recipe.md`, `docs/REPAIR.md` (first version: baselines only; the cumple column reads "not run: build 1 Task 5")
- Test: `tests/test_repair_metrics.py`, `tests/test_repair_baselines.py`

**Interfaces:**
- Consumes: `cumple.io.reader.read`, `cumple.io.ffmpeg.find_ffmpeg`, `tests/fixtures/speech-librivox-3s.wav`.
- Produces: `metrics.sdr_db(ref, est) -> float`; `metrics.delta_sdr(ref, damaged, est, mask=None) -> float`; `metrics.residual_clicks(ref, est, positions, widths, threshold) -> tuple[int, int]` (missed, false); `metrics.peak_error_db(ref, est, mask) -> float`; `damage.clip_to_sdr(x, target_sdr_db) -> tuple[np.ndarray, float, np.ndarray]` (clipped, threshold, mask); `damage.add_clicks(x, samplerate, seed, per_minute=40, widths=(1, 32), gains=(4, 8, 16)) -> tuple[np.ndarray, list[Click], np.ndarray]`; `damage.Manifest` (pydantic, `extra="forbid"`: references with SHA-256, damaged files with SHA-256, per-file threshold or click list, seed); `benchmark_repair.run_ffmpeg(tool, src, dst, filter)`, `benchmark_repair.run_cathar(binary, src, dst, module)`, `benchmark_repair.find_cathar() -> Path | None` (`CUMPLE_CATHAR` or `shutil.which("cathar")`).

- [ ] **Step 1: Read the survey README for the input-SDR levels and the SQAM list**

Fetch `https://github.com/rajmic/declipping2020_codes` README (read only; the code is GPL and is not opened). Record the seven input-SDR levels it uses and the ten SQAM excerpt names in `scripts/make_repair_set.py`'s docstring with the read date. The plan's expectation from memory is 1, 3, 5, 7, 10, 15 and 20 dB; if the README says otherwise, the README wins and this plan is corrected in the same commit.

- [ ] **Step 2: Write the failing metric and damage tests**

```python
"""Metrics and synthetic damage with known answers; nothing here needs the Rust core."""

from __future__ import annotations

import numpy as np

from cumple.repair import damage, metrics


def tone(seconds=2.0, fs=48000, hz=440.0):
    t = np.arange(int(seconds * fs)) / fs
    return 0.5 * np.sin(2 * np.pi * hz * t)


def test_sdr_of_a_perfect_estimate_is_infinite_and_of_half_gain_is_six_db():
    x = tone()
    assert metrics.sdr_db(x, x) == np.inf
    assert abs(metrics.sdr_db(x, 0.5 * x) - 6.02) < 0.01


def test_clip_to_sdr_lands_within_a_tenth_of_a_db_and_returns_the_mask():
    x = tone()
    y, thr, mask = damage.clip_to_sdr(x, 5.0)
    assert abs(metrics.sdr_db(x, y) - 5.0) < 0.1
    assert mask.dtype == bool and mask.sum() > 0
    assert np.all(np.abs(y[mask]) == thr) and np.all(y[~mask] == x[~mask])


def test_add_clicks_is_seeded_and_only_touches_the_mask():
    x = tone()
    y1, clicks1, mask1 = damage.add_clicks(x, 48000, seed=7)
    y2, clicks2, mask2 = damage.add_clicks(x, 48000, seed=7)
    assert clicks1 == clicks2 and np.array_equal(y1, y2)
    assert np.all(y1[~mask1] == x[~mask1]) and 70 <= len(clicks1) <= 90  # 40 per minute on 2 s is about 1; use a 2-minute tone here


def test_delta_sdr_on_damaged_samples_only_ignores_the_rest():
    x = tone()
    y, _, mask = damage.clip_to_sdr(x, 3.0)
    assert metrics.delta_sdr(x, y, x, mask=mask) == np.inf
    assert metrics.delta_sdr(x, y, y, mask=mask) == 0.0


def test_residual_clicks_counts_missed_and_false():
    x = tone(seconds=10)
    y, clicks, _ = damage.add_clicks(x, 48000, seed=1, per_minute=60)
    missed, false = metrics.residual_clicks(x, y, [c.position for c in clicks], [c.width for c in clicks], threshold=4.0)
    assert missed == len(clicks) and false == 0
    missed, false = metrics.residual_clicks(x, x, [c.position for c in clicks], [c.width for c in clicks], threshold=4.0)
    assert missed == 0 and false == 0
```

Fix the click-count assertion to the tone length the test actually uses before running; the comment in the snippet is the reminder.

- [ ] **Step 3: Implement `metrics.py` and `damage.py`**

`sdr_db = 10 log10(sum(ref^2) / sum((ref - est)^2))`, `inf` when the residual energy is 0. `clip_to_sdr` bisects the threshold on `[0, max|x|]` until the SDR is within 0.05 dB of the target (at most 60 steps), then returns the hard-clipped signal, the threshold and `|x| >= thr`. `add_clicks` draws positions from `numpy.random.default_rng(seed)` at `per_minute * seconds` positions at least 2,048 samples apart, widths uniform in `widths`, each click a half-cosine burst of `gain * local_rms` (local RMS over 64 samples, as cathar's detector measures) added with a random sign; returns the list of `Click(position, width, gain)` and the boolean mask. `residual_clicks` re-runs the same local-RMS detector at `threshold` on the estimate and counts injected clicks still detected (missed) and detections outside the dilated click mask (false). `peak_error_db` is `20 log10(max|est[mask]| / max|ref[mask]|)`.

- [ ] **Step 4: Write the failing baseline tests**

```python
"""ffmpeg and cathar as subprocess baselines: when they are on the machine, they repair; when not, nothing here runs."""

import os
import shutil
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from cumple.io.ffmpeg import find_ffmpeg
from cumple.repair import damage, metrics
from scripts.benchmark_repair import find_cathar, run_cathar, run_ffmpeg  # scripts is importable in tests through conftest's sys.path entry; check and add if it is not

TOOLS = find_ffmpeg()
CATHAR = find_cathar()
needs_ffmpeg = pytest.mark.skipif(TOOLS is None, reason="ffmpeg is not on PATH")
needs_cathar = pytest.mark.skipif(CATHAR is None, reason="cathar is not on PATH and CUMPLE_CATHAR is unset")
FIXTURE = Path(__file__).parent / "fixtures" / "speech-librivox-3s.wav"


@pytest.fixture
def clipped(tmp_path):
    x, fs = sf.read(FIXTURE, dtype="float64")
    y, thr, mask = damage.clip_to_sdr(x, 5.0)
    p = tmp_path / "clipped.wav"
    sf.write(p, y, fs, subtype="FLOAT")
    return p, x, y, mask


@needs_ffmpeg
def test_ffmpeg_adeclip_improves_sdr_on_a_clipped_voice(clipped, tmp_path):
    p, x, y, mask = clipped
    out = run_ffmpeg(TOOLS, p, tmp_path / "out.wav", "adeclip")
    est, _ = sf.read(out, dtype="float64")
    assert metrics.delta_sdr(x, y, est) > 0.5


@needs_cathar
def test_cathar_declip_improves_sdr_on_a_clipped_voice(clipped, tmp_path):
    p, x, y, mask = clipped
    out = run_cathar(CATHAR, p, tmp_path / "out.wav", "declip")
    est, _ = sf.read(out, dtype="float64")
    assert metrics.delta_sdr(x, y, est) > 0.5
```

If the fixture (16 kHz mono 16-bit) clips to 5 dB SDR with no improvement from either tool, lower the assertion to `> 0.0` and record the measured figure in the commit message; a baseline that does not improve a 5 dB clip is a finding for REPAIR.md, not a reason to delete the test.

- [ ] **Step 5: Implement `benchmark_repair.py` and `make_repair_set.py`**

`make_repair_set.py`: reads `~/.cache/cumple/repair/reference/*.wav` (or `CUMPLE_REPAIR_SET`) plus the LibriVox chapter from `~/.cache/cumple/real-dialogue/librivox/` when present (decoded through `cumple.io.reader.read`), writes `damaged/<name>.clip<sdr>.wav` at each survey level and `damaged/<name>.clicks<seed>.wav`, and `manifest.json`. Refuses to run when the reference folder is empty and prints where to put the SQAM excerpts (named, with the survey URL, terms unread, nothing fetched).

`benchmark_repair.py`: `run_ffmpeg` builds the argv list the way `io/ffmpeg.py` does (`-nostdin`, `-v error`, `-protocol_whitelist file`, a timeout that kills, stderr capped), filter `adeclick` or `adeclip` at defaults, output `pcm_f32le`. `run_cathar` runs `cathar declick INPUT --out OUT` or `cathar declip INPUT --out OUT` with the same discipline and records `cathar --version`. For each damaged file and each tool: decode, compute ΔSDR(all), ΔSDR(damaged), residual clicks (click files), peak error (clip files), wall time. The RX columns read `rx8/<name>` when the folder exists and its manifest hashes match, else "not run (RX 8 outputs not present; see docs/repair/rx8-recipe.md)". Writes Markdown to stdout: a header with versions and the read dates, one table per damage type with a row per file and level and a column per tool, and a summary block with the per-tool means that `tests/test_repair_numbers.py` will pin in Task 6. Exits with a message and no output if ffmpeg or cathar is missing (`sys.exit`, as `benchmark_meters.py` does at its line 40).

- [ ] **Step 6: Build the cathar baseline, run the harness once, write the recipe**

```bash
cargo install --git https://github.com/vbasky/cathar --rev f2c2842f89084589d069e5a8a0b61311aa70d928 cathar-cli --locked
cathar --version
uv run python scripts/make_repair_set.py
uv run python scripts/benchmark_repair.py > docs/REPAIR.md
```

If `cargo install` fails on the pinned revision, record the error and build from a shallow clone with `cargo build --release -p cathar-cli` instead; the binary path then goes in `CUMPLE_CATHAR`. `docs/REPAIR.md` at this point has the ffmpeg and cathar columns filled, the cumple column "not run: build 1 Task 5" and the RX columns "not run". Write `docs/repair/rx8-recipe.md`: the two RX 8 modules, the factory preset names as read from the preset XML on Victor's machine (the recipe says which files it read and quotes the parameter names from the 02a report), Batch Processing steps, the input folder (`damaged/`), the output folder (`rx8/`), the naming RX uses, and the manifest table Victor fills with SHA-256 values.

- [ ] **Step 7: Run the suite, re-pin counts, commit**

Two tests are gated on ffmpeg (README's macOS and Windows "fewer" figures each go up by one; the cathar-gated test skips everywhere in CI and does not change those lines, which count only ffmpeg gating; say so in the README sentence if it now reads wrong).

---

### Task 2: The Rust workspace, the STFT, the wheel, CI

**Files:**
- Create: `Cargo.toml` (workspace), `crates/cumple-dsp/Cargo.toml`, `crates/cumple-dsp/src/lib.rs`, `crates/cumple-dsp/src/stft.rs`, `crates/cumple-dsp/src/module.rs`, `crates/cumple-dsp/THIRD_PARTY.md`, `crates/cumple-dsp-py/Cargo.toml`, `crates/cumple-dsp-py/pyproject.toml`, `crates/cumple-dsp-py/src/lib.rs`, `deny.toml`, `rust-toolchain.toml`
- Modify: `pyproject.toml` (extra, uv workspace and sources), `.github/workflows/tests.yml` (toolchain, cache, `--extra repair`, cargo steps), `.gitignore` (`target/`)
- Test: `crates/cumple-dsp/src/stft.rs` unit tests, `tests/test_repair_core.py`

**Interfaces:**
- Consumes: nothing from Task 1.
- Produces: Rust `Stft::new(n_fft: usize, hop: usize) -> Stft`, `Stft::n_frames(len) -> usize`, `Stft::analyze(&mut self, x: &[f64], out: &mut [Complex<f64>])` (frames by `n_fft / 2 + 1` bins, row major, periodic Hann, no padding: the first frame starts at sample 0, the last frame is the last that fits), `Stft::synthesize(&mut self, spec: &[Complex<f64>], out: &mut [f64])` (overlap-add with the window applied again and the COLA sum divided out); trait `Module` with `id`, `version`, `context_frames`, `latency_frames`, `process(&mut self, input: &[f64], output: &mut [f64])`, `flush(&mut self, output: &mut [f64]) -> usize`, `report(&self) -> Report`; `Report { events: Vec<Event>, counters: Vec<(String, f64)> }`; Python `cumple_dsp.__version__`, `cumple_dsp.core_version()`, `cumple_dsp.Stft(n_fft, hop)` with `analyze(x: float64[n]) -> complex128[frames, bins]` and `synthesize(spec, length) -> float64[length]`.

- [ ] **Step 1: Workspace, toolchain, deny**

Root `Cargo.toml`: `[workspace] resolver = "3" members = ["crates/cumple-dsp", "crates/cumple-dsp-py"]`, `[workspace.package] edition = "2024" rust-version = "1.87" license = "MIT" repository = "https://github.com/victor10days/cumple"`, `[workspace.dependencies] rustfft = "6" realfft = "3"`, release profile `lto = "thin"`. `rust-toolchain.toml`: stable with `clippy` and `rustfmt`. `deny.toml`: the licence allowlist from the spec; `cargo deny check licenses` must pass.

- [ ] **Step 2: Write the failing STFT tests in Rust and in Python**

Rust (`stft.rs`, `#[cfg(test)]`): a 4,096-sample 440 Hz sine at 48 kHz through `analyze` at `n_fft = 1024, hop = 256` has its largest bin at round(440 / 48000 * 1024) = 9 in every frame; analyze then synthesize reproduces the input within 1e-10 from sample `n_fft` to `len - n_fft`; a signal shorter than `n_fft` yields zero frames and `synthesize` of zero frames writes zeros.

Python (`tests/test_repair_core.py`, `needs_core`):

```python
def test_stft_matches_scipy_within_tolerance():
    import cumple_dsp
    from scipy.signal import ShortTimeFFT
    from scipy.signal.windows import hann

    fs, n_fft, hop = 48000, 1024, 256
    rng = np.random.default_rng(0)
    x = rng.standard_normal(fs) * 0.1
    ours = cumple_dsp.Stft(n_fft, hop).analyze(x)
    sft = ShortTimeFFT(hann(n_fft, sym=False), hop=hop, fs=fs, fft_mode="onesided")
    theirs = sft.stft(x)  # (bins, frames) with scipy's centred framing
    # Align scipy's centred frames to ours (first frame at sample 0): scipy frame k covers samples k*hop - n_fft//2 ...; ours covers k*hop ...
    k0 = (n_fft // 2) // hop
    common = min(ours.shape[0], theirs.shape[1] - k0)
    np.testing.assert_allclose(ours[:common].T, theirs[:, k0 : k0 + common], atol=1e-9, rtol=0)
```

If scipy's framing offset is not an integer number of hops for this `n_fft` and `hop` (it is here: 512 / 256 = 2), the test picks values where it is; the point is the numerics, not scipy's padding convention.

- [ ] **Step 3: Implement `stft.rs` and `module.rs`**

Plan the forward and inverse transforms once in `new` (`realfft::RealFftPlanner`), keep scratch buffers, apply the periodic Hann window on analysis and synthesis, and divide by the window-squared overlap sum computed once (constant away from the edges for hop = n_fft / 4; at the edges divide by the partial sum, never by zero). `module.rs` is the trait and the `Report` types from the spec plus a `Chunker` helper used by the Python side's tests: given `context_frames` and a block, it calls `process` on `context + block + context` and copies out the centre.

- [ ] **Step 4: The bindings crate and the wheel**

`crates/cumple-dsp-py/pyproject.toml`: `[build-system] requires = ["maturin>=1.7,<2"] build-backend = "maturin"`, `[project] name = "cumple-dsp"`, `requires-python = ">=3.12"`, `dependencies = ["numpy>=2.0"]`, `[tool.maturin] module-name = "cumple_dsp" features = ["pyo3/abi3-py312"]`. `Cargo.toml`: `crate-type = ["cdylib"]`, `pyo3` with `extension-module` and `abi3-py312`, the `numpy` crate, `cumple-dsp = { path = "../cumple-dsp" }`. `src/lib.rs`: `#[pymodule] fn cumple_dsp` with `__version__`, `core_version()` and `Stft` (`analyze` releases the GIL with `py.allow_threads` around the transform, output allocated once as a `PyArray2<Complex64>`).

Root `pyproject.toml`:

```toml
[project.optional-dependencies]
repair = ["cumple-dsp"]

[tool.uv.workspace]
members = ["crates/cumple-dsp-py"]

[tool.uv.sources]
cumple-dsp = { workspace = true }
```

`uv sync --extra repair` then builds the wheel; `uv run python -c "import cumple_dsp; print(cumple_dsp.__version__, cumple_dsp.core_version())"` prints `0.1.0 0.1.0`.

- [ ] **Step 5: CI**

`tests.yml`, in the matrix job after `uv sync --group dev`: `dtolnay/rust-toolchain@stable`, `Swatinem/rust-cache@v2`, `uv sync --group dev --extra repair`, then `cargo fmt --all -- --check`, `cargo clippy --workspace --all-targets -- -D warnings`, `cargo test --workspace`, `cargo install cargo-deny --locked` (or the `EmbarkStudios/cargo-deny-action`) and `cargo deny check licenses`; `uv run pytest` as before. `release.yml` is untouched: the frozen apps sync `--extra app` only and never see the extension. Check `uv.lock` after the sync and commit it.

- [ ] **Step 6: Run everything, commit**

`cargo fmt`, `cargo clippy`, `cargo test`, `cargo deny`, ruff, `uv run pytest` (the new Python test runs locally with the wheel built), re-pin counts, commit.

---

### Task 3: De-click and Interpolate, ported from cathar

**Files:**
- Create: `crates/cumple-dsp/src/declick.rs`, `crates/cumple-dsp/src/inpaint.rs`
- Modify: `crates/cumple-dsp/src/lib.rs`, `crates/cumple-dsp-py/src/lib.rs` (the `Declick` class), `crates/cumple-dsp/THIRD_PARTY.md`
- Test: Rust unit tests in both files; `tests/test_repair_declick.py`

**Interfaces:**
- Consumes: `Module`, `Report` from Task 2; `damage.add_clicks`, `metrics` from Task 1; `find_cathar`, `run_cathar` from Task 1.
- Produces: Rust `Declick::new(threshold: f64, window: usize, method: DeclickMethod, iterations: u32) -> Declick` implementing `Module` with `context_frames() == 4096`; `inpaint_gap(signal: &mut [f64], start: usize, len: usize, iterations: u32)` in place; `DeclickMethod::{Ar, Cubic}`; Python `cumple_dsp.Declick(samplerate, threshold=10.0, window=64, method="ar", iterations=3)` with `context_frames`, `latency_frames`, `process(block) -> ndarray`, `flush() -> ndarray`, `report() -> dict` (`{"clicks": n, "positions": [...], "widths": [...], "linear_fallbacks": n}`).

- [ ] **Step 1: Write the failing Python tests**

```python
"""De-click: the port matches upstream cathar within tolerance and touches nothing outside the clicks."""

CATHAR = find_cathar()


@needs_core
def test_declick_removes_injected_clicks_and_leaves_the_rest_alone():
    import cumple_dsp
    x, fs = sf.read(FIXTURE, dtype="float64")
    y, clicks, mask = damage.add_clicks(x, fs, seed=3, per_minute=200)
    m = cumple_dsp.Declick(fs)
    est = chunked(m, y[:, None], block=8192)[:, 0]  # the test helper feeds blocks and drains flush
    missed, false = metrics.residual_clicks(x, est, [c.position for c in clicks], [c.width for c in clicks], threshold=10.0)
    assert missed <= len(clicks) // 10
    dilated = damage.dilate(mask, 8)
    np.testing.assert_allclose(est[~dilated], y[~dilated], atol=1e-9)
    assert metrics.delta_sdr(x, y, est) > 3.0
    assert m.report()["clicks"] >= len(clicks) * 0.9


@needs_core
@needs_cathar
def test_declick_matches_upstream_cathar_within_tolerance(tmp_path):
    import cumple_dsp
    x, fs = sf.read(FIXTURE, dtype="float64")
    y, clicks, mask = damage.add_clicks(x, fs, seed=3, per_minute=200)
    p = tmp_path / "clicks.wav"; sf.write(p, y, fs, subtype="FLOAT")
    up, _ = sf.read(run_cathar(CATHAR, p, tmp_path / "up.wav", "declick"), dtype="float64")
    est = chunked(cumple_dsp.Declick(fs), y[:, None], block=8192)[:, 0]
    assert abs(metrics.delta_sdr(x, y, est) - metrics.delta_sdr(x, y, up)) < 0.1
    boundary = boundary_mask(len(y), block=8192, context=4096)
    assert np.max(np.abs(est[~boundary] - up[~boundary])) < 1e-3
    assert np.max(np.abs(est[boundary] - up[boundary])) < 1e-2


@needs_core
def test_block_size_does_not_change_the_result():
    import cumple_dsp
    x, fs = sf.read(FIXTURE, dtype="float64")
    y, _, _ = damage.add_clicks(x, fs, seed=5, per_minute=200)
    a = chunked(cumple_dsp.Declick(fs), y[:, None], block=8192)
    b = chunked(cumple_dsp.Declick(fs), y[:, None], block=65536)
    np.testing.assert_allclose(a, b, atol=1e-6)
```

`chunked`, `boundary_mask` and `damage.dilate` are small helpers written in this task (`tests/repair_helpers.py` and `damage.py`). Note the per-minute figure: the 3 s fixture needs a high rate to carry about ten clicks; the cathar CLI writes 16-bit WAV by default, so compare after reading both at float64 and expect its quantisation inside the 1e-3 bound (16-bit is 1.5e-5); if the CLI writes float, nothing changes.

- [ ] **Step 2: Port `inpaint.rs`**

Translate cathar's `inpaint_gap`, `estimate_ar_known`, `levinson`, `coef_autocorr`, `solve_gap` and `solve_spd_banded` to f64 slices operating in place, with `AR_ORDER = 32`, `MAX_SOLVE = 2048` and the linear pre-fill exactly as upstream; the file header names the source. Rust tests: a gap of 200 samples cut from a 440 Hz sine at 48 kHz is refilled within 1e-3 after 3 iterations; a gap longer than `MAX_SOLVE` is filled linearly and reported as such; out-of-range spans leave the buffer unchanged.

- [ ] **Step 3: Port `declick.rs`**

Translate `declick_with_method`, `local_rms` and `cubic_interpolate` to f64, operating on `input` and writing `output`, then wrap in a `Module` whose `process` runs the whole-chunk algorithm on `context + block + context` (the shoulder pad `half.clamp(2, 8)` and the gap growth stay as upstream), records each gap's start and length into the report, and counts linear fallbacks. Rust tests: the same local-RMS values as a direct numpy computation on a short vector (write the expected numbers into the test); a single-sample click at 20 times local RMS in a sine is detected and refilled within 1e-3; a clean sine passes through unchanged.

- [ ] **Step 4: The Python class, mutation check, commit**

Add `Declick` to the bindings (one `declick::Declick` per channel, `process` releases the GIL, output allocated once per call). Prove the fidelity test can fail: temporarily flip the sign in the cubic fill or shift the gap start by one sample, run `tests/test_repair_declick.py`, see the upstream comparison fail, revert, record the failing figure in the commit message. Run the full checks, commit.

---

### Task 4: De-clip (A-SPADE and cubic), ported from cathar

**Files:**
- Create: `crates/cumple-dsp/src/declip.rs`
- Modify: `crates/cumple-dsp/src/lib.rs`, `crates/cumple-dsp-py/src/lib.rs` (the `Declip` class), `THIRD_PARTY.md`
- Test: Rust unit tests; `tests/test_repair_declip.py`

**Interfaces:**
- Consumes: `Stft` and `Module` from Task 2; `damage.clip_to_sdr`, `metrics` from Task 1.
- Produces: Rust `Declip::new(threshold: f64, method: DeclipMethod) -> Declip` with `context_frames() == 4096`, `DeclipMethod::{Spade, Cubic}`; Python `cumple_dsp.Declip(samplerate, threshold=0.95, method="spade")`, same surface as `Declick`; `report()` gives `{"runs": n, "longest_run": n, "peak_in": x, "peak_out": x, "iterations_mean": x}`.

- [ ] **Step 1: Write the failing Python tests**

The same three shapes as Task 3: (a) a clipped fixture at 5 dB input SDR gains at least 2 dB ΔSDR(all) and the output equals the input outside the clipping mask dilated by 1,024 samples within 1e-9 (A-SPADE rewrites whole frames; the dilation is the frame length, as the spec says); the restored peak is within 3 dB of the reference's peak over the mask; (b) upstream cathar `declip` at its default 0.95 threshold on a file clipped at exactly 0.95 of full scale (so both see the same mask) matches within 0.1 dB ΔSDR and the same 1e-3 and 1e-2 sample bounds; (c) block size 8,192 against 65,536 within 1e-4 (A-SPADE per chunk is expected to differ more than De-click does across block sizes; if 1e-4 fails, measure, record the figure in REPAIR.md's tolerance note and set the bound to what was measured times two, never silently).

- [ ] **Step 2: Port `declip.rs`**

Translate `declip_spade` (the ADMM loop, the hard-threshold on the Gabor coefficients with relaxation every `RELAX_BY = 2` iterations, the projection onto the clipping-consistent set, `MAX_ITER = 100`, the stopping rule on the residual against the signal energy), `frame_starts`, and the cubic fill with its 4-sample shoulders, onto the shared `Stft` (n_fft 1024, hop 256). Where cathar builds its own Hann frames, use `Stft` and note in the file header that the frame normalisation differs by the COLA constant; the fidelity test bounds the effect. Rust tests: a clipped 440 Hz sine at 0.5 full scale recovers its peak within 1 dB; a signal with no sample at or above the threshold passes through untouched (upstream's early return); a chunk shorter than one frame passes through untouched.

- [ ] **Step 3: The Python class, mutation check, commit**

As Task 3 Step 4. The mutation: drop the clipping-consistency projection for one run and watch the upstream comparison fail.

---

### Task 5: The runner, parameters, chains, presets, receipts, the CLI

**Files:**
- Create: `src/cumple/repair/params.py`, `src/cumple/repair/chain.py`, `src/cumple/repair/runner.py`, `src/cumple/repair/receipt.py`, `src/cumple/repair/presets/declick.yaml`, `src/cumple/repair/presets/declip.yaml`, `src/cumple/repair/presets/declick-declip.yaml`
- Modify: `src/cumple/repair/__init__.py`, `src/cumple/cli.py`, `README.md` (the command list and "Honest limits"), `CONTRIBUTING.md` (set up: Rust, `--extra repair`), `AI_USAGE.md`
- Test: `tests/test_repair_chain.py`, `tests/test_repair_runner.py`, `tests/test_cli_repair.py`

**Interfaces:**
- Consumes: `cumple_dsp.Declick`, `cumple_dsp.Declip`; `iter_blocks`, `probe`, `DEFAULT_BLOCK_FRAMES` from `io/reader.py`; `measure` from `meters/measure.py`; the write discipline of `fix.py`.
- Produces: `params.DeclickParams(threshold: float = 10.0 (ge 1, le 100), window: int = 64 (ge 8, le 1024), method: Literal["ar", "cubic"] = "ar", iterations: int = 3 (ge 1, le 10))`, `params.DeclipParams(threshold: float = 0.95 (ge 0.1, le 1.0), method: Literal["spade", "cubic"] = "spade")`, both `extra="forbid"`; `params.MODULES = {"declick": DeclickParams, "declip": DeclipParams}`; `chain.Chain(id, summary, steps: list[ChainStep])`, `chain.parse(text) -> Chain` (one-line form), `chain.load(path) -> Chain` (YAML), `chain.dump(chain) -> str`, `chain.presets() -> dict[str, Chain]`, `chain.resolve(text_or_id) -> Chain`; `runner.repair_file(src, chain, dst, residual=None) -> RepairResult(dst, receipt_path, reports, changed: bool)`; `receipt.write(path, ...)` and `receipt.Receipt` (pydantic); `cli.repair`.

- [ ] **Step 1: Write the failing tests**

Chain: `parse("declick(threshold=12),declip()")` gives two steps with the right params; `parse("declick(foo=1)")` raises `ValueError` naming `foo`; `dump(parse(t))` round-trips through `load`; a preset YAML with an unknown key fails to load with the key named; the three built-in presets load; a user preset in a temporary `XDG_CONFIG_HOME` overrides a built-in with the same id (follow how `specs` finds user profiles).

Runner (`needs_core`): the clicked fixture through `declick` gives a copy whose SHA-256 differs, a receipt beside it with the chain, the two version strings, the input SHA-256, both `measure()` summaries and one report; `dst == src` raises; `dst` a directory raises; a 2-channel WAV built in the test has each channel repaired independently (clicks injected only in channel 1 leave channel 0 bit-identical); `--residual` output equals input minus output within 1e-9; an input with no clicks gives `changed == False` and no file written; the temporary file never survives a failure (patch the writer to raise mid-way and assert the directory is clean).

CLI (`CliRunner`): `cumple repair clicks.wav --chain "declick()" --out out.wav` exits 0, prints the copy and the receipt path and the click count; with `--preset declick` the same; with a chain naming an unknown module exits 2; with `--out` equal to the input exits 2; on a clean file exits 1 with "nothing to change"; without the extension (monkeypatch `cumple.repair.available` to `False`) exits 2 and the hint contains `uv tool install` and `[repair]` with the brackets intact (escape rich markup, the Silero lesson); `--list-presets` names the three built-ins.

- [ ] **Step 2: Implement `params.py`, `chain.py`**

The one-line grammar: `name(k=v, k=v)` steps separated by commas, values parsed by pydantic from strings; whitespace free. YAML form:

```yaml
id: declick-declip
summary: Clicks first, then clipped peaks, at cathar's defaults.
steps:
  - module: declick
    params: { threshold: 10.0, window: 64, method: ar, iterations: 3 }
  - module: declip
    params: { threshold: 0.95, method: spade }
```

- [ ] **Step 3: Implement `runner.py` and `receipt.py`**

The block loop: a ring per module holding the last `context` frames of its own output (so chained modules see repaired context) and a one-block lookahead read ahead from `iter_blocks`, so each `process` call receives `prev_context + block + next_context`; the last block is padded with zeros to the right and the padding is dropped on write. Open the output with `sf.SoundFile(..., subtype=info.subtype, format=info.container)` as `fix.apply` does; clip to `[-1, 1]` only for integer subtypes. `measure()` runs on the source before and on the copy after, with the default arguments. The receipt is written last; the temporary name and `os.replace` are copied from `fix_file`, not re-invented.

- [ ] **Step 4: Implement `cli.repair`, docs, commit**

Mirror `fix`'s structure and messages. README gains `repair` in the command list, a "Repair" section with the install route, the two modules, the chain forms and the receipt, and an "Honest limits" line: two modules, PCM only, no metadata copy, numbers in `docs/REPAIR.md`. CONTRIBUTING gains the Rust toolchain line and `uv sync --extra repair`. AI_USAGE records the run and this build. Run everything, re-pin counts, commit.

---

### Task 6: cumple in the harness, `docs/REPAIR.md` pinned, the roadmap

**Files:**
- Modify: `scripts/benchmark_repair.py` (the cumple column through `repair_file`), `docs/REPAIR.md` (regenerated), `docs/ROADMAP.md` (R10 to building, then merged in the receipt), `site/index.html` only if a figure is quoted there (none is planned)
- Create: `tests/test_repair_numbers.py`, `docs/graph-runs/2026-10-08-rx-parity-landscape/06-build-1-notes.md` (what was measured, the mutation figures, any tolerance that had to move and why)

**Interfaces:**
- Consumes: everything above.
- Produces: `docs/REPAIR.md` with all five columns (cumple, ffmpeg, cathar, RX 8 De-click, RX 8 De-clip) filled or "not run"; `tests/test_repair_numbers.py`.

- [ ] **Step 1: Write the failing pin test**

Parse the summary block and the tables as `test_site_numbers.py` does; assert each summary mean equals the mean of its column within 0.005; `needs_core` and `needs_ffmpeg`: re-run the fixture damaged with seed 3 through `declick` and assert ΔSDR(all) matches the pinned "fixture" row within 0.05 dB; assert the file contains no "not checked" and the RX columns say "not run" or carry numbers.

- [ ] **Step 2: Add the cumple column, regenerate, pin**

`uv run python scripts/benchmark_repair.py > docs/REPAIR.md`. The header states: versions (cumple, cumple_dsp, ffmpeg, cathar commit), the reference set present (LibriVox only, or with SQAM), the seeds, the tolerances from the spec's scoring rule and whether each was met. If a tolerance was not met, the number stays and the build is not done: fix the port or write the reason in `06-build-1-notes.md` and bring it to Victor.

- [ ] **Step 3: Roadmap and notes, commit**

R10 to `building` with the branch name. Run everything, re-pin counts, commit.

---

### Task 7: The whole-branch review and the receipt

- [ ] A fresh context reviews the branch diff against the spec's scoring rule and this plan's constraints (as the Silero run's `03b-branch-review.md` did), with the harness output and the mutation figures in hand.
- [ ] Open the pull request from the branch (title: one sentence; body from the receipt's "What shipped"); subscribe to it; drive CI to green on the three runners.
- [ ] After green checks: `docs/graph-runs/2026-10-08-rx-parity-landscape/05-receipt.md` gains the PR link under "What shipped" and a "Build 1" section with what was measured; `docs/ROADMAP.md` R10 to `merged` with the PR number and the receipt path. Commit on the same branch before merge, as the earlier runs did.
