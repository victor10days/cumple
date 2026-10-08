# 03b Skeptic: the build-1 repair foundation plan

Date: 2026-10-08.

Reviewed: `docs/superpowers/plans/2026-10-08-repair-foundation.md` against its spec, the run's 01 and 04, the code it touches, cathar at f2c2842 (read through `gh api` only) and numpy re-expressions of cathar's two algorithms. The worktree was left unchanged apart from this file (`git status` shows only it; `uv run` created the git-ignored `.venv/`).

## Inputs read

- The plan, the spec, `01-frame.md`, `04-recommendation.md` (sections 3, 4, 5, 7, 10, 11), the three receipts, the Silero `03-skeptic.md`, the devils-advocate skill and references.
- cumple: `pyproject.toml`, `.gitignore`, both workflows, `fix.py`, `io/reader.py`, `specs/registry.py`, `benchmark_meters.py`, `fetch_real_dialogue.sh`, `conftest.py`, `test_counts.py`, `test_site_numbers.py`, the count pins, ROADMAP R10, the fixture.
- cathar at f2c2842: root `Cargo.toml`, `deny.toml`, licence files, tree, `restore.rs`, `inpaint.rs`, `declip.rs`, `util.rs`, `audio.rs`, `lib.rs`, `golden.rs`, the CLI's `Cargo.toml`, `main.rs`, `banner.rs`.
- The survey README (not its code) and companion page; PyO3 CHANGELOG, FAQ, `marker.rs` at v0.29.3; rust-numpy 0.29.0; crates.io and PyPI JSON; cargo-deny and uv docs; `ffmpeg -h filter=adeclick|adeclip`.
- Scratch (`plan-skeptic/` in the session scratchpad): `declick_bound.py`, `drift_long.py`, `spade_chunk.py` (cathar's detector and `declip_spade` in numpy f32) and a uv workspace mirroring Task 2.
- Side effect to report: the first `uv lock` in that scratch workspace ran maturin's metadata hook without cargo, and maturin bootstrapped a Rust toolchain into `~/Library/Caches/puccinialin` (473 MB). Nothing was deleted. Separately, `~/.rustup` and `~/.cargo` appeared at 14:18 today from a process outside this review; `cargo` is not on this shell's PATH.

## Steelman

The shape is right: the harness and both baselines come before any DSP, the compiled core sits behind an extra with skip gates, writes copy `fix_file`'s discipline, ported files carry their notice, and each port task ends with a mutation check. Tolerances are numbers, RX columns say "not run", and chunking is named as the risk. What nobody did is run cathar's two algorithms at the parameters the plan chose; most of what follows comes from doing that.

## Concerns

### 1. De-click at cathar's defaults can never detect a click

Severity: Critical, blocking. Framework: confidence without correctness ("provably correct, or does it look correct?").

What I see: `local_rms` (restore.rs 171 to 194) averages 64 samples that include the sample tested, so |s|/rms can never exceed sqrt(64) = 8, and the detector fires on `> threshold * rms` with the CLI's fixed window 64 and default threshold 10.0 (main.rs 482, 1424). In exact arithmetic it never fires. Measured on the fixture with the plan's damage (200 per minute, seeds 3 and 5): max |s|/rms 4.42 and 4.30, zero samples above 10. cathar's own unit tests use threshold 5 with window 32 (lib.rs 183 to 198). Width matters as well: a click of width w that dominates its window reaches about sqrt(128 / w), so at threshold 4 only clicks narrower than about 8 samples show; in my implementation of Task 1's tone test, 3 of 10 injected clicks exceed 4x.

Consequences: Task 3's first test (90 % found, ΔSDR above 3) fails; the Rust test "a single-sample click at 20 times local RMS is detected" fails (7.4x at most); the upstream-match and block-size tests pass because both sides return their input, and the mutation check cannot fail; Task 1's `missed == len(clicks)` fails; both De-click columns read ΔSDR 0, so rule 1 passes without exercising the port, and Task 6 pins 0.00.

A smaller upstream effect: on 10 minutes of the LibriVox reference, cathar's f32 running sum goes negative 31,884 times and 32,034 samples cross 10x through rounding alone (152 runs, longest 3,140 samples, |s| at most 7.7e-4, energy share 1.3e-8). An f64 port will not reproduce those rewrites; they sit below the 0.1 dB rule.

Why it matters: the module would ship green with no evidence it detects anything: the Silero receipt's test that cannot fail, at the scoring rule.

What to do: write the bound into the spec and into `DeclickParams` (reject `threshold >= sqrt(window)` with that reason); pick a working default by measurement (5 at window 64 is nearest to upstream's own tests); pass it to cathar with `-t` in the harness and the baseline tests; give the tests damage this detector can see (widths 1 to 4, gain 16) while the harness keeps widths 1 to 32 and reports the miss rate as the naive detector's real weakness. Record the f32 drift in REPAIR.md as an upstream finding.

### 2. De-clip at 0.95 never sees the harness damage

Severity: Critical, blocking. Framework: inversion.

What I see: the fixture peaks at 0.232, and `clip_to_sdr` lands at thresholds 0.0073, 0.0218, 0.0361, 0.0501, 0.0700, 0.1001 and 0.1260 for 1 to 20 dB. `declip_with_method` returns its input when no sample reaches the threshold (declip.rs 58), so cathar's default 0.95 and cumple's `declip` preset are passthroughs. Task 1's cathar test gets ΔSDR exactly 0 and fails both `> 0.5` and the fallback `> 0.0`; Task 4 (a) fails; Task 4 (b) clips "at exactly 0.95 of full scale", which clips nothing here; the harness's cathar and cumple De-clip columns read 0 and rule 1 passes vacuously again. `DeclipParams` `ge 0.1` rejects five of the seven thresholds above, and a peak-normalised reference still needs 0.031 and 0.094 of peak at 1 and 3 dB.

Why it matters: the benchmark would publish "cumple matches cathar" for a module that never ran.

What to do: give every declipper the manifest's threshold (`cathar declip -t <thr>`, a per-file `declip(threshold=<thr>)` chain rather than the preset), written as the float32 repr so `|v| >= thr` holds on the stored samples; lower the range (1e-4, or relative to peak); Task 4 (b) uses the damaged file's own threshold.

### 3. The De-clip fidelity rule is unreachable as designed, and the port recipe misreads A-SPADE

Severity: Critical, blocking. Framework: pre-mortem.

What I see: `spade_chunk.py` reproduces `declip_spade` (two-sided 1024-point FFT, symmetric Hann, 1/sqrt(L) scale, per-frame top-k, ADMM, projection) whole-file and chunked, with the original signal as context, the most favourable case:

| input | block, context | ΔSDR whole | ΔSDR chunked | max diff beyond 1,024 of a boundary | within |
|---|---|---|---|---|---|
| fixture, 5 dB | 8,192, 4,096 | 7.71 | 7.71 | 0.0925 | 0.0293 |
| fixture, 10 dB | 8,192, 4,096 | 8.01 | 8.15 | 0.0309 | 0.0205 |
| fixture, 20 dB | 8,192, 4,096 | 7.91 | 7.91 | 0 | 0 |
| LibriVox 30 s, 5 dB | 262,144, 4,096 | 8.50 | 8.50 | 0.0018 | 0.0257 |
| LibriVox 30 s, 10 dB | 262,144, 4,096 | 9.89 | 9.89 | 0 | 0 |

Every run stopped at `MAX_ITER` 100, so the energy term the spec blames is inert; the coupling is iterated overlap-add carrying the chunk edge inward. At 8,192 the 1e-3 and 1e-2 bounds fail for a perfect port and the 0.1 dB rule fails at 10 dB; at the runner's real block the 1e-2 bound fails at 5 dB.

The recipe also departs from upstream: cathar's window is symmetric (util.rs 5 to 12 divides by size minus 1), its top-k runs over all 1024 complex bins with k = 1, 3, 5 (`k += RELAX_BY` every iteration, declip.rs 266; plan line 344 and spec line 39 say "every 2 iterations"), and its stopping residual lives in its own scaling. A one-sided periodic-Hann variant moved ΔSDR by +0.58, +1.31 and +0.60 dB on the fixture and -0.42 and +0.09 on LibriVox.

Two more: the projection returns every unclipped sample exactly, yet criterion 2 dilates by 1,024, which leaves 17 % of the fixture outside at 5 dB; and the De-click context arithmetic (spec line 42) ignores `inpaint_gap`'s AR window of max(4 len, 8 p, 1024) per side (inpaint.rs 37 to 42), so 4,096 covers gaps up to about 819 samples, not 2,048.

What to do (a spec change, Victor's): split rule 1 into port fidelity on the whole file (one `process` call over the whole signal; the port keeps cathar's two-sided FFT, window and scale) and chunking cost (cumple chunked against cumple whole at `DEFAULT_BLOCK_FRAMES`, context and tolerance chosen by measurement); drop 8,192-sample fidelity tests; test exact equality on unclipped samples; correct the relaxation sentence and the context arithmetic.

### 4. Task 2 cannot pass as written

Severity: Critical, blocking; each fix is small. Framework: "current releases" checked rather than assumed.

What I see:
- The scipy test: `p_min` is -1, so frame 0 is column 3, not `k0 = 2`, and the default `phase_shift=0` references phase to each slice's centre. As written, against a numpy STFT with the plan's conventions: max difference 12.1. With `phase_shift=None` and column `n_fft // (2 * hop) - sft.p_min`: 2.4e-15.
- pyo3 is 0.29.3. `allow_threads` became `detach` in 0.26 and 0.28 removed 0.26's deprecations; `marker.rs` at v0.29.3 has only `detach`.
- `extension-module` is deprecated; PyO3's FAQ says it "breaks binaries and tests" and points to maturin 1.9.4 or later. The plan enables it, pins `maturin>=1.7`, and runs `cargo test --workspace`, which links a test harness for the bindings crate. Not reproduced (no toolchain); the FAQ is the source.
- `cargo deny check licenses`: target-lexicon 0.13.5, a non-optional dependency of pyo3-build-config 0.29.3, is `Apache-2.0 WITH LLVM-exception`; cargo-deny treats an exception as a distinct licence, so the spec's allowlist fails. cathar's `deny.toml` lists it.
- The numpy crate is BSD-2-Clause (Toshiki Teramura, 2017), not MIT or Apache as the spec says; a wheel that links it carries that notice too.

What to do: fix the offset and phase; `py.detach`; drop `extension-module`, require maturin 1.9.4, run `cargo test -p cumple-dsp` (or `test = false` on the bindings lib); allow the exception; add rust-numpy's notice to `THIRD_PARTY.md`.

### 5. The extension goes stale silently, and `[repair]` compiles Rust on the user's machine

Severity: High, blocking for Tasks 3 and 4. Framework: environment gaps.

What I see: uv rebuilds a local or editable package only when `pyproject.toml`, `setup.py` or `setup.cfg` change (uv cache docs), and a workspace member installs editable (scratch lock: `source = { editable = "crates/b-py" }`). After Task 3's Rust edits, `uv run pytest` imports Task 2's binary, and the mutation checks of Tasks 3 and 4 run against an unmutated build.

Scratch mirror (hatchling root, maturin member, the extra, the sources): a fresh `uv lock` with the member's version dynamic (maturin's default; the plan's member names no version) took 2 min 26 s and bootstrapped Rust; with a static version, 5 ms. With a committed lock, `uv lock --check` took 5 ms. `uv pip compile "a[repair] @ git+file://..."` resolved the member to `git+...#subdirectory=crates/b-py`, so README's `uv tool install` route builds cumple-dsp from source (Rust, or a silent toolchain download). The built root wheel says `Requires-Dist: b-dsp; extra == 'repair'`, a bare name, and `cumple-dsp` is unregistered on PyPI (404): pip fails today, and a squatter could fill the name.

Tasks 1 (Step 6) and 2 need cargo on the executing machine; that install is Victor's decision and the plan does not say so.

What to do: `uv sync --extra repair --reinstall-package cumple-dsp` after every Rust change (or member `cache-keys` covering both crates' sources and `Cargo.lock`, verified); a static version in the member; README and the `RepairUnavailable` hint say `[repair]` compiles Rust; reserve the PyPI name or record the risk; list the toolchain as a precondition Victor approves.

### 6. The count bookkeeping and the runner list are wrong

Severity: High, non-blocking. Framework: "the step nobody read" (Silero receipt).

What I see:
- Task 1 adds one ffmpeg-gated test, not two (plan lines 21 and 174; "two" and "each go up by one" also disagree).
- Task 6's re-run is gated on ffmpeg for no stated reason: another skip on macOS and Windows.
- Three cathar-gated tests skip on every runner, so README's "CI runs N-29 of them on Ubuntu" becomes false while `tests/test_counts.py` line 33 forces `n - EBU_CASES`; that file is in no task's list.
- `release.yml` runs on this PR (its paths include `pyproject.toml` and `uv.lock`), four runners with macos-15-intel; Task 7 says three.
- `cargo install cargo-deny` compiles from source on three runners; once on Linux suffices.

What to do: count from the snippets; gate the re-run on `needs_core`; add a cathar constant beside `EBU_CASES`; name `release.yml` in Task 7.

### 7. Harness facts wrong or left open

Severity: Medium, non-blocking.

- The survey README names neither levels nor excerpts ("ten audio files with the seven input distortion levels"); rajmic.github.io/declipping2020 lists 1, 3, 5, 7, 10, 15, 20 dB and the ten instruments. The plan's values match; Step 1 should cite the page.
- SQAM is already here: `fetch_real_dialogue.sh` line 12 records the EBU terms ("R&D tool only"), line 49 fetches the set, and `~/.cache/cumple/real-dialogue/sqam/flac/` holds 71 files.
- cathar writes 32-bit float WAV (audio.rs 87 to 118).
- `benchmark_meters.py` line 40 is the CASES list; its exits are at 99, 147, 211, 309.
- cathar's A-SPADE on the 25.9-minute chapter: 133,603 frames, 1.09 GB per complex64 frame array, about four alive per iteration.
- The runner: a left context of the module's own output makes De-click detect on repaired samples where upstream detects on the original, and a chain's second module needs the first's output beyond the block. Say which approximation is chosen.
- `boundary_mask(48000, 8192, 4096)` leaves only the first 4,096 samples outside; Task 6 pins a "fixture" row the set never produces.

## Contradictions

- Spec 39 and plan 344 ("relaxation every 2 iterations") against declip.rs 266.
- Plan 344 ("differs by the COLA constant") against a symmetric window and two-sided top-k.
- Plan 311 (16-bit) against audio.rs.
- Spec section 5 ("terms are unread, so nothing fetches them") against `fetch_real_dialogue.sh` 12 and 49.
- Spec licences (numpy crate MIT or Apache) against BSD-2-Clause.
- Spec 42's 2,128 against inpaint.rs 40.
- Plan Step 1 ("the README wins") against a README holding neither list.
- Task 7's three runners against `release.yml`'s paths.
- Criterion 2 ("A-SPADE rewrites whole frames") against the projection, which keeps every unclipped sample.

## Unsupported claims

- Threshold 10.0 "typical 8.0 to 15.0", from cathar's docstring, never run.
- "A sign error or an off-by-one moves ΔSDR by whole dB": at the defaults nothing is detected or clipped, so no mutation moves anything.
- "`uv sync` works without Rust": true with a committed lock; a re-lock with a dynamic member version bootstraps Rust.
- "Read-only views in, the GIL released": unchecked; a channel of a C-order `(frames, channels)` array is strided, so each block is copied per channel.
- "A-SPADE couples frames through its energy term": it never converged within 100 iterations here.

## Verified

| Claim | Source | Result |
|---|---|---|
| Commit f2c2842, 2026-09-21 | `gh api .../commits/f2c2842...` | confirmed |
| edition 2024, rust-version 1.87 | cathar `Cargo.toml` | confirmed |
| MIT OR Apache-2.0, "The cathar Authors", two licence files | `Cargo.toml`, `LICENSE-MIT`, tree | confirmed |
| rustfft 6, realfft 3 | cathar `Cargo.toml` | confirmed |
| restore.rs 93 to 190 holds `declick_with_method`, `local_rms` | restore.rs 116 to 169, 171 to 194 | contradicted in detail: ends inside `local_rms`, omits `cubic_interpolate` (196 to 213) |
| inpaint.rs 286 lines, declip.rs 712 | `wc -l` | confirmed |
| `inpaint_gap`, `estimate_ar_known`, `levinson`, `coef_autocorr`, `solve_gap`, `solve_spd_banded` | inpaint.rs 18, 87, 110, 137, 150, 192 | confirmed |
| `AR_ORDER = 32`, `MAX_SOLVE = 2048`, linear pre-fill | inpaint.rs 10, 13, 25 to 34 | confirmed |
| De-click context 64 + 16 + 2,048 | inpaint.rs 37 to 42 | contradicted |
| pad `half.clamp(2, 8)`, 3 AR iterations | restore.rs 146, 153 | confirmed |
| CLI threshold 10.0, window 64 | main.rs 482, 1424 | confirmed |
| threshold 10 at window 64 detects | sqrt(64) = 8; measured max 4.42 | contradicted |
| `declip_spade` 1024, 256, `MAX_ITER` 100 | declip.rs 187 to 194 | confirmed |
| relaxation every 2 iterations | declip.rs 266 | contradicted |
| `frame_starts`, last frame flush | declip.rs 107 to 116 | confirmed |
| cathar frame equals a periodic one-sided Stft up to COLA | util.rs 5 to 12, declip.rs 196 to 243 | contradicted |
| De-clip default 0.95, early return | main.rs 507, declip.rs 58 | confirmed |
| cathar writes 16-bit | audio.rs 87 to 118 | contradicted (float32) |
| `cargo install ... cathar-cli --locked`, binary `cathar` | tree has `Cargo.lock`; CLI `[[bin]]` | confirmed |
| survey README lists levels, SQAM names | README | contradicted; companion page confirms the plan's values |
| ffmpeg 9.0.1 `adeclick`, `adeclip` | `ffmpeg -h filter=` | confirmed |
| `py.allow_threads` | PyO3 CHANGELOG, marker.rs v0.29.3 | contradicted |
| numpy crate MIT or Apache | rust-numpy 0.29.0 | contradicted (BSD-2-Clause) |
| deny allowlist suffices | target-lexicon 0.13.5; cargo-deny docs | contradicted |
| scipy alignment `k0 = 2` | run, scipy 1.18.1 | contradicted |
| extra in wheel metadata | scratch `uv build` | bare `Requires-Dist` |
| `cumple-dsp` on PyPI | PyPI JSON | 404 |
| 252 collected; five pins | `--collect-only`, `test_counts.py` | confirmed |
| fixture 16 kHz mono PCM_16, 3 s | `sf.info` | confirmed, peak 0.232 |
| `scripts` importable from tests | tests import `tests.*` from the root | confirmed |

## Verdict

**Rethink this**, in the scoring rule and the harness parameters; the architecture, crate layout and task order stand. Both modules run at defaults that touch none of the harness damage (concerns 1 and 2), so the fidelity rule would pass for two no-ops, while the one comparison doing real work, chunked A-SPADE against whole-file upstream, cannot meet its tolerances even for a perfect port (concern 3). Those need a spec amendment Victor approves: thresholds from the damage, fidelity measured whole-file, chunking cost measured separately. Concerns 4 to 6 are plan edits; 7 rides along. Checked hardest: the De-click bound (proved, then measured on the fixture and 10 minutes of the reference) and A-SPADE chunking (emulated at both block sizes).

Counts: Critical 4 (concerns 1 to 4), High 2 (5, 6), Medium 1 (7). Blocking: 1 to 5.
