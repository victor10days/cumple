# 03c Plan skeptic, second read: the repair foundation plan (build 1)

Date: 2026-10-08. A second, independent skeptic run by the cloud session in a fresh context, started before `03b-plan-skeptic.md` reached the branch and without reading it; it built the cathar CLI at the pinned commit and ran the plan's own recipes. Where the two reads agree (the detector bound, the De-clip threshold, the A-SPADE tolerances, the scipy offset, the stale extension), the findings were reached twice from different experiments. What only this read found: CI never runs the fidelity tests (concern 6), "exit codes as `fix`" is false (8), the click model is too heavy for an impulse detector (9), the SPDX ids in the allowlist (14). Kept verbatim below the header.


Date: 2026-10-08. Reviewed: `docs/superpowers/plans/2026-10-08-repair-foundation.md` against `docs/superpowers/specs/2026-10-08-repair-foundation-design.md`, the decision documents, the cumple code it builds on, and the cathar source it ports (shallow clone at commit f2c2842f). Read-only: nothing in the worktree was changed (`git status --short` empty at the end). Scratch scripts, a release build of the cathar CLI at the pinned commit, and two throwaway uv workspaces live under the session scratchpad `skeptic/`.

## Inputs read

- `docs/superpowers/plans/2026-10-08-repair-foundation.md` (whole), `docs/superpowers/specs/2026-10-08-repair-foundation-design.md` (whole)
- `docs/graph-runs/2026-10-08-rx-parity-landscape/04-recommendation.md` (sections 3, 5, 10, 11), `05-receipt.md`, `00-plan.md`
- `docs/superpowers/plans/2026-09-13-silero-vad.md` and `docs/graph-runs/2026-09-13-silero-vad/03-skeptic.md` (shape and the four classes it caught)
- cathar at f2c2842f: `Cargo.toml`, `crates/cathar/Cargo.toml`, `crates/cathar-cli/Cargo.toml`, `deny.toml`, `rust-toolchain.toml`, `LICENSE-MIT`, `LICENSE-APACHE` (head), `Cargo.lock` (the rustfft and realfft entries and their dependencies), `crates/cathar/src/restore.rs` 80 to 220, `crates/cathar/src/inpaint.rs` (whole), `crates/cathar/src/declip.rs` (whole), `crates/cathar/src/util.rs` (`hann_window`), `crates/cathar/src/audio.rs` 20 to 130, `crates/cathar/src/lib.rs` (the declick and declip tests, 178 to 212), `crates/cathar-cli/src/main.rs` 400 to 530 and 1400 to 1460
- cumple: `src/cumple/fix.py`, `src/cumple/io/reader.py`, `src/cumple/io/ffmpeg.py`, `src/cumple/cli.py`, `src/cumple/meters/measure.py` (160 to 215), `src/cumple/specs/registry.py`, `scripts/benchmark_meters.py` (head and its exits), `scripts/fetch_real_dialogue.sh` (the LibriVox line), `tests/conftest.py`, `tests/test_counts.py`, `tests/test_site_numbers.py`, `tests/test_ffmpeg_io.py` (head and the decorators), `tests/test_vad.py` (head), `tests/fixtures/NOTICE.md`, `pyproject.toml`, `uv.lock` (head and the cumple entry), `.github/workflows/tests.yml`, `.github/workflows/release.yml`, `packaging/cumple.spec`, `.gitignore`, `README.md` (install, the Tests line), `CONTRIBUTING.md` (the count), `docs/ROADMAP.md` (R10, R11, R15)
- The survey repository `rajmic/declipping2020_codes`: its README and the `Sounds` folder listing (read, nothing cloned; the code is GPL)
- The uv cache documentation (`docs/concepts/cache.md` from the uv repository), the PyO3 FAQ (`guide/src/faq.md`), the maturin configuration page (`guide/src/config.md`), all read from raw GitHub since the documentation hosts are blocked by the proxy

## Steelman

