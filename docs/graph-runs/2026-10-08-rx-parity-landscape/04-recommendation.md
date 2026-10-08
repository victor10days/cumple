# 04 Recommendation: a Rust core seeded from cathar, scored against RX

Date: 2026-10-08. Run: `docs/graph-runs/2026-10-08-rx-parity-landscape/`. Fresh opus agent; read only the frame, 02a to 02f and 03. Kept verbatim. Victor's decision on section 12 is recorded in `05-receipt.md`.

## 1. Recommendation

Build the repair engine once, as a Rust core seeded from cathar (path C). It becomes a `cumple-dsp` crate with PyO3 bindings behind a `cumple[repair]` extra. The Python meters, CLI, harness and pywebview app stay as they are, and the plugin comes later as a C++ CLAP, clap-wrapper and ARA shell over the core's C ABI. Order: build 1 (foundation, harness, De-click, De-clip), De-click v2, editor v1, De-noise, plugin shell (section 10).

## 2. Why

One implementation: 02e rules Python out of the plugin process (03 corrects the reason: real-time safety and distribution); that makes 02d's numpy runner plus 02e's later C++ port the write-then-rewrite that 03 Concern 3 names. Head start: cathar (02d) already has permissive A-SPADE, Janssen inpainting, declick and about 30 more modules; porting Rust to Rust costs less than translating it (estimate). The plugin side is C++ anyway: 02e's permissive plugin stack (CLAP, clap-wrapper, ARA SDK, choc) is C++, so only the shell is C++. The QC product is untouched: the compiled part sits behind an extra, the way `vad` does. The skeptic's verdict was "Ship with changes"; both Critical findings are addressed in sections 4 and 7.

## 3. Architecture decision, costed

Shared by all paths: `src/cumple/repair/` (runner, params, YAML chains, receipts, per 02d), a `repair` subcommand in `cli.py` (496 lines), the harness and the editor UI. Reused, not rewritten: `io/reader.py` (314 lines, `iter_blocks`), `io/ffmpeg.py` (288), `fix.py` (136; `fix_file()` lines 113 to 136 already refuse to overwrite the source, write under a temporary name, then `os.replace`), `meters/` (8 files, 1,394 lines: bs1770 318, measure 320, truepeak 168, leqm 160, dialogue 150, vad 140, layout 126, init 12). No meter moves in any path. `pyproject.toml` (85 lines) keeps hatchling.

| | A: C++ core, nanobind | B: numpy, thin ARA front end | C: Rust core from cathar, PyO3 |
|---|---|---|---|
| Written | C++ STFT (ducc0 or pocketfft), De-click, Interpolate, A-SPADE; wheel job | numpy STFT on `ShortTimeFFT`; same 3 modules | `crates/cumple-dsp`: streaming STFT on realfft; port of cathar `declip.rs` (712 lines), `inpaint.rs` (286), declick in `restore.rs` (about 120); abi3 wheel |
| Rewritten | cathar translated by hand over the long tail (about 10,800 lines; estimate from 376,270 bytes in `crates/cathar/src`) | every module a live insert needs, later | cathar's whole-file `Vec<Vec<f32>>` API reshaped to allocation-free blocks |
| cumple files | `pyproject.toml` one extra; wheel job in `release.yml` (4 runners, lines 33 to 36) and `tests.yml` | no extra files | as A |
| Plugin | CLAP, clap-wrapper for VST3 and AU, ARA SDK, choc; JUCE fallback (AGPL or EULA) | ARA plugin that sends clips to the frozen engine (RX Connect pattern); no live inserts | A's C++ shell over a C ABI; clack (Apache) as the pure-Rust CLAP option; nih-plug out (GPLv3 VST3, maintenance mode); no Rust ARA binding |
| Licence | BSD-3, MIT, Apache-2.0 | permissive | cathar MIT OR Apache-2.0 (both licence files read), realfft MIT, rustfft and PyO3 MIT/Apache |
| Cycles, estimate | M1 2, M2 +2, M3 +2 to 3; 1 per family | M1 1 to 2; M2 needs A or C plus a rewrite per family; M3 +3 | M1 2, M2 +2 to 3, M3 +2 to 3; 0.5 to 1 per family cathar already covers |

