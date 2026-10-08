# Repair foundation: design for build 1

Date: 2026-10-08. Source run: `docs/graph-runs/2026-10-08-rx-parity-landscape/` (sections 3, 4, 5, 7, 10 and 11 of `04-recommendation.md`; Victor's approval of path C in `05-receipt.md`). Roadmap item R10. The implementation plan is `docs/superpowers/plans/2026-10-08-repair-foundation.md`.

## Goal

`cumple repair <file> --chain "declick(),declip()" --out <copy>` writes a repaired copy of a PCM file through a compiled DSP core, leaves a sidecar receipt that says exactly what ran, and `docs/REPAIR.md` scores the two modules against ffmpeg and cathar on synthetic damage with a held clean reference, with RX 8 columns ready for Victor's Batch Processing outputs. The core is the one implementation that the desktop app and, later, the plugin will share.

## Non-goals for build 1

- No module beyond De-click (with Interpolate as its gap filler) and De-clip. cathar's `declip.rs` carries six methods; build 1 ports A-SPADE (the default, and the survey's preferred family) and the cubic fill (the cheap fallback cathar itself uses at file edges). Social sparsity, constrained OMP, NMF and the unfolded-ISTA method stay in cathar until the harness has RX scores to rank them against; each would need its own fidelity test, and the plan does not pay for four of them before one is scored.
- No change to any meter, check, profile, report or to `fix`. `measure()` is called by the repair runner, never modified.
- No editor, no plugin, no C ABI. The crate layout leaves room for both (see Architecture) and nothing more.
- No AR-residual click detection and no 4,000-sample Interpolate: build 2 (R11).
- No model weights, no network at run time.
- The frozen desktop apps do not carry the extension until build 5; `release.yml` is untouched.
- PySide6 replaces PyQt6 in a separate one-PR fix (R15), a precondition of the next release, not part of this build.

## Architecture

Three layers, one direction of dependency: the Rust core knows nothing about Python; the Python package imports the core only inside `cumple.repair`; the CLI and app call `cumple.repair`.

### 1. The core: `crates/cumple-dsp`

A pure Rust library crate, `MIT`, no C dependencies, in a Cargo workspace rooted at the repository (`Cargo.toml` at the root lists `crates/cumple-dsp` and `crates/cumple-dsp-py`; the plugin shell later adds a `capi` crate beside them). Edition 2024, `rust-version` 1.87, matching cathar so the port compiles unchanged where it is unchanged.

Contents:

- `stft.rs`: a streaming STFT and inverse STFT on `realfft` (3.x) and `rustfft` (6.x), f64 throughout. `Stft::new(n_fft, hop, Window::Hann)` with a periodic Hann window, one-sided spectra, overlap-add synthesis with the COLA normalisation for sqrt-Hann at 75 % overlap and Hann at hop = n_fft / 4; `analyze` and `synthesize` take slices and write into caller-owned buffers. It is checked against scipy's `ShortTimeFFT` (which runs on ducc0, BSD-3) within a stated tolerance, not for bit equality: 1e-9 absolute on unit-scale signals for the forward transform, and perfect reconstruction (analysis then synthesis) within 1e-10 for Hann at hop n_fft / 4 away from the edges.
- `module.rs`: the module contract, a trait:
  - `fn id(&self) -> &'static str` and `fn version(&self) -> &'static str`;
  - `fn context_frames(&self) -> usize`: how many samples of neighbouring audio the module needs on each side of a block to process it as if it had the whole file;
  - `fn latency_frames(&self) -> usize`: 0 for every build-1 module; reported so the runner and later the plugin can compensate;
  - `fn process(&mut self, input: &[f64], output: &mut [f64])`: input is one channel of one block plus its context on both sides; output is the same length; the runner keeps the centre;
  - `fn flush(&mut self, output: &mut [f64]) -> usize`: anything a latency-carrying module still holds; 0 in build 1;
  - `fn report(&self) -> Report`: what happened, as counts and positions (clicks repaired and where; clipped runs rebuilt, the longest run, the peak restored), serialised to JSON by the Python side and copied into the receipt.
  - Buffers are allocated once per module from `context_frames` and the block size; `process` allocates nothing per sample. "Allocation-free" means that, not that the Rust side never calls the allocator during setup.
