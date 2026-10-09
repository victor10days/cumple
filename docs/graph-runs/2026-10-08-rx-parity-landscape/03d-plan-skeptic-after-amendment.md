# 03d Skeptic: the amended build-1 plan

Date: 2026-10-08.

Reviewed: commit ed39f6e (the amended plan and spec, and the diff from c9b5517) against 03b, 03c, the unadopted `pr29-amendment-alt`, cathar at f2c2842 through `gh api`, numpy re-expressions of cathar's detector, `inpaint_gap` and `declip_spade`, and a scratch uv and Cargo mirror of Task 2 (pyo3 0.29.3, numpy crate 0.29.0, maturin 1.15.0, uv 0.12.23, cargo on PATH throughout). The worktree was left unchanged apart from this file.

## Steelman

The amendment fixed what both reads proved: thresholds come from the damage, De-clip is scored on ΔSDR with exact equality on unclipped samples, the port recipe matches `declip.rs` line by line, the scipy oracle aligns to 2.4e-15, and the Rust and uv wiring (static member version, `py.detach`, no `extension-module`, `cargo test -p`, the LLVM exception) builds as written apart from one name. The mutation checks now bite: in my emulation, shifting the AR gap start by one sample moves the fixture output by 9.7e-3 to 5.5e-2 and ΔSDR by 0.46 to 2.24 dB, and dropping the projection breaks exact equality. What survives is narrower: several new numbers were each measured once, under one condition, and promoted to gates on every file.

## Earlier concerns after the amendment

| Concern | Status | Checked at |
|---|---|---|
| 03b-1 De-click never detects | partly fixed: default 5 and the bound; test damage calibrated at threshold 4 (concern 2) | spec 41; plan 38, 286, 317 |
| 03b-2 De-clip at 0.95 | fixed | plan 157 to 161, 168, 396; spec 76 |
| 03b-3 De-clip rule, recipe | partly fixed: whole-file split from chunking, recipe from the code; 0.1 dB at the noise floor (concern 3) | spec 42, 86, 87; plan 379 |
| 03b-4 Task 2 cannot pass | fixed (scipy re-run 2.39e-15, mirror builds); one new compile error (concern 1) | plan 200, 219 to 225, 236, 250 |
| 03b-5 stale extension, Rust on install | partly fixed; relaxation checked with the wrong command (concern 7) | plan 16, 236 to 248, 265, 404 |
| 03b-6 counts, runners | partly fixed: Task 3 miscounted | plan 183, 269, 358, 442, 457 |
| 03b-7 harness facts | partly fixed: the 25.9-minute chapter is still read whole | plan 42, 166, 168, 282 |
| 03c-1 detector cannot fire | partly fixed, as 03b-1; mutation on the AR path | plan 358 |
| 03c-2 De-clip tolerances | partly fixed (concern 3) | spec 86 |
| 03c-3 cathar at 0.95 | fixed | plan 157 to 161 |
| 03c-4 scipy oracle | fixed | plan 219 to 225 |
| 03c-5 no rebuild | partly fixed (concern 7) | plan 16, 265 |
| 03c-6 CI never runs fidelity | partly fixed: cathar built on Ubuntu, nothing fails on a skip (concern 6) | plan 17, 269; spec 90 |
| 03c-7 De-click context | fixed (16,384); new edge divergence (concern 5) | spec 41; plan 350, 354 |
| 03c-8 exit codes | fixed | spec 70; plan 404 |
| 03c-9 click model | partly fixed: IMPULSE mostly invisible at 5 (concern 2) | plan 38; spec 74 |
| 03c-10 survey README | fixed | plan 42 |
| 03c-11 count arithmetic | partly fixed: Task 3 wrong | plan 22, 358 |
| 03c-12 A-SPADE recipe | fixed | plan 379; spec 42 |
| 03c-13 runner semantics | fixed | spec 63; plan 402, 422 |
| 03c-14 ten small items | fixed | spec 41; plan 9, 79, 168, 200, 236, 269, 375 |

## In the parallel amendment, not in the adopted one