Milestones: M1 = De-click and De-clip scored against RX; M2 = VST3 and AU inserts; M3 = ARA editor. Pick C. A loses: it pays the same compiled-package cost with no head start; every cathar module would be hand-translated into a memory-unsafe language by a solo developer; A's one real edge, that the plugin SDKs are C++, survives in C's C++ shell. B loses: it defers the rewrite rather than avoiding it; live inserts mean rewriting every module (02e); B also still translates cathar into numpy, where sample-by-sample AR loops are slow (inference, not measured). C follows Victor's goals in order: breadth (cathar covers most families), benchmarks (the Python harness drives the core), editor (the core computes the spectrogram tiles), plugin (the core can run in real time once reshaped).

## 4. Stack table

Key: P permissive, L LGPL, G GPL/AGPL (subprocess or paper only), M model behind an extra. "naive" means "permissive baseline, naive": a simple cathar method, as 03 Concern 1 or cathar's README section "Inside each tool" shows.

| RX family | Source | Class |
|---|---|---|
| De-click, Interpolate | port cathar `declick` (local-RMS detector, naive), `inpaint.rs`; AR-residual detection from Godsill and Rayner | P; paper |
| De-clip | port cathar `declip.rs` (A-SPADE, social, OMP, NMF) | P |
| De-crackle, De-plosive, Wow & Flutter, EQ Match | cathar `decrackle.rs`, `deplosive`, `dewow.rs`, `rebalance.rs` | P, naive |
| Mouth De-click | none (4 gh searches, 03) | gap |
| De-hum | cathar `dehum`, `adehum.rs`; ZapLine reference | P |
| Azimuth, Phase | cathar `align.rs` GCC-PHAT; fixed rotation via Hilbert; adaptive Phase | P; gap |
| Dither | Lipshitz et al. 1992 | paper |
| Resample, EQ, Gain, Fade, Normalize, Mixing, Trim, Generator | cathar `resample.rs`, `filter.rs`, `edit.rs`, `effects.rs` | P |
| Waveform Stats, Loudness Control, Leveler | cumple meters, `fix.py`, VAD; true-peak limiter from cathar `normalize` | P (own) |
| Markers | wavinfo for reading; cue writing | P; small gap |
| Spectral De-noise, Ambience Match | cathar `denoise.rs`, `noiseprint`, `psycho.rs` | P |
| Voice De-noise | cathar Wiener; GTCRN or umxse | P; M |
| De-reverb | cathar `wpe.rs` | P |
| Dialogue De-reverb | VoiceFixer (weights CC BY 4.0) | M |
| De-rustle, De-wind | cathar `derustle`, `dewind` (4th-order high-pass) | P, naive |
| De-ess | cathar `deesser` multiband | P |
| Breath Control | cathar `breath`; Respiro-en as upgrade | P, naive; M |
| Guitar De-noise | hiss via De-noise; pick, squeak | P; gap |
| De-bleed | MDF from speexdsp (BSD-3); cathar `align` | P |
| Spectral Repair | cathar `repair` (temporal median); Janssen-TF | P, naive; paper |
| Spectral Recovery | cathar `enhance.rs`; AP-BWE | P, naive; M |
| Dialogue Isolate | cathar `voiceisolate`; umxse or MossFormer2; reverb output | P, naive; M; gap |
| Music Rebalance | htdemucs (MIT) | M |
| Scene Rebalance | BandIt v2 CC-BY-SA, BandIt Plus unlicensed | gap |
| Center Extract | Avendano and Jot; cathar `stereo` | paper; P, naive |
| Deconstruct | cathar `hpss.rs`, `sms.rs` | P |
| Time & Pitch, Variable Time and Pitch, Dialogue Contour | cathar `timestretch.rs`, `pitch.rs` (naive); Signalsmith Stretch (MIT) port; Rubber Band reference | P; G |
| Find Similar | log-mel cross-correlation, DTW | paper |
| Repair Assistant | cumple checks, cathar `stats` pattern; chain generation | P; gap |
| Streaming Preview | soundfile encoders, cumple meters | L |
| Plug-in Hosting | VST3 SDK now MIT; no host yet | gap |

## 5. The RX harness

