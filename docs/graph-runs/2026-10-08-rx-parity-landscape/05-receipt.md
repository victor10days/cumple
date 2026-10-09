2026-10-08 | rx-parity-landscape | Diamond, 5 branches | Ship with changes | five "gap" cells were disproved by a sibling branch's find (cathar), and the C++ core was recommended without costing what had to move into it | paths A and B; a numpy runner later rewritten; Python inside the plugin; JUCE as anything but the ARA fallback

# 05 Receipt: cumple as a full open-source DSP tool, benchmarked against iZotope RX

## Decision

Victor's, on 2026-10-08: cumple stops being a read-only delivery QC tool and becomes a full open-source audio DSP tool with every iZotope RX module, benchmarked against RX (RX 8.5.1 Standard now, the latest RX when a trial is available), with a spectral editor for his own use first and a plugin (CLAP, VST3, AU, ARA later). Reverse engineering is black-box only. This reverses the 12 September ruling in `docs/ROADMAP.md` that automatic repair is outside the tool.

Path C (a Rust core seeded from cathar, PyO3 bindings behind `cumple[repair]`, a C++ plugin shell later) is recorded as approved with build 1 as written in `04-recommendation.md` section 10: the plan file that closed the run was handed to this session as its task, together with the steps it lists "after approval". If Victor meant path A or B instead, only build 1's language changes; the spec and plan name the places that would move.

## What shipped

Pull request #29, https://github.com/victor10days/cumple/pull/29, branch `claude/laughing-darwin-15lo3a`, documentation only, no code and no dependency change: this run folder (`00-plan.md`, the plan Victor approved in plan mode; `01-frame.md`, five branch reports `02a` to `02e`, `02f-notes.md`, `03-skeptic.md`, `04-recommendation.md`, this receipt), the build-1 design at `docs/superpowers/specs/2026-10-08-repair-foundation-design.md`, the build-1 implementation plan at `docs/superpowers/plans/2026-10-08-repair-foundation.md`, and `docs/ROADMAP.md` with the dated reversal, items R10 to R15 and this run in its list. Steps outside this session: the vault hub (`~/brain/Projects/cumple/cumple.md`, Home.md) is on Victor's machine; running RX 8 Batch Processing from the recipe is Victor's; the RX 12 trial is Victor's.

Pull request #30 (https://github.com/victor10days/cumple/pull/30, branch `docs/graph-run-rx-parity-landscape`, from the session that ran the graph) merged the same run to main first, on 2026-10-08 at 18:13 UTC, under three other file names (`02b-research-noise-and-reverb.md`, `02e-research-plugin-and-editor-stack.md`, `02f-notes-repos-sent-mid-run.md`) and with its own receipt and roadmap rows. This branch merged main in and kept its own copies: the same text, word for word, plus the headers that say where each correction lives, the PR link, and the spec and plan in the roadmap row. #30's three duplicate files were removed; `00-plan.md` came from #30.

## Rejected options

