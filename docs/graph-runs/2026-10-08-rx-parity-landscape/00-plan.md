# Plan: cumple as a full open-source DSP tool, benchmarked against iZotope RX

Status: graph run complete (Diamond, 5 branches, skeptic, recommendation). Run folder `docs/graph-runs/2026-10-08-rx-parity-landscape/` is unpacked from this file after approval. Everything below "## 01 Frame" is the run's artifacts, kept verbatim as receipts.

## Context

On 2026-10-08 Victor decided that cumple stops being a read-only delivery QC tool and becomes a full open-source audio DSP tool with every feature iZotope RX has, benchmarked against RX (his RX 8.5.1 Standard now, the latest RX when he gets a trial), with a really cool looking spectral editing tool for his own use, delivered as a VST plugin. This reverses the 12 September decision in `docs/ROADMAP.md:29` ("automatic repair: outside a read-only QC tool"). Reverse engineering is black-box only: run RX on signals with a held clean reference, measure, and build from the literature and permissively licensed open code; no decompiling, no model extraction.

What the research found (sections 02a to 03 below, 5 opus branches, about 55 cells re-fetched by the skeptic, all confirmed at cell level):
- Almost every RX module has a permissive open implementation or a defining paper. The one repo that matters most is **cathar** (github.com/vbasky/cathar, MIT OR Apache-2.0, pure Rust, no C deps, created 2026-06-17, 0.8.0, one author, about 10,800 lines): declick, A-SPADE declip, Janssen inpaint, dehum, WPE dereverb, deplosive, derustle, dewind, deesser, breath, hpss, time and pitch, spectral repair, and more. Several of its methods are naive (dewind is a 4th-order high-pass). It is a head start, not a finished product, and it has no benchmark against RX.
- Python cannot run inside a plugin process (real-time safety and distribution), so the engine that ships in the plugin must be compiled. The permissive plugin stack is CLAP + clap-wrapper (VST3, AU) + ARA SDK (Apache) + choc WebView (ISC); JUCE is AGPL or a paid EULA and stays the fallback if ARA through clap-wrapper stalls (verified for VST3 only).
- Model weights are the licence problem, not code: DeepFilterNet's weights are unlicensed, SGMSE and STORM train on NC or LDC data, BandIt v2 is CC-BY-SA. GTCRN, umxse, htdemucs (MIT) and Respiro-en (MIT, CC-BY data) are clean.
- cumple's own Linux release already bundles PyQt6 (GPL-3.0-only) through `app-qt`; it must move to PySide6 (LGPL).
- No open brush or lasso spectral editor plugin exists under a permissive licence; the closest UX precedent is Noise Canvas (AGPL, reference only); Thesia (MIT, PixiJS WebGL) and Sebastian Lague's Audio-Experiments (MIT, C#) are the behaviour references.

## Decision being asked (the gate)

**Architecture path C**: a Rust core (`crates/cumple-dsp`) seeded from cathar, exposed to Python through PyO3 behind a `cumple[repair]` extra; the Python meters, CLI, harness and pywebview app stay as they are; the plugin comes later as a C++ CLAP, clap-wrapper and ARA shell over the core's C ABI. The costed alternatives are A (C++ core with nanobind, no head start, hand-translating cathar) and B (numpy now, plugin as an out-of-process ARA front end, every module rewritten later). Section 04.3 below has the costing. Saying "A" or "B" instead of approving changes build 1's language, nothing else in this plan.

## Recommended approach

