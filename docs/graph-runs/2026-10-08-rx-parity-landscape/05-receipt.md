2026-10-08 | rx-parity-landscape | Diamond, 5 branches | Ship with changes | five "gap" cells were disproved by a sibling branch's find (cathar), and the C++ core was recommended without costing what had to move into it | paths A and B; a numpy runner later rewritten; Python inside the plugin; JUCE as anything but the ARA fallback

# 05 Receipt: cumple as a full open-source DSP tool, benchmarked against iZotope RX

## Decision

Victor's, on 2026-10-08: cumple stops being a read-only delivery QC tool and becomes a full open-source audio DSP tool with every iZotope RX module, benchmarked against RX (RX 8.5.1 Standard now, the latest RX when a trial is available), with a spectral editor for his own use first and a plugin (CLAP, VST3, AU, ARA later). Reverse engineering is black-box only. This reverses the 12 September ruling in `docs/ROADMAP.md` that automatic repair is outside the tool.

Path C (a Rust core seeded from cathar, PyO3 bindings behind `cumple[repair]`, a C++ plugin shell later) is recorded as approved with build 1 as written in `04-recommendation.md` section 10: the plan file that closed the run was handed to this session as its task, together with the steps it lists "after approval". If Victor meant path A or B instead, only build 1's language changes; the spec and plan name the places that would move.

## What shipped

Pull request #29, https://github.com/victor10days/cumple/pull/29, branch `claude/laughing-darwin-15lo3a`, documentation only, no code and no dependency change: this run folder (`01-frame.md`, five branch reports `02a` to `02e`, `02f-notes.md`, `03-skeptic.md`, `04-recommendation.md`, this receipt), the build-1 design at `docs/superpowers/specs/2026-10-08-repair-foundation-design.md`, the build-1 implementation plan at `docs/superpowers/plans/2026-10-08-repair-foundation.md`, and `docs/ROADMAP.md` with the dated reversal, items R10 to R15 and this run in its list. Steps outside this session: the vault hub (`~/brain/Projects/cumple/cumple.md`, Home.md) is on Victor's machine; running RX 8 Batch Processing from the recipe is Victor's; the RX 12 trial is Victor's.

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
- RX columns in `docs/REPAIR.md` say "not run" until Victor's Batch Processing outputs land; the benchmark script refuses to write only when the ffmpeg or cathar baseline is missing.

## The box that earned its place

The skeptic, for the third run in a row: a sibling branch had already found the repository that disproved five gap cells, and nobody inside the branches connected the two. The costing table in 04 exists because the skeptic refused an architecture choice with no module count behind it.