The plan is the right shape for this repository: the harness and the baselines come before any new DSP (the receipt's own ruling), every numeric claim is meant to be pinned by a test the way `BENCHMARK.md` and `DIALOGUE.md` are, the extension sits behind an extra so the base install and the frozen apps are untouched, writes copy `fix_file`'s temporary-name-then-`os.replace` discipline, and the port carries cathar's notice. The module contract (context, latency, process, flush, report) is what a streaming runner and a later plugin both need, and keeping the ADMM declipper per chunk with a measured boundary cost is the honest way to reconcile a whole-file algorithm with `iter_blocks`. The uv workspace wiring is sound: I verified that an extra pointing at a workspace member resolves even when cumple is installed from a git URL (check 11), so the install hint can work.

## Checks run

All from `/home/user/cumple` with `uv run python`, scripts under the scratchpad `skeptic/`.

1. Fixture: `tests/fixtures/speech-librivox-3s.wav` is 48,000 samples at 16 kHz, peak 0.2317, RMS 0.0405. `clip_to_sdr` as the plan specifies lands the seven survey levels at thresholds 0.0072 (1 dB) to 0.1258 (20 dB); the 5 dB level clips at 0.0362, which is 28.8 dBFS below full scale and 16.1 dB below the fixture's own peak, with 25.9 % of samples clipped.
2. cathar's `local_rms` (restore.rs 171 to 194) replicated in numpy: the window of sample `i` contains sample `i`, so `|x_i| / rms_i <= sqrt(64) = 8` for every sample. With the plan's clicks (half-cosine bursts, gains 4, 8, 16 times the clean local RMS, widths 1 to 32) the largest ratio any click reaches on the fixture is 7.05 (gain 16, width 1); at width 32 it is 2.0 for every gain. At the plan's default threshold 10 nothing is detectable; at the metric's threshold 4 only gains 8 and 16 at widths up to 8 are.
3. cathar CLI built at f2c2842f (`cargo build --release -p cathar-cli --locked`, 2 min 01 s; `cathar --version` prints `cathar 0.8.0`) run on the fixture with ten injected clicks (seed 3, the plan's recipe): `declick` at the default threshold 10 changed 0 samples; `--threshold 7` changed 0; `--threshold 3` changed 141 samples and moved ΔSDR by +0.00 dB. Output subtype is `FLOAT` (32-bit float WAV, audio.rs 113 to 118), 192,068 bytes.
4. The same binary on the 5 dB clipped fixture: `declip` at the default 0.95 changed 0 samples (the early return at declip.rs 58). With `--threshold 0.0362` it changed exactly the 12,422 clipped samples and gained +7.71 dB ΔSDR(all).
5. A faithful numpy port of `declip_spade` (`skeptic/spade.py`, f64, cathar's symmetric Hann, `k += 2` every iteration, full complex FFT, tie rule kept) on the 5 dB clip: +7.56 dB in 100 iterations, 0 unclipped samples changed, restored peak +1.98 dB above the reference's over the mask. Against the cathar CLI's own output (check 4) the port matches ΔSDR within 0.01 dB (+7.70 against +7.71) while the largest sample difference is 0.182 and 9,281 of the 12,422 clipped samples differ by more than 1e-3. Variants of the port, each against the f64 whole-file run: float32 arithmetic, largest difference 0.123, ΔSDR 0.03 dB lower; periodic instead of symmetric Hann, 0.114, ΔSDR 0.12 dB higher; chunked as the plan's runner would (block 8,192, context 4,096, repaired left context, raw lookahead, zero padding), 0.251 largest difference, 7,741 samples over 1e-3, the largest outside the boundary regions, ΔSDR +7.85 (0.29 dB off); block 65,536, 0.252; block 8,192 against 65,536, 3.05e-2.
6. ffmpeg 6.1.1 (the one on this machine) `adeclip` at defaults on the 5 dB clip: +2.57 dB; on the same file scaled so the clip level sits at 0.95, +2.60 dB (its threshold is relative). `adeclick` at defaults on the ten clicks: input SDR 0.25 dB, output 0.23 dB, change of 0.02 dB in the wrong direction.
7. scipy 1.18.1 `ShortTimeFFT(hann(1024, sym=False), hop=256, fs=48000, fft_mode="onesided")` on the plan's noise: `p_min` is -1, so `stft(x)` column `j` is slice `j - 1`; the slice covering samples 0 to 1023 is column 3, not the plan's `k0 = 2`. With the default `phase_shift=0` no column offset matches a plain windowed FFT (largest difference 9.5 to 12.4 at every offset 0 to 7; at offset 3 the odd bins carry the opposite sign). With `phase_shift=None` and offset 3 the difference is 2.4e-15. `scipy.fft` here is `_duccfft`, so the spec's "runs on ducc0" is right for this version.
8. `uv run pytest tests/test_ffmpeg_io.py --collect-only`: 31 items, 19 carry `needs_ffmpeg`, 1 carries `skipif(sys.platform == "win32")` (line 128). README's "19 fewer on macOS" and "20 fewer on Windows" are exactly those counts; `tests/test_counts.py` checks only `**Tests**: N` and `runs N-29 of them on Ubuntu`.
9. A throwaway uv workspace (`skeptic/pyo3ws`): root `foo` with `rs = ["foo-rs"]`, member `crates/foo-rs` built by maturin from a pyo3 0.27.2 cdylib with `extension-module` and `abi3-py312` and `[tool.maturin] features = ["pyo3/abi3-py312"]`. `uv sync --extra rs` built and installed it (16.8 s). Editing `lib.rs` (the function returns 2 instead of 1) and running `uv sync --extra rs` again: "Checked 2 packages", the import still returns 1. `uv sync --extra rs --reinstall-package foo-rs`: returns 2. The uv cache page confirms the rule: local directory dependencies are rebuilt only when `pyproject.toml`, `setup.py` or `setup.cfg` changes, unless `tool.uv.cache-keys` says otherwise.
10. Same workspace: `cargo test --workspace` linked and ran the test (it failed only because I had already changed 1 to 2); `cargo clippy --workspace --all-targets -- -D warnings` clean. The PyO3 FAQ now calls `extension-module` deprecated and recommends removing it with maturin 1.9.4 or newer. With the member's version made `dynamic = ["version"]`, `uv lock` and `uv sync` without the extra succeed with cargo removed from PATH (maturin reads Cargo.toml itself), and `uv sync` without the extra installs only `foo`.
11. A throwaway hatchling workspace (`skeptic/uvws`) committed to git and installed as `"foo[bar] @ git+file:///..."` into a fresh venv: both `foo` and the workspace member `foo-bar` installed (uv 0.11.32). The git install route resolves workspace sources.
12. `grep` for em and en dashes in the plan and the spec: none. "not checked" appears only where the rule is quoted (plan 20 and 407, spec 85).
13. The survey README (`rajmic/declipping2020_codes`): it says "seven input distortion levels" and "ten audio files" without any dB value or file name; the licence line says GPL-3.0; the metrics are named `dSDR_all`, `dSDR_clipped`, PEAQ, PEMO-Q, Rnonlin. The `Sounds` folder lists `a08_violin.wav`, `a16_clarinet.wav`, `a18_bassoon.wav`, `a25_harp.wav`, `a35_glockenspiel.wav`, `a41_celesta.wav`, `a42_accordion.wav`, `a58_guitar_sarasate.wav`, `a60_piano_schubert.wav`, `a66_wind_ensemble_stravinsky.wav` and `Sound_database.mat`.
14. `cli.py` `fix` (437 to 466): `Exit(2)` on any exception (the `cannot fix` print at 447 does not escape markup), `Exit(1)` when `fp.gain_db is None` ("no fix written"), `Exit(0)` when the plan says "already complies; nothing to change" (452 to 454), and after a write `Exit(0 if report.passed else 1)`.
15. `tests/__init__.py` exists and `tests/conftest.py` has no `sys.path` entry; pytest's prepend import mode therefore puts the repository root on `sys.path`, and `scripts/` has no `__init__.py`, so `from scripts.benchmark_repair import ...` resolves as a namespace package. The plan's hedge at line 119 is right either way.
16. `specs/registry.py` 28 to 30: `user_dir()` honours `XDG_CONFIG_HOME`; the preset override test can follow it as the plan says.
17. cathar `inpaint.rs` 36 to 42: `p = len.clamp(32, 128)`, `ctx = (len * 4).max(p * 8).max(1024)`, the AR estimate reads `ctx` samples on each side of the gap. For the longest solvable gap (2,048) that is 8,192 samples each side.
18. cathar `util.rs` 5 to 13: `hann_window` divides by `size - 1` (a symmetric window). `declip.rs` 266: `k += RELAX_BY` runs every iteration; 133 to 146: `hard_threshold_k` ranks all `L` complex bins and keeps ties at the cutoff; 255 to 263: the residual sums over all `L` bins of every frame; 73 to 83: `project_gamma` returns the observation unchanged for every sample below the threshold.
19. `benchmark_meters.py`: the refusals are `sys.exit` at lines 99, 147, 211 and 309; line 40 is the `CASES` table.

## Concerns

### 1. De-click at cathar's defaults cannot detect anything, so three of the plan's tests cannot do their job and the harness column is a no-op

Severity: Critical (blocking). Framework: "is this provably correct, or does it just look correct?"; the test that cannot fail.

What I see: the port keeps `local_rms` as upstream (plan 319) with `threshold=10.0, window=64` as the defaults (plan 261, spec 38, receipt). The sample under test sits inside its own 64-sample RMS window (restore.rs 171 to 194), so the ratio the detector compares against the threshold can never exceed sqrt(64) = 8 (check 2). The built cathar CLI confirms it: 0 samples changed at threshold 10 and at 7 on the plan's own click set (check 3). cathar's own tests use threshold 5 and window 32 (lib.rs 186, 194), never the CLI pair.

Why it matters: `test_declick_removes_injected_clicks_and_leaves_the_rest_alone` (plan 272 to 283) asserts `report()["clicks"] >= 9` and `delta_sdr > 3.0`; with the default parameters the module reports 0 and changes nothing, so it fails. `test_declick_matches_upstream_cathar_within_tolerance` and `test_block_size_does_not_change_the_result` then pass by comparing one untouched copy with another, and the Task 3 Step 4 mutation check ("flip the sign in the cubic fill or shift the gap start by one sample") cannot make them fail because no gap is ever filled; the plan would record a mutation figure that proves nothing. The Rust unit test "a single-sample click at 20 times local RMS in a sine is detected" (plan 319) fails for the same reason (20 / sqrt((63 + 400) / 64) = 7.4). In the harness, cathar's De-click column reads a no-op on every file, so "beats cathar on ΔSDR" (spec 88, R11) is met by doing nothing. The pydantic range `threshold ge 1, le 100` and the help text "typical 8.0 to 15.0" describe values the detector cannot reach above 8.

What to do: decide the detector before Task 3, in the spec. Either port it as it is and set defaults inside its reach (the metric's 4.0 on window 64 detects gains 8 and 16 up to width 8, check 2), with the bound written into the Rust test and the parameter help; or exclude the centre sample (or the centre run) from its own RMS window, which removes the bound, and then say in `THIRD_PARTY.md` and the file header that the detector differs from upstream by that line, with the fidelity test run against cathar at a threshold both can reach. Either way: make the clicks the harness injects detectable by the detector of record (concern 9), make the mutation check mutate the AR path that the default method uses (the cubic fill only runs at file edges, restore.rs 150 to 157), and require the mutation to produce a failing test before the commit, not a figure.

### 2. The De-clip fidelity tolerances cannot be met by any faithful port of A-SPADE

Severity: Critical (blocking for Task 4 and for the spec's scoring rule). Framework: boundary conditions; "the tolerance is a number, not a hope" (spec 100) turned on itself.

What I see: spec 83 and plan 340 require, against the cathar CLI at the pinned commit, ΔSDR(all) within 0.1 dB and sample differences of at most 1e-3 outside the chunk boundary regions and 1e-2 inside them, and 1e-4 between block sizes. Check 5: a faithful f64 port matches the CLI's ΔSDR within 0.01 dB while differing by up to 0.182 at the samples it rebuilds (9,281 of 12,422 clipped samples over 1e-3). The precision change alone (f32 to f64) moves samples by 0.123; the window the plan prescribes (periodic Hann in `Stft`, spec 29) against cathar's symmetric one (util.rs 6) moves them by 0.114; chunking with the plan's context moves them by 0.251, most of it outside the boundary mask, and moves ΔSDR by 0.29 dB; block 8,192 against 65,536 differs by 3e-2 against the plan's 1e-4. The ADMM with a hard threshold that keeps the `k` largest bins is sensitive to tiny magnitude changes: a different bin survives a tie, the dual variable diverges, and every rebuilt sample moves. All runs reached the 100-iteration cap (the residual rule at declip.rs 263 never fired), so "the stopping rule" is not what differs; the path is.

Why it matters: Task 4 as written ends with a failing fidelity test and a plan instruction (340) that forbids widening without a receipt. An implementer under pressure will either loosen the bound silently or abandon the port. The spec's rule 1 is also internally inconsistent for this module: the sample bounds measure chaos in the algorithm, not port errors, while ΔSDR measures what the harness cares about and is stable (0.01 dB between the port and the CLI).

What to do: rewrite scoring rule 1 for De-clip before Task 4. Fidelity is ΔSDR(all) and ΔSDR(clipped) against the cathar CLI within a tolerance derived from check 5's precision figure (0.1 dB holds for a whole-file run; the port must be run with a block at least the file length for this comparison, so chunking is not mixed into port fidelity), plus "every unclipped sample is unchanged, exactly" (concern 19). The chunk-boundary cost is a separate, reported number (ΔSDR of the chunked run against the whole-file run of the port; 0.29 dB measured here), not a gate. Drop the sample bounds for De-clip; keep them for De-click, where the fills are deterministic. The block-size test (c) compares ΔSDR within a measured tolerance, not samples within 1e-4. Keep the mutation check (dropping the consistency projection moves ΔSDR by whole dB). Also carry the port instructions in concern 12.

### 3. The harness runs cathar `declip` at a threshold it will never cross, and the baseline test cannot pass

Severity: Critical (blocking; Task 1 Step 4 fails as written). Framework: "which number does the first run print?"

What I see: `clipped` writes the fixture hard-clipped to 5 dB SDR, which is at 0.0362 (28.8 dBFS below full scale, check 1), and `run_cathar(..., "declip")` runs the CLI at its default `--threshold 0.95` (plan 159, spec 73). cathar's `declip_with_method` returns the input unchanged when no sample reaches the threshold (declip.rs 58 to 60); check 4 shows 0 samples changed. `test_cathar_declip_improves_sdr_on_a_clipped_voice` asserts `> 0.5`; the plan's fallback at line 153 lowers it to `> 0.0`, which 0.0 also fails. The same applies to every row of `docs/REPAIR.md`: speech and the SQAM excerpts clipped to the survey levels sit well below full scale, so cathar's De-clip column is a column of zeros, and RX 8's De-clip factory preset, which also has an absolute threshold, would do the same on the `damaged/` folder. ffmpeg's `adeclip` detects relative to the window maximum and is unaffected (+2.57 dB either way, check 6).

Why it matters: the first measured number of build 1 would be a measurement of a parameter mismatch, not of a declipper; the "beats cathar" rule from build 2 would be met trivially; Victor's RX run would be wasted on files RX cannot see as clipped.

What to do: the manifest already records the clip threshold per file. Pass it: `cathar declip --threshold <thr>` and `cumple repair --chain "declip(threshold=<thr>)"` in the harness, and write "oracle threshold" in the table header. For RX, scale each damaged file so its clip level sits at a stated level near full scale (0.95, or whatever the De-clip factory preset assumes) and record the scale in the manifest, so the recipe's outputs can be scaled back before scoring. Fix the baseline test the same way (`run_cathar` takes the threshold; the fixture's 5 dB clip is scored with `--threshold thr`), and keep the `> 0.5` assertion: cathar gains +7.71 dB there (check 4).

### 4. The scipy STFT oracle test fails as written: wrong frame offset and a phase convention the plan did not know about

Severity: Critical (blocking for Task 2 Step 2; a few lines to fix). Framework: run the oracle before trusting it.

What I see: plan 200 to 217 aligns `ours[j]` with `theirs[:, j + 2]` on the reasoning "scipy frame k covers samples k*hop - n_fft//2". scipy's `stft(x)` starts at `p_min = -1` (check 7), so the slice centred at sample 512 is column 3. Independently, the default `phase_shift=0` references each slice's phase to its centre, which flips the sign of every odd bin relative to a plain FFT of the frame; no column offset matches within the plan's 1e-9 (largest difference 9.5 to 12.4 at every offset). With `phase_shift=None` and offset 3 the match is 2.4e-15.

Why it matters: the test is the only check that the Rust STFT is an STFT and not merely self-consistent; an implementer who sees it fail at every offset will suspect the Rust side and lose a day, or will "fix" the test by loosening it.

What to do: construct `ShortTimeFFT(..., phase_shift=None)` and take the frames with `sft.stft(x, p0=2, p1=2 + ours.shape[0])` (or compute the column offset as `2 - sft.p_min`). Keep `atol=1e-9`. Add one assertion on `sft.p_min` so a scipy change surfaces as a message, not a mystery.

### 5. `uv sync` and `uv run` do not rebuild the extension when Rust sources change, so every "edit Rust, run the suite" step in the plan tests stale code

Severity: High (blocking in effect for the mutation checks of Tasks 3 and 4). Framework: pre-mortem "the mutation check passes and nobody knows why".

What I see: check 9: after editing `lib.rs`, `uv sync --extra rs` reports "Checked 2 packages" and the import returns the old value; only `--reinstall-package` rebuilds. The uv cache page states the rule (rebuild on `pyproject.toml`, `setup.py`, `setup.cfg` changes only, unless `tool.uv.cache-keys` is set). The plan's loop (`uv run pytest` after each Rust change, 248, 323, 348; the mutation "temporarily flip the sign ... run tests ... see the upstream comparison fail") never rebuilds.

Why it matters: a mutation that does not change the installed module cannot fail a test; the plan would then record "the test cannot fail" (or, worse, record a pass and move on). The same applies to the fix after any failing fidelity test.

What to do: in `crates/cumple-dsp-py/pyproject.toml` add `[tool.uv] cache-keys = [{ file = "pyproject.toml" }, { file = "Cargo.toml" }, { file = "src/**/*.rs" }, { file = "../cumple-dsp/Cargo.toml" }, { file = "../cumple-dsp/src/**/*.rs" }]` and verify once (the uv page warns globs cost a directory walk; that is fine here). Until that is verified, every command in the plan that runs Python tests after a Rust change says `uv sync --extra repair --reinstall-package cumple-dsp` first. Add that line to CONTRIBUTING with the extra.

### 6. The fidelity tests never run in CI, so the scoring rule's first gate is enforced by nobody

Severity: High (non-blocking for the code, blocking for the claim "CI green proves the port"). Framework: inversion of "`uv run pytest` is green on all three runners".

What I see: every upstream comparison is `@needs_cathar` (plan 287, 340) and `tests.yml` as amended by Task 2 Step 5 installs Rust, builds the wheel, runs `cargo` checks and `uv run pytest`, but never installs cathar (plan 244). Plan 174 says so itself ("the cathar-gated test skips everywhere in CI"). The spec's scoring rule 4 says CI `success` is part of "done".

Why it matters: the port's fidelity would be checked only on the machine that wrote it, which is the pattern the last three receipts call out. It also makes README's "runs N-29 of them on Ubuntu" wrong by the number of cathar-gated tests, since those skip on Ubuntu too and `test_counts.py` subtracts only the 29 EBU cases (check 8).

What to do: build cathar in CI on Linux at least: `cargo install --git https://github.com/vbasky/cathar --rev f2c2842f89084589d069e5a8a0b61311aa70d928 cathar-cli --locked` (verified to build in 2 min 01 s here, check 3) behind `actions/cache` on `~/.cargo/bin/cathar` keyed by the revision (`Swatinem/rust-cache` does not cache `~/.cargo/bin`), then `CUMPLE_CATHAR` for the tests. Then the Ubuntu count sentence stays true and the cathar-gated tests count toward "fewer on macOS and Windows" exactly like the ffmpeg-gated ones; say so in the Task 7 re-pin.

### 7. `context_frames == 4096` does not cover the AR estimate's reach, which the spec's formula leaves out

Severity: High (non-blocking for the plan's own clicks; blocking for the fidelity claim on longer gaps). Framework: boundary conditions.

What I see: spec 42 computes De-click's context as `window + 2 * pad + MAX_SOLVE` (2,128, rounded to 4,096). `inpaint_gap` reads `ctx = max(4 * len, 8 * p, 1024)` samples on each side of the gap for the AR estimate (inpaint.rs 37 to 42, check 17): 1,024 for any gap up to 256 samples, and 8,192 for the longest gap it solves (2,048). A gap of a few hundred samples near a chunk edge therefore sees truncated context in the port and full context upstream; the AR coefficients differ, and so does the fill.

Why it matters: the fidelity test on the plan's clicks (widths up to 32, gaps of at most 48 with shoulders) cannot see this, so the port would ship with a context that is right for the test set and wrong for the module's own parameter range; build 2 raises `MAX_SOLVE` toward 4,000 and the gap widens.

What to do: state the real bound in `declick.rs` (`pad + max(4 * gap, 8 * p, 1024)` on each side) and either set `context_frames` to cover the longest gap the module accepts (8,192 + 8 + 64 for `MAX_SOLVE = 2048`), or cap the gap the chunked module will AR-fill at what 4,096 covers (about 800 samples) and name the cap in the report when it fires, the way linear fallbacks are named. Add one Rust test with a 1,500-sample gap placed within 2,000 samples of a chunk edge, compared against the whole-file call.

### 8. "Exit codes as `fix`" describes codes `fix` does not use

Severity: Medium (non-blocking; a sentence in the spec and one line in the plan). Framework: "as X does" where X does not.

What I see: spec 67 and plan 369: 1 for "nothing to change". `fix` exits 0 on "already complies; nothing to change" (cli.py 452 to 454, check 14) and 1 only when gain alone cannot do it, or when the re-check after a write fails. The CLI test "on a clean file exits 1 with 'nothing to change'" is internally consistent but the sentence "as fix" is false, and "mirror fix's structure" (plan 391) would copy `fix`'s unescaped `cannot fix` print (cli.py 447) that the plan elsewhere says to escape.

What to do: say the codes without the comparison (0 wrote, 1 nothing to change, 2 error), and in the plan name the one difference from `fix`. Keep `escape()` on every print that interpolates an exception or a path.

### 9. The click model makes every baseline look useless, including the ones that work

Severity: Medium (non-blocking; changes what `REPAIR.md` will mean). Framework: "what would the first table say and would it be believed?"

What I see: ten clicks at gains up to 16 times local RMS and widths up to 32 samples put the fixture at 0.25 dB input SDR (check 6): the bursts carry as much energy as three seconds of speech. ffmpeg's `adeclick` at defaults changes nothing (0.02 dB the wrong way); cathar cannot see them (concern 1). RX's De-click and ffmpeg's `adeclick` are impulse detectors for a few samples; a 32-sample half-cosine at 16 times RMS is a dropout for Interpolate (build 2), not a click.

What to do: split the damage by width: clicks at widths 1 to 8 for De-click (with the detector of record able to see them), longer bursts in a separate table reserved for build 2's Interpolate, and state ΔSDR(damaged) per width. Record the measured `adeclick` figure in `REPAIR.md` either way.

### 10. Task 1 Step 1 reads a README that has nothing the step wants

Severity: Medium (non-blocking; the step has a clear replacement). Framework: checkable claim, checked.

What I see: plan 41 and spec 71 and 04 section 5 say the survey README names the seven input-SDR levels and the ten SQAM excerpts. It does neither (check 13): it says "seven input distortion levels" and "ten audio files" with no values and no names. The names are the file names under `Sounds/` (a08 to a66 by SQAM track); the levels are in the paper.

What to do: point the step at the paper (Záviška, Rajmic, Mokrý, Průša, "A survey and an extensive evaluation of popular audio declipping methods", 2020, open access) for the levels, and at the `Sounds` listing for the ten names; keep the plan's expectation (1, 3, 5, 7, 10, 15, 20) as the thing to confirm. Correct section 5 of `04-recommendation.md` in the receipt (its "named in the README" is wrong).

### 11. The test-count arithmetic in the plan is off by what it adds

Severity: Medium (non-blocking; the five pins are tested, the "fewer" sentences are not). Framework: count what the plan adds against the rule the repository uses.

What I see: README's "19 fewer on macOS" is the number of `needs_ffmpeg` items in `test_ffmpeg_io.py` and "20 fewer on Windows" adds the one `win32` skip (check 8). Plan 174 says "Two tests are gated on ffmpeg" and in the same sentence that the second is cathar-gated; Task 1 adds one ffmpeg-gated test, Task 6 adds another (`needs_core and needs_ffmpeg`, plan 407) that the re-pin instruction at 415 does not mention. The cathar-gated tests change the Ubuntu sentence too (concern 6).

What to do: in Global Constraints say the rule as the repository applies it (macOS: items gated on ffmpeg; Windows: those plus items gated on `win32`), and count per task: Task 1 adds one to each, Task 6 adds one to each, plus the cathar-gated tests if CI does not build cathar. If a test needs both ffmpeg and the core, it still counts once.

### 12. The A-SPADE port instructions in the plan describe an algorithm that is not cathar's

Severity: Medium (non-blocking once concern 2 is fixed; blocking for "port fidelity" as a phrase). Framework: every number attributed to upstream, checked against the line.

What I see (check 18): plan 344 and spec 39 say "relaxation every `RELAX_BY = 2` iterations"; the code adds 2 to `k` every iteration (declip.rs 266). The plan says to replace cathar's frames with the shared periodic-Hann `Stft` and note that "the frame normalisation differs by the COLA constant"; the window itself differs (symmetric, util.rs 6), which moves rebuilt samples by 0.114 (check 5). `hard_threshold_k` ranks all 1,024 complex bins with the mirror half present and keeps ties at the cutoff (133 to 146), so "keep the k largest" on a one-sided spectrum keeps a different set for odd `k`; the residual sums over all 1,024 bins of every frame (255 to 263) and is compared with `1e-3 * ||x||` in absolute terms, so a one-sided unscaled transform changes when the loop stops. `frame_starts` appends a frame flush to the end when the length is not on the hop grid (107 to 116); the plan's `Stft` does not.

What to do: write the port instructions from the code: symmetric Hann of length 1,024 for this module (a `Window::HannSymmetric` in `Stft`, or the module's own window), `k += 2` each iteration, the hard threshold applied with multiplicity 2 on interior bins and the tie rule kept, the residual weighted the same way and scaled by `1/sqrt(L)` so the stopping rule matches upstream, and the flush frame when the chunk length is off the grid. Then the fidelity figure in concern 2 measures precision and chunking only.

### 13. The runner's context semantics are inconsistent for chains and at the file ends, and the fidelity test cannot see it

Severity: Medium (non-blocking). Framework: trace one block through two modules.

What I see: plan 387: each module keeps a ring of its own output as left context ("chained modules see repaired context") and takes the raw lookahead block as right context. For the second module the right context is audio the first module has not processed yet, so the chain's right context is unrepaired while its left is repaired; the whole-file reference for a chain (upstream run twice) has both sides repaired by the first module. The last block is zero-padded, so upstream's end-of-file branch (cubic fill when `gap_end < n` fails, restore.rs 150 to 157) is unreachable for the port at the true end, and block 0's left context is zeros where upstream has none. The fidelity tests are single-module and their boundary mask covers only interior block edges.

What to do: either give the lookahead to the whole chain (run module 1 on the lookahead block early, which doubles its work on one block) or state that chains see raw right context and test it with a two-module chain against the whole-file reference, with the cost reported. Treat the file head and tail as boundary regions in `boundary_mask`, and make the last-block padding carry a length so modules can take upstream's edge branch.

### 14. Smaller inaccuracies that would send an implementer the wrong way

Severity: Low (non-blocking). Framework: line-by-line against the sources.

- Plan 311: "the cathar CLI writes 16-bit WAV by default": it writes 32-bit float (audio.rs 113 to 118; check 3 shows `FLOAT`). The plan's hedge covers it; delete the sentence.
- Spec 38: "lines 93 to 190": `DeclickMethod` starts at 93, `declick_with_method` is 116 to 169, `local_rms` 171 to 194, `cubic_interpolate` 196 to 213.
- Plan 159: "`sys.exit`, as `benchmark_meters.py` does at its line 40": the exits are at 99, 147, 211 and 309 (check 19).
- Plan 231 to 238 and 225: the member's `[project]` has no `version`; give it `version = "0.1.0"` (static metadata keeps `uv lock` from invoking maturin; both work, check 10) and make `__version__` read it.
- Spec 92: "Unicode" and "BSD-2", "BSD-3" are not SPDX ids; `deny.toml` needs `Unicode-3.0` (cathar's own line 25; `unicode-ident` arrives through `syn` under `pyo3-macros`), `BSD-2-Clause`, `BSD-3-Clause`, and `[licenses] version = 2`. The rustfft and realfft trees (Cargo.lock: num-complex, num-integer, num-traits, primal-check, strength_reduce, transpose, version_check, autocfg, libm, bytemuck) are all MIT or Apache-2.0 or both, so the list passes once the ids are right.
- Plan 225: pyo3's FAQ now deprecates `extension-module` and asks for maturin 1.9.4 or newer without it; the plan pins `maturin>=1.7,<2`. `cargo test --workspace` linked fine here with pyo3 0.27 (check 10), so this is a floor to raise, not a failure.
- Plan 244: `cargo install cargo-deny --locked` compiles cargo-deny on every runner on every run unless cached; `EmbarkStudios/cargo-deny-action` on Linux alone is enough, licences do not vary by runner.
- Spec 29 `Stft::new(n_fft, hop, Window::Hann)` against plan 187 `Stft::new(n_fft, hop)`; spec 62 `residual_clicks(reference, estimate, positions, threshold)` against plan 37 with `widths`. Pick one.
- Plan 79: a 2-second tone at 40 clicks per minute carries one click; the comment says so. Write the test for the length it uses before running it.
- Plan 340 and spec 84: dilating the clip mask by the frame length for De-clip is unnecessary; A-SPADE returns the observation for every unclipped sample (declip.rs 75 to 83; 0 unclipped samples changed in every run of check 5). Assert equality with no dilation; it is a stronger test for free.
- Plan 9: "ffmpeg 9.0.1" is the version on Victor's Mac; CI's Ubuntu has 6.1.1 (check 6) and macOS and Windows have none. The header line in `REPAIR.md` prints what ran, which is right; the tech-stack line should not promise a version.

## Contradictions

- Plan 174: "Two tests are gated on ffmpeg" and, in the same sentence, one of them is gated on cathar (check 8: one).
- Spec 67 "exit codes as `fix`" against cli.py 452 to 454, where `fix` exits 0 on nothing to change (check 14).
- Spec 29 says the `Stft` is a periodic Hann; plan 344 ports A-SPADE onto it; cathar's window is symmetric (util.rs 6), and the measured effect is 0.114 in sample value (check 5).
- Spec 39 and plan 344 "relaxation every 2 iterations" against declip.rs 266, where `k` grows by 2 every iteration.
- Spec 42 "`context_frames` for De-click is window + 2 pad + MAX_SOLVE" against inpaint.rs 40, where the AR estimate reads up to 8,192 samples on each side.
- Spec 83 "ΔSDR within 0.1 dB and samples within 1e-3" for De-clip against check 5, where the CLI and a faithful port agree on ΔSDR within 0.01 dB and disagree on 9,281 samples by more than 1e-3.
- Plan 153 "lower the assertion to `> 0.0`" against the measured 0.0 (check 4), which `> 0.0` also rejects.
- Plan 311 "the cathar CLI writes 16-bit WAV" against audio.rs 117 to 118 and check 3 (`FLOAT`).
- Plan 41 and 04 section 5 "the README names the levels and the excerpts" against check 13 (it names neither).
- Plan 211 "scipy frame k covers samples k*hop - n_fft//2 ..." with `k0 = 2` against check 7 (`p_min = -1`, column 3, and a phase convention on top).

## Unsupported claims

- "`cumple_dsp.Declick(fs)` ... `assert m.report()["clicks"] >= len(clicks) * 0.9`" (plan 283): with the stated defaults the figure is 0 (checks 2 and 3).
- "the two outputs differ by at most 1e-3 sample-peak outside the chunk-boundary regions" for De-clip (spec 83): refuted for this algorithm by check 5.
- "block size 8,192 against 65,536 within 1e-4" for De-clip (plan 340): measured 3.05e-2 (check 5). The plan allows measuring here; the number should be measured, recorded and explained, as it says.
- "`context_frames == 4096` covers De-click's worst case" (spec 42): refuted by inpaint.rs 40 (check 17) for gaps over about 800 samples.
- "the restored peak is within 3 dB of the reference's peak" (plan 340): supported on the fixture at 5 dB (+1.98 dB, check 5); untested at 1 dB and 3 dB, where the survey's own tables show A-SPADE overshooting. Keep it, but per level.
- "a clipped fixture at 5 dB gains at least 2 dB" (plan 340): supported (+7.56 dB whole-file, +7.85 chunked, check 5) provided the module is run at the clip threshold, not at 0.95 (concern 3).
- "`uv sync --extra repair` then builds the wheel" (plan 240): supported (check 9), with the rebuild caveat of concern 5.
- "`uv tool install "cumple[repair]"` from git" (spec 63): supported for the resolution (check 11); it still needs a Rust toolchain on the user's machine, which the hint should say in the same breath.
- "a 200-sample gap cut from a 440 Hz sine at 48 kHz is refilled within 1e-3 after 3 iterations" (plan 315): plausible (a sine is an AR(2) process and cathar's own test refills a 480-sample gap in a chord within 0.15 RMS); I did not run it.
- "cathar's A-SPADE couples frames across the whole file through its energy term" (spec 42): the energy term sets `eps` (declip.rs 229 to 230), and no run in check 5 ever reached it; the coupling that matters is the per-frame hard threshold's sensitivity, which the chunked runs show. Harmless as a sentence, wrong as a diagnosis.

## Verdict

**Do not ship as written.** The architecture is right and I could not break the parts of it I could exercise: the uv workspace, the git install route, the STFT numerics, the write discipline, the preset override path. What fails is the plan's own test of its two deliverables. De-click is ported with defaults under which the detector cannot fire (a bound in the arithmetic, confirmed on the built CLI), so its tests cannot fail and its harness column is a no-op. De-clip is held to sample tolerances that a faithful port of this ADMM cannot meet while the harness metric it serves agrees within 0.01 dB, so its tests cannot pass. The harness runs cathar's declipper below its threshold on every file, so the first measured number is a parameter mismatch. The scipy oracle test is misaligned, and the loop the plan prescribes for fixing any of this does not rebuild the extension it tests.

None of these moves the design away from path C; all of them change what the spec calls "done". Fix 1 to 5 in the spec and the plan before Task 1 runs (3 and 4 are Task 1 and Task 2 failures on the first day; 1 and 2 decide what the port is; 5 decides whether any later fix can be seen). 6 and 7 can be fixed in the plan now or carried as receipts, but the receipt must then say that CI does not check port fidelity and that the De-click context is right only up to a stated gap. 8 to 13 are sentences; 14 is a list.

Counts: Critical 4 (concerns 1 to 4), High 3 (5 to 7), Medium 6 (8 to 13), Low 1 (14, ten items). Blocking: 1, 2, 3, 4, 5.