| Item (alt) | Matters? |
|---|---|
| Rule 3 scored against the gaps the module reports | Yes: the fix for concern 4 |
| Click tests at widths 1 to 3, gain 32, with a visibility precondition | Yes: 100 % visible at threshold 5 on the fixture and a tone (concern 2) |
| Rule 0: cathar must change the file, or the comparison is vacuous | Medium: no adopted check flags a no-op baseline column |
| LibriVox as three 30 s excerpts | Medium: the chapter is 133,603 A-SPADE frames, 2.04 GiB per complex128 frame array, per level and tool |
| RX De-clip per clip level, threshold set in dBFS | Medium: the adopted recipe scales the plateau to 0.95 (-0.45 dBFS) under a "Default" with no preset file; factory thresholds here run from -0.25 dB ("Subtle Digital Clipping", which would see nothing) to -6.6 dB |
| Chunking test on the fixture tiled past `DEFAULT_BLOCK_FRAMES` | Low: a 65,536 block on 48,000 samples is one chunk |
| Explicit reinstall kept, checked with `uv run` | Medium (concern 7) |
| n-pass runner | No: the adopted runner states and measures its approximation |

## New concerns

### 1. Two steps fail as written (Critical, blocking; one line each)

Framework: confidence without correctness.

What I see: plan 250 puts `#[pymodule] fn cumple_dsp` in a crate that depends on `cumple-dsp`. pyo3's macro emits a module named after the function, which shadows the extern crate: in the mirror, `use mini_dsp::VALUE;` fails with E0659 ("ambiguous") and `mini_dsp::VALUE` with E0425; `::mini_dsp::VALUE` compiles and clippy is then clean. Plan 350 wants a 200-sample gap in a 440 Hz sine at 48 kHz "refilled within 1e-3 after 3 iterations". A line-by-line numpy port of `inpaint_gap` (its ridge and `r[0] *= 1 + 1e-6` included) leaves 6.4e-3 at amplitude 0.5, 1.3e-3 at 0.1. 03c called it plausible and did not run it.

Why it matters: Task 2 does not compile; Task 3 Step 2 fails for a faithful port and invites a "fix" to the port.

What to do: rename the dependency (`dsp = { package = "cumple-dsp", ... }`) or write `::cumple_dsp::`; bound the refill at 1e-2.

### 2. IMPULSE was calibrated at threshold 4 and is used at 5 (High, blocking before Task 1)

Framework: inversion (what does the first run print?).

What I see: plan 38 and spec 74 define IMPULSE as widths 1 to 8 at gains 8 and 16, "what the detector of record can see, measured in 03c". 03c measured that at threshold 4. At the amended 5 (cathar's exact window, 200 positions per cell, two half-cosine shapes, best sample of each click): widths 6 to 8 are never visible; 4 and 5 only at gain 16 with a Hann-shaped burst; width 2 at gain 8 at most 1 %; 30 to 38 % of the preset overall. At threshold 4 the set is visible to width 7, confirming 03c. With my `add_clicks` on the fixture (not the plan's random stream), the port found 1, 5, 7 and 1 of 10 clicks at four seeds.

Why it matters: Task 1's two click tests and Task 3's first test fail as written. The fallback (plan 112: narrow the preset) lands on width 1, since `ratios[c.position]` at a click's first sample passes 5 only there; widths 2 to 8 then sit in no table (BURST starts at 9).

What to do: before Task 1, take widths 1 to 3 at gain 32 with BURST from 4, or report widths 4 to 8 as invisible to the detector of record; define `position` as the peak; correct spec 74.

### 3. Rule 1's tolerances sit at the noise floor on short files (High, blocking for "done")

Framework: pre-mortem; one measurement promoted to a gate.

What I see: spec 86 gates every damaged file on De-clip ΔSDR within 0.1 dB, citing 03c's 0.01 dB (one file, one level). A faithful numpy A-SPADE (f64 gives +7.56 dB at 5 dB, 03c's figure) against the same code in float32, on the fixture at 1, 3, 5, 7, 10, 15 and 20 dB: 0.14, 0.21, 0.06, 0.01, 0.04, 0.10 and 0.44 dB apart; a 2^-50 relative nudge inside f64 moves ΔSDR by up to 0.24 dB. On SQAM 58 (16 s) and 66 (18 s) the spread is at most 0.06 and 0.08. De-click: spec 86 says cathar's f32 drift "stays under both bounds". Emulating cathar's f32 running sum, the 3 s fixture's pause gets spurious gaps in 5 of 8 seeds, and their fills differ from the f64 port by up to 1.2e-3. 03b measured drifted samples, not fills.