- `declick.rs`: the port of `declick_with_method` and `local_rms` from cathar `restore.rs` (lines 93 to 190 at commit f2c2842), and `inpaint.rs` from cathar's `inpaint.rs` (286 lines; its AR estimate, Levinson recursion and banded solve already run in f64 upstream). Parameters: `threshold` in local-RMS multiples (cathar: 10.0 default, "typical 8.0 to 15.0"), `window` in samples (cathar's CLI fixes 64), `method` `ar` or `cubic`, `iterations` (cathar passes 3). cathar's `MAX_SOLVE = 2048` linear-fill fallback is kept in build 1 and named in the report when it fires, so build 2 can measure what raising it buys.
- `declip.rs`: the port of `declip_spade`, `frame_starts` and the cubic fill from cathar `declip.rs` (712 lines; A-SPADE over a 1024-sample Hann frame at hop 256, relaxation every 2 iterations, at most 100). Parameters: `threshold` as a linear sample value (cathar: 0.95), `method` `spade` or `cubic`. The port replaces cathar's private Hann frame and FFT calls with the shared `stft.rs` so the two modules share one transform; the fidelity test (below) bounds what that changes.
- `lib.rs`: re-exports; `THIRD_PARTY.md` beside `Cargo.toml` carries cathar's MIT text with "Copyright (c) The cathar Authors", the commit the port was taken from, and the list of ported functions. Every ported file starts with a comment naming its source file and commit.

Why chunked with context rather than whole-file: cumple's reader streams 262,144-frame blocks (`io/reader.py`, `DEFAULT_BLOCK_FRAMES`) in constant memory, and the plugin will stream too. A click or a clipped run is local; A-SPADE's ADMM in cathar couples frames across the whole file through its energy term and shared overlap-add, so the port runs it per chunk and the test suite measures the chunk-boundary cost against upstream instead of assuming it away. `context_frames` for De-clip is 4 frames (4,096 samples); for De-click it is `window + 2 * pad + MAX_SOLVE` (64 + 16 + 2,048 = 2,128), rounded up to 4,096 so both share one reader stride.

### 2. The bindings: `crates/cumple-dsp-py`

A PyO3 `cdylib` built by maturin into the Python distribution `cumple-dsp`, import name `cumple_dsp`, abi3 for CPython 3.12 and later. It exposes:

- `cumple_dsp.__version__` and `cumple_dsp.core_version()` (the crate versions, which go into receipts);
- `cumple_dsp.Stft(n_fft, hop)` with `analyze(x) -> complex128 (frames, bins)` and `synthesize(spec, length) -> float64`, for the tests and later the editor's tiles;
- `cumple_dsp.Declick(samplerate, threshold=10.0, window=64, method="ar", iterations=3)` and `cumple_dsp.Declip(samplerate, threshold=0.95, method="spade")`, each with `context_frames`, `latency_frames`, `process(block: ndarray[float64, (frames, channels)]) -> ndarray` that runs each channel through its own module instance, `flush() -> ndarray`, and `report() -> dict`.

Numpy arrays cross through the `numpy` crate as read-only views in and freshly allocated arrays out, one allocation per block. The GIL is released during `process`.

`pyproject.toml` at the root gains `[tool.uv.workspace] members = ["crates/cumple-dsp-py"]`, `[tool.uv.sources] cumple-dsp = { workspace = true }` and the extra `repair = ["cumple-dsp"]`. The dev group does not carry it, so `uv sync` still works on a machine without a Rust toolchain; CI runs `uv sync --group dev --extra repair` after installing stable Rust, and the tests that need the core skip when `cumple_dsp` is not importable, the way the Silero tests skip without onnxruntime. hatchling stays the build backend of `cumple` itself.

### 3. The Python side: `src/cumple/repair/`