- Path A (C++ core with nanobind): the same compiled-package cost with no head start; every cathar module hand-translated into a memory-unsafe language by one developer. What would change it: cathar's licence changing, or its port proving slower than a translation (measured, not estimated).
- Path B (numpy now, plugin as a thin ARA front end to an out-of-process engine): defers the rewrite instead of avoiding it; live inserts would need every module rewritten; AR loops in numpy are slow (inference, not measured).
- Python inside the plugin process: real-time safety and distribution, not impossibility (the skeptic corrected 02e's wording).
- A separately written plugin: two implementations drift and every test doubles.
- 02d's "GPL optional extra is legal" row: overruled; the frame's rule stands (GPL and AGPL as a subprocess or from the paper only), and `app-qt` moves to PySide6.
- Bundling any model weights: fetched on first use with a pinned hash and a licence allowlist; DeepFilterNet3's weights have no stated licence and are out until verified.

## Findings that changed the outcome

- Skeptic, Critical: 02a and 02b called De-plosive, Wow & Flutter, EQ Match, De-crackle, adaptive De-hum, De-rustle and De-wind gaps; cathar (found by 02d) has permissive code for each. The stack table now says "permissive baseline, naive" where that is the truth, and cathar joins ffmpeg as a harness baseline.
- Skeptic, Critical: 02b recommended DeepFilterNet3 weights as MIT or Apache while its own unknowns said the README licenses code only. Marked unknown; GTCRN or umxse preferred.
- Skeptic, High: 02e recommended a C++ core while 02a to 02d designed numpy modules, so build 1 would have been written and then rewritten. 04 costed three paths and chose C.
- Skeptic, High: the Linux release already bundles PyQt6 (GPL-3.0-only) through `app-qt`. PySide6 (LGPL) becomes R15 and a precondition of the next release.
- Skeptic, Medium: build 1 had no scoring rule and nothing had been measured. Section 5 of 04 defines ΔSDR on all and on damaged samples, residual clicks and restored-peak error, and makes the ffmpeg and cathar baseline run build 1's first task.
- This session, from a shallow clone of cathar at commit f2c2842 (2026-09-21 UTC), read 2026-10-08: `crates/cathar/src` is 10,277 lines of Rust (the research estimated about 10,800 from byte counts); the workspace is edition 2024 with `rust-version = "1.87"`, licence `MIT OR Apache-2.0` with the copyright line "The cathar Authors"; it depends on `rustfft = "6"` and `realfft = "3"`; `declick_with_method` fixes the local-RMS window at 64 samples from the CLI with `--threshold` 10.0 and defaults to Janssen AR through `inpaint_gap`; `inpaint_gap` does its AR estimate and banded solve in f64 already, with `AR_ORDER = 32` and a linear-fill fallback above `MAX_SOLVE = 2048` samples (RX's Interpolate allows 4,000, so build 2 must raise it); `declip_spade` uses a 1024-sample Hann frame, hop 256 and at most 100 iterations with `--threshold` 0.95 as the CLI default. These numbers are in the plan so the port can be checked against them.

## Rulings

- The branch reports are unpacked verbatim, including the cells the skeptic disproved; the corrections live in 03 and 04, and each branch file's header says where. A reader gets the receipts, not a cleaned history.
- The phrase "not checked" appears in four cells of the verbatim branch reports (02a C4 and its unknowns, 02b GAC and its unknowns); each is an unknown the branch declared, and 03 lists them. The rule forbids the phrase on the page, in README and in RELATED; the run folder keeps the branches' own words.
- Word counts: the five branch reports exceed the frame's 1500 words (2076, 2039, 1687, 1668, 1930 with tables); accepted, as the 12 September receipt accepted 900 over 600 when the table is the deliverable.
- Dates: branches report push dates, 02d commit dates; no decision depended on the difference; 04 names both for cathar.
- superpowers:writing-plans was not available in the cloud session that closed this run, so the build-1 plan was written by hand in the shape of `docs/superpowers/plans/2026-09-13-silero-vad.md`. The plan skeptic (a fresh context, as the Silero run did) still reads it before any task runs; that gate is not skipped, only deferred to the session that executes build 1.
- No Rust toolchain was on Victor's Mac on 2026-10-08 (`cargo`, `rustc` and `maturin` not found); he installed rustup himself the same day (rustc and cargo 1.99.0, stable, aarch64-apple-darwin).
- RX columns in `docs/REPAIR.md` say "not run" until Victor's Batch Processing outputs land; the benchmark script refuses to write only when the ffmpeg or cathar baseline is missing.

## Plan skeptic

`03b-plan-skeptic.md` (fresh opus context, 2026-10-08) read the build-1 plan against the spec, the code and cathar at f2c2842, and ran numpy re-expressions of cathar's two algorithms. Verdict: Rethink this, in the scoring rule and the harness parameters; the architecture, crate layout and task order stand. Critical 4, High 2, Medium 1; concerns 1 to 5 block. Headline: at cathar's defaults neither module touches the harness damage (De-click's local RMS includes the tested sample, so a sample can reach at most sqrt(64) = 8 times it against a threshold of 10; De-clip returns its input when nothing reaches 0.95, while the damage clips at 0.007 to 0.126), so the fidelity rule would pass for two no-ops; and chunked A-SPADE misses its own tolerances even for a perfect port. The main session re-read `local_rms`, the De-clip early return and the relaxation step at that commit and confirmed all three. Side effect: the skeptic's scratch `uv lock` made maturin download a Rust toolchain into `~/Library/Caches/puccinialin` (473 MB); left for Victor to keep or delete. The spec amendment (thresholds from the damage, fidelity measured whole-file, chunking cost measured separately) is Victor's decision.

`03c-plan-skeptic-second-read.md` (fresh context in the cloud session, started before 03b reached the branch and without reading it; it built the cathar CLI at the pinned commit and ran the plan's recipes on the fixture). Verdict: Do not ship as written; Critical 4, High 3, Medium 6, Low 1. It reached the same four blocking findings by different experiments (the detector bound confirmed on the built CLI: 0 samples changed at thresholds 10 and 7; cathar `declip` at 0.95 on the 5 dB clip: 0 samples, at the clip level: +7.71 dB; a faithful f64 A-SPADE port against the CLI: ΔSDR within 0.01 dB, 9,281 samples over 1e-3; the scipy oracle off by one column and a phase convention) and added four of its own: CI never ran the fidelity tests, "exit codes as `fix`" was false (`fix` exits 0 on nothing to change), the click model put the fixture at 0.25 dB input SDR so even ffmpeg's `adeclick` could do nothing, and the `cargo deny` allowlist used names that are not SPDX ids.

On Victor's "continue" the cloud session applied both reports to the spec and the plan the same day, including the scoring-rule amendment both skeptics proposed in the same words (port fidelity measured whole-file; chunking cost measured and reported, not gated; De-clip scored on ΔSDR with unclipped samples exactly unchanged and no sample bound on rebuilt ones; De-click default threshold 5 under the sqrt(window) bound; the harness runs every declipper at the manifest's clip level and gives RX a scaled input folder). The amendment is marked at the top of the spec and is Victor's to reverse before merge; nothing in it moves the design off path C. Two findings stay as receipts rather than fixes: the detector of record cannot see wide or weak clicks (build 2 replaces it; the harness reports its miss rate on a burst table), and two faithful A-SPADE implementations differ at the sample level (the rule scores ΔSDR, which is what the harness and RX use).

## Plan re-check

`03d-plan-skeptic-after-amendment.md` (a third fresh context, on Victor's Mac, 2026-10-08) read the amended plan at ed39f6e, ran the new numbers and a scratch mirror of the Rust workspace. Verdict: Ship with changes; Critical 1, High 5, Medium 1; five block. The bindings do not compile as named (`#[pymodule] fn cumple_dsp` shadows the `cumple_dsp` crate, E0659); the click preset was calibrated at threshold 4 and is used at 5; De-clip's 0.1 dB fidelity gate sits at the f32 against f64 noise floor on short files (up to 0.44 dB on the fixture); locality fails on half the SQAM set because a lone LSB in digital silence has ratio exactly 8; and the planned `inpaint_gap` fills file-edge gaps linearly where cathar solves AR. A parallel amendment made on Victor's Mac from 03b alone was parked on the local branch `pr29-amendment-alt`; 03d lists what it had that the adopted version lacks. The roadmap's damping allows one skeptic fix round; this report goes to Victor before any second round.

## Second fix round and its check

The main session on Victor's Mac answered 03d in 269008d. It covered the crate rename, the refill bound, the click preset at threshold 5, locality against the module's own gaps, a per-file De-clip tolerance (the rule Victor chose), the file-edge AR rule, CI that fails when cathar is missing, and the rebuild rule. `03e-plan-skeptic-fix-round-2.md` (fresh context) found 18 of the 21 03d items answered, and two blockers in the round's own fixes: the De-click fidelity test fails a correct f64 port in about one click layout in seven, because cathar's f32 running RMS can also read high and miss a click; and the per-file De-clip tolerance measures nothing, since every harness file is already float32-exact and a 1 - 2^-50 nudge sends every clipped sample under the threshold. Comparing an f32 upstream with an f64 port has now failed twice as a tolerance design, so the session stopped and took the alternatives to Victor rather than trying a third rule.

## Precision round and its check

Victor chose to port both precisions (e46b764): the f32 build does cathar's arithmetic on cathar's pinned rustfft and is held to 1e-6 and 0.01 dB; the f64 build ships, and its difference is reported. `03f-plan-skeptic-precision-round.md` confirmed the approach holds (five build profiles gave bit-identical f32 rustfft output; cathar's decode and write paths are exact; the De-clip mutations now miss the bound by 2.7e-2 to 4.5e-1) and found two Task 3 blockers: cathar's gaps cannot be read off its output, and a mutation that computes local_rms in f64 passed about half the click layouts. Both are answered in the plan (cathar's detector re-expressed exactly in float32; a seed where the two precisions differ and a bit-exact local_rms test), with the wording and window fixes it named.

## Build 1

Pull request #31, https://github.com/victor10days/cumple/pull/31, branch `build/r10-repair-foundation`, from main at d7e42c8 (the plan, merged in #29). Run by subagent-driven development on Victor's Mac on 2026-10-08 and 09:
- seven tasks, each with a fresh implementer and a fresh task reviewer;
- a fix round on four of them;
- a final whole-branch review on the most capable model, one fix wave, and a scoped re-review.

What shipped:
- the Rust core `crates/cumple-dsp`: a streaming STFT, the module contract and chunk protocol, and De-click, Interpolate and De-clip ported from cathar at f2c2842, generic over f32 and f64;
- the PyO3 bindings behind `cumple[repair]`;
- `cumple repair`, with its chains, presets, runner, receipts and refusals;
- the harness and `docs/REPAIR.md`, pinned by `tests/test_repair_numbers.py`;
- CI for Rust, with cathar built on Linux;
- `06-build-1-notes.md`, which holds every measured figure and cites the task reports.

### What was measured

- **Port fidelity (spec rule 1):** met on all 126 damaged files. The largest sample difference against the cathar CLI is 4.66e-10. The De-click gap lists are equal on 28 of 28, and unclipped samples are exactly equal on 98 of 98. The f32 build is bit-exact on the fixture at every level.
- **Mutations:** every mutation the plan named fails its test, with the figures recorded in the notes.
- **De-clip, the shipped f64 build:** mean ΔSDR +8.32 dB against cathar's +8.48 over 98 files. Over the 44 files ffmpeg also ran: cumple +11.36, cathar +11.46, ffmpeg +4.47.
- **Impulse De-click:** cumple +36.95 dB, with 0 of 578 clicks missed and 6 false detections (lone LSBs in digital silence). Cathar +35.99 dB, with 52 missed and 1,699 false detections, counted through the f32 build. ffmpeg +16.12 dB. The lead over cathar comes almost entirely from one file, a35-glockenspiel. There cathar's f32 running sum drifts, and it writes a -30 dBFS artefact into clean audio. Without that file the lead is +0.04 dB.
- **Burst clicks:** about 0 dB for every tool, since they are invisible to the detector of record by its sqrt(window) bound.
- **Precision effect (rule 1b):** -2.47 to +12.95 dB. The drift runs both ways: spurious fills in quiet passages, and missed clicks elsewhere.
- **Chunking cost at `DEFAULT_BLOCK_FRAMES` (rule 2):** De-click is exact. De-clip is within 0.18 dB.
- **Chains:**
  - De-clip then De-click: -0.10 to +0.09 dB over 24 layouts, with every gap list equal.
  - De-click then De-clip: -0.12 to +0.06 dB.
- **First CI run** (2026-10-09, run 37909916065): all three test runners, EBU conformance and the four release builds passed.
  - The uncached cathar build took 80 s on ubuntu-latest.
  - The cathar-gated tests ran there with the "required" gate set.
- **Locally:** `uv run pytest` 327 passed and `cargo test -p cumple-dsp` 41 passed.

### Findings that changed the build

- **Task 1:** the first summary compared ffmpeg and cathar over different file sets. It now pairs them, and counts unchanged files only where a tool ran.
- **Task 3:** a repaired gap's tail was dropped when blocks were shorter than the gap. Windows 2 and 3 panicked in chunked mode. Both were fixed.
- **Task 5:** a destination that differs from the source only in letter case replaced the source on macOS. It is now refused through `samefile` and a casefolded comparison.
- **Task 6:**
  - The first false-detection counts hid exactly the detections spec rule 3 names. The counts now take each build's own gaps.
  - The impulse lead now says which file drives it.
- **Final review:** De-click after De-clip in a chain drifted its running sum and rewrote 14 % of a clean file (265 false clicks on 30 s of speech). De-click now redoes its sum from the first sample a chain changed. Single-module output stays byte-identical.
- **Final review, CI:** four window pins sat within 0.063 ULP of a rounding midpoint, so they were dropped before the first CI run.

### Rulings made during the build

1. `metrics.local_rms_ratio` is part of Task 1's deliverable, because the plan's tests call it. Cost if wrong: none.
2. The `Module` trait stays f64 at its boundary, and the f32 builds cast internally. Cost if wrong: a small refactor if the trait later needs a type parameter.
3. The test helpers live in `tests/repair_helpers.py`, and `PRECISION_SEED` lives in the De-click test file. Cost if wrong: none.
4. README's Ubuntu sentence never got an interim clause, because CI first ran after cathar was built there. Cost if wrong: one sentence.
5. The `num-complex =0.4.6` pin may fall back to unpinned; it held. Cost if wrong: none, since the fidelity test would catch a difference.
6. A plan slip, "Then wrap the result then wrap in a Module", was read as "wrap the result in a Module". Cost if wrong: none.
7. The "clean file" in the runner and CLI tests is a continuous tone with no digital silence. Cost if wrong: a test on the wrong input, which review would catch.
8. The harness summary pairs the tools and counts unchanged files only where a tool ran. Cost if wrong: a longer summary block.
9. The 20 s SQAM excerpts and ffmpeg's time budget (0.5 x duration + 10 s, this machine's) stand, disclosed in the header. Cost if wrong: another machine pairs a different ffmpeg subset; comparisons stay fair because they are paired.
10. README's macOS and Windows sentence names both reasons, no ffmpeg and no cathar baseline, as dispatched. Cost if wrong: one clause.
11. The RX De-click values are Victor's to read off RX 8; the recipe marks them. Cost if wrong: none; the RX columns read "not run" until then.
12. The wheel's rust-numpy notice was deferred to the final wave and added there, before any wheel is distributed. Cost if wrong: none now; it is fixed.
13. Windows 2 and 3, which panicked, were treated as Important and fixed in Task 3's round. Cost if wrong: one extra line.
14. The plan's `resolve()` rule for refusing the source was kept and strengthened with `samefile` and a casefolded comparison. Cost if wrong: a stricter refusal of two names that differ only in case on a case-sensitive volume.
15. The same two defects in `cumple fix` (the case-variant overwrite, and truncation at 16 and 24 bits) were left out of this build, since the spec forbids changing `fix`. They went to a separate task, which Victor started on 2026-10-09. Cost if wrong: `cumple fix` keeps both defects until that task lands.
16. The impulse lead's one-file explanation joined Task 6's fix round, because it corrects the same sentence. Cost if wrong: none.
17. The last residual Minor ("a minute" for a 30 s file in AI_USAGE.md and a test docstring) was corrected in this receipt commit rather than in a second fix wave. Cost if wrong: none.

### Deferred to later builds

These were triaged as able to wait, and are listed in the final review's ledger extract:
- `Stft::synthesize`'s edge gain, which must be fixed before R12's editor uses it;
- the binding tests for synthesize and non-contiguous input;
- fallback-counter tests;
- release of `process_whole` memory, and the A-SPADE early return;
- suite time (59 s);
- Task 6's wider pin coverage;
- moving `cathar_gaps` into `src/`.

### Steps only Victor can take

- Merge #31.
- Run RX 8 Batch Processing from `docs/repair/rx8-recipe.md`, filling in the De-click values.
- Get an RX 12 Advanced trial.
- Reserve `cumple-dsp` on PyPI (R8).

Machine side effects on his Mac during the build:
- `cathar` installed in `~/.cargo/bin` (the pinned baseline);
- `cargo-deny` installed;
- uv installed a managed CPython 3.12.15 during Task 2's no-Rust checks.

## The box that earned its place

The skeptic, for the third run in a row, and this time twice on the plan: two fresh contexts, one on each machine, each proved that the plan's own tests could not fail at the defaults it chose, and each measured it rather than arguing it. In the research: a sibling branch had already found the repository that disproved five gap cells, and nobody inside the branches connected the two. The costing table in 04 exists because the skeptic refused an architecture choice with no module count behind it.