Why it matters: a correct port stops the build at Task 6 Step 2 on the fixture rows, and plausibly on the shortest SQAM tracks; Task 4 (b) tests only 5 dB, where the spread happened to be small.

What to do: derive the De-clip tolerance per file from measured spread (the port plus a few nudged runs; the CLI must fall inside), or gate only files of 15 s or more; for De-click, compare gap lists outside cathar's drift gaps and apply 1e-3 elsewhere. Run Task 4 (b) at all seven levels.

### 4. Rule 3 fails on the references, because threshold 5 sees isolated LSBs (High, blocking for "done")

Framework: inversion; one number changed, another rule broke.

What I see: spec 88 requires the De-click output to equal the input "outside the click mask dilated by the shoulder pad" within 1e-9, the injected mask (plan 310). A lone nonzero sample in digital silence has ratio exactly sqrt(64) = 8, so any threshold below 8 fires on it. Clean SQAM at threshold 5: 11 detections in 5 of 10 tracks (08, 18, 25, 41, 60), each one LSB (3.05e-5), and the port rewrites 1 to 17 samples there. At the old 10 this was impossible; the fixture has none (largest clean ratio 3.38), so no test sees it.

Why it matters: rule 3 fails for any faithful port, cathar included, on half the set; the same LSBs make `cumple repair --chain "declick()"` exit 0 on a clean file with sparse dither in its silences.

What to do: score locality against the gaps the module reports (the parallel wording), count other detections as false detections, and say so in the help and README.

### 5. `inpaint_gap` fills linearly at file edges, where cathar does not (High, blocking for Task 3)

Framework: line by line against the source.

What I see: plan 286 and 350 give `inpaint_gap(signal, start, len, iterations) -> Fill`, returning `Fill::Linear` "when the context would reach past the slice". cathar clips the context at the file and still solves AR (inpaint.rs 41 to 42). In `process_whole` the slice is the file, so a gap within about 1,032 samples of either end is filled linearly by the port and by AR upstream; `Edge` never reaches the function. Spec 41 says "past the context", the right rule.

Why it matters: the fidelity test passes or fails on where seed 3 drops a click (about one chance in three for ten clicks on 48,000 samples, an estimate), and whole-file runs report "context fallbacks".

What to do: pass the file bounds into `inpaint_gap`; fall back only at a chunk edge that is not the file's.

### 6. The fidelity tests can still skip silently in CI (High, non-blocking for the code)

Framework: inversion of "CI green".

What I see: plan 17 and 269 build cathar on Ubuntu and set `CUMPLE_CATHAR=~/.cargo/bin/cathar`; nothing fails if `needs_cathar` skips. In an `env:` block the tilde stays literal, and `find_cathar()`'s fallback is unspecified. `test_counts.py` checks collected tests, never run ones. Plan 269's reason for a second cache ("rust-cache does not cache `~/.cargo/bin`") is wrong: rust-cache v2.9.2 documents `cache-bin` default true; harmless, but reasoned rather than run.

Why it matters: spec 90 claims the fidelity tests run on Linux; one path slip makes them green skips, the Silero lesson one level up.

What to do: on Ubuntu, a `cathar --version` step and `CUMPLE_REQUIRE_CATHAR=1` turning the skip into a failure; expand the path in `run:`.

### 7. The cache-keys check tests a command the loop does not use (Medium, non-blocking)

Framework: environment gaps.

What I see: in the mirror, the plan's cache-keys (with the `../` globs) make `uv sync --extra repair` rebuild after an edit to either crate. A bare `uv run`, which every "run everything" step uses, does not (the import kept the old value); `uv run --extra repair` does. Plan 16 and 265 relax the reinstall rule once the `uv sync` check passes.

Why it matters: after the relaxation, a port fix followed by `uv run pytest` tests the previous build.

What to do: keep an explicit `uv sync --extra repair` (or `uv run --extra repair pytest`) after Rust edits, in CONTRIBUTING too.

## Contradictions

