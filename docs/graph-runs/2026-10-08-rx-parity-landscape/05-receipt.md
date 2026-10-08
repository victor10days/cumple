2026-10-08 | rx-parity-landscape | Diamond (5 branches) | Ship with changes (Critical 2, High 2, Medium 3) | six "gap" cells were disproved by cathar, a repo another branch had found; and the C++ core was recommended without costing the rewrite | paths A (C++ core, nanobind) and B (numpy now, out-of-process plugin front end); JUCE except as the ARA fallback; every model whose weights are unlicensed, non-commercial or share-alike

## Decision

Victor approved the plan on 2026-10-08 (plan mode, ExitPlanMode): cumple becomes a full open-source DSP tool with every iZotope RX feature, benchmarked black-box against RX 8.5.1 Standard (owned) and the latest RX (trial to come); architecture path C, a Rust core `crates/cumple-dsp` seeded from cathar (MIT OR Apache-2.0) behind a `cumple[repair]` extra, the Python meters and CLI untouched, a C++ CLAP, clap-wrapper and ARA shell later; a WebGL2 spectral editor in the pywebview app first, shared with the plugin through choc's WebView; build order: foundation plus harness plus De-click and De-clip, De-click v2, editor v1, De-noise plus brush and lasso, plugin shell. This reverses the 2026-09-12 roadmap decision "automatic repair: outside a read-only QC tool".

## What shipped

Research only, no code. The run folder: `00-plan.md` (the approved plan), `01-frame.md`, `02a` to `02e` (five opus research branches, each over the 1500-word budget, accepted as a ruling), `02f-notes-repos-sent-mid-run.md` (ARC-AudioBench, Sebastian Lague's Audio-Experiments), `03-skeptic.md`, `04-recommendation.md`. `docs/ROADMAP.md` gains the reversal as a dated decision and the new items. Next: the build-1 spec under `docs/superpowers/specs/`, then superpowers:writing-plans.

## Rejected options

- Path A, a C++ core with nanobind: same compiled-package cost as C with no head start; cathar hand-translated into C++ by one person.
- Path B, numpy now with the plugin as an out-of-process ARA front end (the RX Connect pattern): defers the rewrite; every live insert rewritten later; sample-by-sample AR loops slow in numpy (inference, not measured).
- Python inside the plugin: real-time safety and distribution (the skeptic corrected "impossible" to these two reasons; PyoVST and juce-python exist as toys).
- JUCE as the primary framework: AGPL or a paid EULA; kept as the ARA fallback. iPlug2 and DPF: no ARA. nih-plug: maintenance mode, GPLv3 VST3 path.
- Models with unlicensed, non-commercial, LDC-trained or share-alike weights: DeepFilterNet3 (weights unlicensed), SGMSE, STORM, CleanUNet, facebook denoiser, Spleeter, the RoFormers, BandIt. Clean: GTCRN, umxse, htdemucs, Respiro-en, AP-BWE, VoiceFixer (CC BY).
- A GPL optional extra: the frame's rule stands (GPL and AGPL only as a subprocess or from the paper); the Linux release already bundles PyQt6 (GPL-3.0-only) through `app-qt` and moves to PySide6.
- ARC-AudioBench: report-format reference only; it measures nothing cumple does not already measure.

## Findings that changed the outcome

1. cathar (found by 02d) disproved the "gap" cells of 02a and 02b for De-plosive, Wow & Flutter, EQ Match, De-crackle, adaptive De-hum, De-rustle, De-wind and Breath; the stack table was re-mapped and cathar joined the harness as a baseline. Same blind spot as the 2026-09-12 receipt (a feature declared missing that existed): branches infer gaps from their own silence.
2. 02e's "port only the STFT to C++" would have left the repair DSP in numpy, which cannot ship in a plugin; the costing forced the language choice before build 1 instead of after it.
3. DeepFilterNet3's weights have no licence (the README licenses "All code" only); the model side of Voice De-noise now prefers GTCRN or umxse.
4. The frame's GPL rule was already broken by the shipped Linux app (PyQt6); found by 02d, ruled on in 04.
5. Push dates and commit dates were mixed across branches (SoX 2023-11-24 push versus 2021-05-09 commit); no decision depended on it; future frames say "last commit" and name the field.

## Rulings

- The five branch reports exceed 1500 words (1668 to 2076 with tables); accepted, because the tables carry the evidence.
- Push dates stand in the branch files as written; the recommendation normalises where it matters.
- Reverse engineering is black-box only, stated in the frame and repeated in the plan; no RX binary, model or code is ever read.
- Research branches and the skeptic ran on opus at Victor's request ("our best research agents"), not the skill's default sonnet.
- Plan mode held the artifacts in the plan file; they were unpacked into this folder after approval, as the graph-engineer skill allows.
- No Rust toolchain exists on this Mac yet (`cargo`, `rustc`, `maturin` not found on 2026-10-08); installing rustup is a download-and-execute step for Victor to run or approve, before build 1.

## Steps only Victor can take

Run RX 8 Batch Processing from the recipe build 1 writes; get an RX 12 Advanced trial; install rustup; decide the PySide6 switch's timing.

## The box that earned its place

The skeptic: it re-fetched about 55 cells and found the research right everywhere except in its synthesis, where one branch's discovery (cathar) falsified six cells in two others and the architecture had been chosen without a cost; both changed the recommendation.