- `params.py`: one pydantic model per module with `extra="forbid"`, ranges (`threshold` 1 to 100 for De-click, 0.1 to 1.0 for De-clip), units and help text, and a `module_id` and `module_version` read from the core at import; `ChainStep(module, params)` and `Chain(steps, id, summary)`. The JSON schema of these models is what the app's forms will read later.
- `chain.py`: parse the one-line form `declick(threshold=10),declip(threshold=0.95)` and the YAML form (the strict style of the specs profiles: unknown keys fail), round-trip between them, load built-in presets from `src/cumple/repair/presets/*.yaml` and user presets from `~/.config/cumple/repair/*.yaml` (a user preset overrides a built-in with the same id, as profiles do).
- `runner.py`: `repair_file(src, chain, dst, residual=None) -> RepairResult`. Reads with `iter_blocks` (float64, `DEFAULT_BLOCK_FRAMES`), keeps a context tail per module of `context_frames` on each side, feeds each block plus context to each module in chain order (modules are instantiated once per channel, chained in memory), writes the centre of each output block, and at the end drains `flush`. Writes as `fix.apply` does: same sample rate, channels, subtype and format; a temporary name beside the destination; `os.replace` once the copy is complete; refuses a destination that resolves to the source, a directory, or a file ffmpeg decoded (PCM only, as `fix`). Does not copy bext or iXML metadata (as `fix`; the CLI says so). `--residual` writes input minus output through the same path, which is the "output clicks only" view RX offers.
- `receipt.py`: the sidecar `<dst>.cumple-repair.json`: cumple version, `cumple_dsp` versions, the chain in YAML form and as parsed parameters, the input path and SHA-256, the output SHA-256, `measure()` summaries before and after (integrated loudness, true peak, sample peak, the clipping count cumple already reports), each module's `report()`, and wall time. The receipt is written after the copy is in place; a failure before that leaves no receipt and no copy.
- `metrics.py`: pure numpy, no extension needed: `sdr_db(reference, estimate)`, `delta_sdr(reference, damaged, estimate, mask=None)`, `residual_clicks(reference, estimate, positions, threshold)`, `peak_error_db(reference, estimate, mask)`. Used by the harness and by the tests.
- `__init__.py`: `available() -> bool` and `require()` that raises `RepairUnavailable` with the install route (`uv tool install "cumple[repair]"` from git, since cumple is not on PyPI; never `pip install`).

### 4. The CLI

`cumple repair PATH --chain TEXT | --preset ID --out PATH [--residual PATH] [--receipt PATH]` in `cli.py`. Exit codes as `fix`: 0 wrote the copy, 1 nothing to change (every module reports zero events and the output would equal the input; no copy is written), 2 an error (unreadable file, bad chain, missing extension, destination equals source). Output names the copy, the receipt, and a one-line summary per module from its report. `cumple repair --list-presets` prints the built-ins.

### 5. The harness

`scripts/make_repair_set.py`: builds `~/.cache/cumple/repair/` from references the user has put under `~/.cache/cumple/repair/reference/` (the ten SQAM excerpts the declipping survey names; their terms are unread, so nothing fetches them) plus the LibriVox chapter `scripts/fetch_real_dialogue.sh` already fetches. Damage, with fixed seeds recorded in a manifest JSON: hard clipping to the survey's input-SDR levels (the plan lists them from memory; the task reads the survey README and pins what it says), and clicks at known positions, widths 1 to 32 samples, amplitudes 4, 8 and 16 times the local RMS, 40 per minute. The manifest holds every reference SHA-256, every damaged file's SHA-256, the clipping threshold per file and the click positions.

`scripts/benchmark_repair.py > docs/REPAIR.md`: runs cumple (`cumple repair` with the built-in `declick` and `declip` presets), ffmpeg `adeclick` and `adeclip` at their defaults (version printed), cathar `declick` and `declip` at their CLI defaults from a binary built at the pinned commit (`cargo install --git https://github.com/vbasky/cathar --rev f2c2842f cathar-cli`), and reads RX 8 outputs from `~/.cache/cumple/repair/rx8/` when they exist, matched by file name against the manifest. Metrics per file and level: ΔSDR on all samples and on damaged samples only, residual click count and false detections (De-click), restored-peak error in dB (De-clip), wall time. The RX columns print "not run" when the folder is absent. The script refuses to write if ffmpeg or the cathar binary is missing, as `benchmark_meters.py` refuses without the EBU set, and prints what to install.