Scoring rule: build 1 passes when the ported De-click and De-clip match upstream cathar on ΔSDR within a stated tolerance (port fidelity), no sample outside detected damage changes beyond that tolerance, and every column is filled or marked "not run". From build 2 on, a module ships only if it beats ffmpeg and cathar on ΔSDR at every damage level. RX 8 is the reported target, not a gate. Harness design: references are the survey's 10 SQAM excerpts (named in the `rajmic/declipping2020_codes` README; that code is GPL, so only the protocol is reused) and LibriVox speech, fetched to `~/.cache/cumple/` and never committed (SQAM terms unread); damage is hard clipping at the survey's seven input-SDR levels and clicks at known positions, widths and levels above local RMS, fixed seeds; metrics ΔSDR on the whole signal and on damaged samples only (the survey's dSDR_all and dSDR_clipped, read from its README), residual click count (injected clicks still above threshold plus false detections), restored-peak error in dB per clipped run; the survey's PEAQ, PEMO-Q and Rnonlin cannot ship (PEAQ code sits in the GPL repo, PEMO-Q is withheld for copyright). Baselines: RX 8 Standard Batch Processing run by Victor from `docs/repair/rx8-recipe.md` (factory presets, folders, SHA-256 manifest); ffmpeg 9.0.1 `adeclick` and `adeclip`; cathar `declick` and `declip` at a pinned version. Pinning: `scripts/benchmark_repair.py > docs/REPAIR.md`, refusing to write if a baseline is missing, as `scripts/benchmark_meters.py` does; `tests/test_repair_numbers.py` checks the summaries against the tables as `tests/test_site_numbers.py` does and reruns one short fixture within a tolerance; the RX columns say "not run" until Victor's outputs land.

## 6. The spectral editor

| RX 8 operation (`interactive-tools/index.html`) | Module | When |
|---|---|---|
| Instant Process: Gain | Gain on a time-frequency mask | first |
| Instant Process: De-click (Interpolate under 4,000 samples) | De-click, Interpolate | second |
| Instant Process: Attenuate | Spectral Repair, Attenuate | third |
| Instant Process: Replace, Fade | Spectral Repair Replace (Janssen-TF), Fade | later |
| Time [T], Time-Frequency [R], Frequency [F] | selection mask | first |
| Lasso [L], Brush [B] | selection mask | cycle 4 |
| Magic Wand [W], Harmonic selection | partial tracking (cathar `sms.rs`) | later |
| Shift add, Alt subtract, selections stored with undo | edit list | first |
| View Clip Gain | gain envelope (Leveler) | later |

UI stack: WebGL2 in the existing pywebview app (`src/cumple/app/ui/app.js`, 264 lines), drawing tiles that the core computes; a non-destructive edit list serves as both undo and A/B (02e); the same bundle later runs in the plugin through choc's WebView (ISC). References: SebLague/Audio-Experiments (MIT, C#) for how painting on the spectrogram and resynthesising should behave; Thesia (MIT) as a GPU spectrogram viewer; Noise Canvas (AGPL) for user experience only, no code.

## 7. Licence rulings

Keep the frame's GPL rule: GPL and AGPL only as a subprocess or from the paper, never as an extra; 02d's own table says a bundle with a GPL extra becomes GPL, and both the app and the plugin are bundles. `app-qt`: the Linux release is built with `--extra app-qt` (`release.yml` line 36), so a shipped artefact already bundles PyQt6 (GPL-3.0-only); move to PySide6 (LGPL-3.0) in a one-PR fix before the next release. Weights: CC-BY allowed behind an extra, fetched on first use, hash-pinned, with attribution in the manifest and the receipt; CC-BY-SA only as a user-triggered download from upstream, never bundled, redistributed or fine-tuned; no licence excluded, at most a path the user supplies, off by default; CC-BY-NC excluded. DeepFilterNet3 weights: licence unknown (the README licenses "All code" only); GTCRN or umxse preferred until verified (03 Concern 2). cathar's bundled `denoiser.safetensors` (2.1 MB) is not ported: its CHANGELOG cites `scripts/train_denoiser.py`, which is not in the tree.

## 8. Rejected options

Architecture: paths A and B, nih-plug, nice-plug (section 3); Python inside the plugin (real-time safety); a separately written plugin (drift); 02d's numpy runner (replaced by the core; its runner design stays). Plugin frameworks: JUCE (AGPL or paid EULA; ARA fallback only); iPlug2, DPF (no ARA). DSP building blocks: Faust, Cabbage 3 (GPL), Elementary, Glicol, Pure Data, FunDSP, DaisySP, STK, Maximilian, liquid-dsp (stream or synthesis blocks with no repair). FFT libraries: KFR, FFTW (GPL), Intel IPP (not OSI), vDSP (Apple only) rejected; KissFFT, PFFFT, pocketfft fine, but realfft keeps the core pure Rust, with scipy's ducc0 as the oracle within a tolerance. GPL or AGPL, reference only: pedalboard, DawDreamer, Carla, Essentia, matchering, Audacity, GWC, IPOL, Parselmouth. Unchecked and no RX module needs them: JamesDSP, Dragonfly Reverb, SOF, freeDSP, ESP32-FFT, Audioflux, pyAudioDspTools. Native GUIs (egui, iced, vizia, Dear ImGui, NanoVG, Skia, wgpu) would split the app and plugin UIs. Models: DeepFilterNet3, SGMSE, STORM, CleanUNet, the facebook denoiser, Spleeter, RoFormers, BandIt (weights unknown, NC, LDC-trained or share-alike). ARC-AudioBench: report-format reference only. A GPL hosting helper: not needed.

## 9. Skeptic findings and disposition

1. Critical, cathar contradicts gap cells: addressed (section 4 re-maps every gap against cathar's tree and README, marks naive methods, cathar joins the harness). 2. Critical, DFN weights: addressed (marked unknown; GTCRN or umxse preferred). 3. High, uncosted C++ core: addressed (three paths costed, C chosen, no numpy module oracle). 4. High, licence rulings: addressed (frame's rule kept, `app-qt` to PySide6, rows for CC-BY, CC-BY-SA and no-licence weights). 5. Medium, dates and budget: risk accepted (no decision depends on push versus commit dates; cathar last commit 2026-09-21, push 2026-09-30, 19 stars on 2026-10-08; the run folder normalises dates; word overage accepted as a ruling). 6. Medium, no scoring rule: addressed in section 5; the baseline runs are build 1's first task. 7. Medium, editor answered as a stack: addressed in section 6.

## 10. Build order

1. Build 1 (path C): `crates/cumple-dsp` with a PyO3 abi3 wheel behind `cumple[repair]`; a streaming STFT on realfft checked against scipy `ShortTimeFFT` within a stated tolerance; the module contract (ranged params, `process`, `flush`, `report`, latency); De-click and De-clip ported from cathar, carrying its notice; `cumple repair` with a sidecar receipt and copy-only writes; the section 5 harness, the RX recipe, `docs/REPAIR.md` and its test. Unlocks the first RX scores and the core the plugin will share.
2. De-click v2: AR-residual detection, Interpolate with RX's 4,000-sample rule, gap-wise Janssen (Mokrý and Rajmic 2025). Unlocks beating both baselines.
3. Editor v1 in pywebview: WebGL2 spectrogram, the first three operations, the edit list. Unlocks Victor's own use.
4. Spectral and Voice De-noise from cathar, plus brush and lasso selection; the harness adds SI-SDR and DNSMOS. Unlocks the family a post engineer likely uses most (assumption).
5. Plugin shell, the first of an estimated 2 to 3 cycles: C++ CLAP over the C ABI, clap-wrapper for VST3 and AU, inserts with latency reporting, the editor in choc, code signing and notarisation. ARA follows.

## 11. Open risks

cathar is young and unbenchmarked: created 2026-06-17, at 0.8.0, all 106 contributions by one author; `book/src/13-vs-industry.md` compares it with RX in prose only; `ROADMAP.md` plans benchmarks against SoX and FFmpeg only; `crates/cathar/tests/golden.rs` checks byte equality on a 440 Hz tone, macOS only; its 39 `lib.rs` tests use synthetic tones. Precision mismatch: cathar is f32 and whole-file, cumple float64 and streaming, so tests need tolerances. Two compiled languages (Rust core, C++ shell) on four CI runners. ARA through clap-wrapper is verified for VST3 only; webviews inside hosts are unmeasured. Only RX 8 Standard is owned. All cycle counts are estimates.

## 12. Next action for Victor

Approve path C with build 1 as written in section 10, or choose path A or B instead.