- Plan 112 gives cathar's window as i - 32 to i + 31; restore.rs 171 to 194 gives i - 31 to i + 32.
- Plan 358: "two cathar-gated and three core-gated"; the snippet has one and three, so the macOS and Windows figures end at 23 and 24, not 24 and 25.
- Spec 74 "measured in 03c" against 03c check 2 (threshold 4).
- Spec 88's heading "nothing outside detected damage" against its body, the injected mask.
- Plan 350 "past the slice" against spec 41 "past the context" and inpaint.rs 41 to 42.
- Plan 395 consumes `user_dir()`, which returns `~/.config/cumple/profiles` (registry.py 28 to 30); spec 62 wants `.../repair`.
- Spec 80 reads "Default" presets from files (plan 179); `Presets/De-clip` and `Presets/De-click` here hold no Default file.

## Unsupported claims

- Spec 45 and plan 375, "about 0.03 dB at 262,144": not measured; 03b has 0.00 dB on LibriVox 30 s, and 03c's 3.05e-2 is a sample difference between 8,192 and 65,536 blocks.
- Spec 86 lists ΔSDR(all) and ΔSDR(clipped) as two De-clip checks; with unclipped samples exactly equal they are the same ratio.
- Spec 86, "stays under both bounds" (concern 3).
- Plan 173, "about two minutes uncached": 03c's machine; cathar builds with thin LTO, `codegen-units = 1` and symphonia "all".

## Verified

| Claim | Source | Result |
|---|---|---|
| Detector `abs(s) > t * rms`, window 64, `--threshold`, `--out` | restore.rs 116 to 194; main.rs 475 to 511, 1420 to 1424 | confirmed |
| No natural detections on the clean fixture at 5 | numpy, largest ratio 3.38 | confirmed |
| IMPULSE visible at threshold 5 | emulation, 200 positions per cell | contradicted (30 to 38 %) |
| IMPULSE visible at threshold 4 | same | confirmed |
| Single-sample click at 20 times RMS: ratio about 7.4, refilled within 1e-3 | emulation | confirmed (7.36 to 7.50; 1.6e-4) |
| 200-sample sine refill within 1e-3 | numpy `inpaint_gap` | contradicted (6.4e-3) |
| Gap-start mutation fails the fidelity test | emulation, four seeds | confirmed |
| De-click port within 1e-3 of f32 cathar | emulation, eight seeds | contradicted once (1.2e-3) |
| Faithful De-clip ports within 0.1 dB | seven levels, three files | contradicted on the fixture (0.44) |
| Chunking cost at 8,192 under 0.5 dB, and the test can fail | nudged runs; context 0 and off-by-one mutants | confirmed (0.01 to 0.28; 1.73, 2.00) |
| scipy alignment | scipy 1.18.1 | confirmed (2.39e-15) |
| pyo3 0.29.3, numpy 0.29.0 (BSD-2-Clause), MSRV 1.83 | crates.io | confirmed |
| Allowlist covers the tree | `cargo metadata`, 29 crates | confirmed |
| `#[pymodule] fn cumple_dsp` beside a `cumple_dsp` dependency | mirror | contradicted (E0659, E0425) |
| abi3 wheel without `extension-module`; clippy clean with `test = false` | mirror | confirmed |
| `release.yml`'s sync never builds the member | mirror, `--extra app --group packaging --no-default-groups` | confirmed (static metadata; root only) |
| cache-keys rebuild on `uv sync --extra repair` | mirror | confirmed; bare `uv run` does not |
| rust-cache skips `~/.cargo/bin` | rust-cache README v2.9.2 | contradicted |
| `inpaint_gap` truncates context at file edges | inpaint.rs 37 to 42 | confirmed |
| LibriVox chapter 133,603 frames | `sf.info` | confirmed |
| 252 tests collected | `--collect-only` | confirmed |

## Verdict

**Ship with changes.** The architecture, the task order and most of the amendment stand, and `release.yml` is safe: its sync never touches the member. Before Task 1: the two one-liners (concern 1), IMPULSE recalibrated to threshold 5 (2), and the file bounds passed to `inpaint_gap` (5). Concerns 3 and 4 are sentences in the scoring rule Victor approved amending, so they need his nod. Concern 6 goes with Task 2; 7 any time. Checked hardest: rule 1 for A-SPADE (seven levels, three files, float32 and nudged f64) and the De-click detector at threshold 5 (preset visibility, natural detections on SQAM, cathar's f32 drift).

Counts: Critical 1 (concern 1), High 5 (2 to 6), Medium 1 (7). Blocking: 1 to 5.