1. **Stack and licence rules** (04.4 and 04.7): permissive dependencies and ports (MIT, BSD, ISC, Apache, cathar); LGPL only as shared libraries or subprocesses (ffmpeg, libsndfile already); GPL and AGPL only as a subprocess baseline or from the paper (ffmpeg adeclick, Audacity, Essentia, Rubber Band); model weights fetched on first use with a pinned hash and a licence allowlist that refuses NC and no-licence weights; CC-BY-SA only as a user-triggered download. Frame's GPL rule kept.
2. **The RX harness** (04.5): synthetic damage at known levels on held clean references (SQAM excerpts and LibriVox, cached under `~/.cache/cumple/`, never committed), metrics ΔSDR all and ΔSDR on damaged samples (the declipping survey's measures), residual click count, restored-peak error; baselines RX 8 Standard Batch Processing (run by Victor from a written recipe with factory presets), ffmpeg 9.0.1 adeclick and adeclip, cathar at a pinned version; `scripts/benchmark_repair.py > docs/REPAIR.md` pinned by `tests/test_repair_numbers.py`, following `scripts/benchmark_meters.py` and `tests/test_site_numbers.py`. RX is the reported target; from build 2 on, a module ships only if it beats ffmpeg and cathar.
3. **The editor** (04.6): WebGL2 spectrogram in the existing pywebview app (`src/cumple/app/ui/app.js`), tiles computed by the core, a non-destructive edit list that is both undo and A/B, first operations Gain on a time-frequency selection, De-click on a selection, Attenuate; lasso and brush in cycle 4; the same bundle later inside the plugin through choc's WebView.
4. **Build order** (04.10): build 1 foundation + harness + De-click + De-clip; build 2 De-click v2 (AR-residual detection, Interpolate up to 4,000 samples, gap-wise Janssen); build 3 editor v1; build 4 Spectral and Voice De-noise plus brush and lasso; build 5 plugin shell (CLAP, clap-wrapper, inserts with latency, editor in choc, signing), ARA after. Estimates, one cycle = one spec, plan, PR.

## Build 1 (what gets planned next with superpowers:writing-plans)

- `crates/cumple-dsp` (Rust): streaming STFT on realfft checked against scipy `ShortTimeFFT` within a stated tolerance; the module contract (ranged params, `process`, `flush`, `report`, latency); De-click and De-clip ported from cathar (`declip.rs` 712 lines, `inpaint.rs` 286, declick in `restore.rs` about 120), reshaped from whole-file `Vec<Vec<f32>>` to allocation-free float64 blocks, carrying cathar's notice. PyO3 abi3 wheel via maturin, behind `cumple[repair]`, excluded from the frozen apps until build 5.
- `src/cumple/repair/`: runner on `io/reader.py`'s `iter_blocks` (262,144-frame float64 blocks), pydantic params with `extra="forbid"`, YAML chains in the specs-profile style, built-in presets, copy-only writes as `fix.py:99-136` does (temporary name, `os.replace`, refuses dst == src), a sidecar JSON receipt (chain, versions, input SHA-256, before and after `measure()`), `--residual`.
- `cli.py`: `cumple repair <file> --chain ... --out ...`, exit codes as `fix`.
- Harness: `scripts/make_repair_set.py` (seeded damage), `scripts/benchmark_repair.py`, `docs/REPAIR.md`, `docs/repair/rx8-recipe.md` (module, preset, folders, SHA-256 manifest; RX columns say "not run" until Victor's outputs land), `tests/test_repair_numbers.py`.
- Repo housekeeping in the same branch or a one-PR fix before: `app-qt` to PySide6; `docs/ROADMAP.md` gains the reversal as a dated decision and the new items R10 onward; test count re-pinned in its five copies; no em or en dashes anywhere.
- Done when: `uv run pytest` green on all three runners with the Rust extension built, ruff clean, the two ported modules match upstream cathar on ΔSDR within tolerance, no sample outside detected damage changes beyond tolerance, `docs/REPAIR.md` written with ffmpeg and cathar baselines filled, CI `success`.

## Immediate steps after approval (this session)

1. Branch `docs/graph-run-rx-parity-landscape` from main; unpack this file into `docs/graph-runs/2026-10-08-rx-parity-landscape/` as `01-frame.md`, `02a` to `02e` plus `02f-notes.md`, `03-skeptic.md`, `04-recommendation.md`; write `05-receipt.md`; commit (no push to main; PR from the branch).
2. Update the vault hub `~/brain/Projects/cumple/cumple.md`: dated decision (2026-10-08: cumple becomes a full DSP tool; RX is the benchmark; path C; black-box only), Now, Next, Gotchas (RX 8 has no CLI; PyQt6 is GPL), session log; Home.md row; commit and push the vault.
3. Brainstorming is done by this run; write the build-1 spec at `docs/superpowers/specs/2026-10-08-repair-foundation-design.md` from section 04 and this plan, then invoke superpowers:writing-plans for build 1 (plan skeptic before plan approval, per the graph-engineer Chain), then subagent-driven development.

## Verification of this plan's claims

- Every repo cell carries a URL, a licence source and the read date 2026-10-08; the skeptic re-fetched about 55 of them (03 Re-fetch tally) and found the only errors in synthesis (gap cells disproved by cathar; the uncosted C++ core), both corrected in 04.
- Nothing has been benchmarked or timed yet: cathar's quality against RX, FFT speeds, model runtimes and all cycle counts are labelled estimates. Build 1's first task is the baseline run (ffmpeg and cathar on three signals), so the first measured number arrives before any new DSP is written.
- Steps only Victor can take: run RX 8 Batch Processing from the recipe; get an RX 12 trial; decide on PySide6.

## Open risks (04.11)

cathar is young and unbenchmarked (prose comparison with RX only, tests on synthetic tones); f32 whole-file versus float64 streaming needs tolerances; two compiled languages on four CI runners; ARA through clap-wrapper verified for VST3 only and webviews inside hosts unmeasured; only RX 8 Standard is owned.