`tests/test_repair_numbers.py`: the tables in `docs/REPAIR.md` are parsed as `test_site_numbers.py` parses `BENCHMARK.md`; the summary lines must equal the table means; one short fixture (`tests/fixtures/speech-librivox-3s.wav`, damaged in the test with the harness's own functions and seed) is re-run through the core and its ΔSDR must match the pinned figure within 0.05 dB. This test skips without the extension.

`docs/repair/rx8-recipe.md`: for Victor: which RX 8 modules and factory presets (De-click "Default", De-clip "Default"; the recipe names the preset files it read), the input folder, the output folder, the file naming RX Batch Processing uses, and the SHA-256 manifest to fill in so the harness can refuse a mismatched set.

## Scoring rule for build 1

Build 1 is done when, on the harness set:

1. The port matches upstream cathar: for every damaged file, ΔSDR(all) of cumple's De-click and De-clip is within 0.1 dB of cathar's CLI output at the pinned commit, and the two outputs differ by at most 1e-3 sample-peak outside the chunk-boundary regions (the context stride) and by at most 1e-2 inside them. The tolerances are stated in `docs/REPAIR.md`; if the port cannot meet them, the receipt says what differs and why before any tolerance is widened.
2. No sample outside detected damage changes: with the manifest's damage mask dilated by the module's shoulder pad (8 samples for De-click, the frame length for De-clip), the output equals the input outside the dilated mask within 1e-9.
3. Every column of every table is a number or "not run"; no "not checked".
4. `uv run pytest` is green on all three runners with the extension built; `cargo test`, `cargo fmt --check` and `cargo clippy -- -D warnings` are green; ruff is clean; CI concludes `success`.

RX 8 is reported, not gated. From build 2 on, a module ships only if it beats ffmpeg and cathar on ΔSDR at every damage level.

## Licences

The core and bindings are MIT, as cumple is. Ported cathar code carries its notice (`THIRD_PARTY.md`, per-file headers) under cathar's MIT option. Dependencies: `rustfft` and `realfft` (MIT or Apache-2.0 per cathar's own `deny.toml` allowlist, re-read at task time from their crates), `pyo3` and `numpy` crates (MIT or Apache-2.0, re-read), maturin (MIT or Apache-2.0). `cargo deny check licenses` with an allowlist of MIT, Apache-2.0, BSD-2, BSD-3, ISC, Unicode and Zlib runs in CI so a transitive licence change fails the build. ffmpeg stays a subprocess (LGPL); cathar's CLI is a subprocess baseline only, never linked. No GPL code is read for the port.

## Where paths A and B would differ

If Victor chooses path A, sections 1 and 2 become a C++ library with nanobind and the module contract stays as written; the port becomes a translation and the fidelity tolerances must be re-derived. If Victor chooses path B, section 1 becomes `src/cumple/repair/core_numpy.py` with the same contract in Python, section 2 disappears, and the plugin milestone becomes an out-of-process front end. Nothing in sections 3 to 5 changes under either.

## Risks carried into the plan

- cathar's A-SPADE is whole-file; chunking changes results at boundaries. The fidelity test measures it; the tolerance is a number, not a hope.
- f32 upstream against f64 here: the 0.1 dB ΔSDR tolerance is wide enough for precision and narrow enough to catch a wrong port (a sign error or an off-by-one on a gap moves ΔSDR by whole dB on the harness set; this is an expectation, checked by mutation in the plan).
- Rust on three CI runners adds a toolchain install and a cache to `tests.yml`; `release.yml` is untouched.
- The SQAM excerpts may never be fetched; LibriVox alone is enough for the pinned numbers, and the tables say which references were present.
