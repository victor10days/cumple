# 01 Frame: cumple as a full open-source DSP tool, benchmarked against iZotope RX

Date: 2026-10-08. Run: `docs/graph-runs/2026-10-08-rx-parity-landscape/`. Branch: `claude/laughing-darwin-15lo3a` (the run folder); build 1 follows on its own branch. This run reverses the 12 September decision in `docs/ROADMAP.md` ("automatic repair: outside a read-only QC tool").

## Question

Which open-source audio DSP code (GitHub and elsewhere) can be assembled, under licences compatible with cumple's MIT licence, into one coherent architecture whose modules match every iZotope RX tool, and in what order should cumple build them so that each one is scored against RX?

## Context

- cumple (`~/code/cumple`, MIT, Python 3.12, numpy/scipy/soundfile, streaming meters, 252 tests) is a delivery QC tool: check, diff, watch, fix (gain only), specs, desktop app. There is no STFT or resynthesis code anywhere (explored 2026-10-08).
- Victor decided on 2026-10-08 that cumple becomes a full open-source DSP tool with all RX features, benchmarked against RX 8.5.1 (installed here, most likely Standard: the 15 installed plugins match the Standard list exactly) and against the latest RX (12 Advanced; not owned, needs a trial or licence from Victor).
- Reverse engineering is black-box only: run RX on signals with a held clean reference, measure, then build from the literature and open code. No decompiling, no model extraction (EULA, and derived code would poison an MIT project).
- RX 8 has no CLI or AppleScript; its Batch Processor is the only repeatable path, run by Victor from a written recipe. Factory presets are readable XML with parameter names (De-click: Sensitivity, Algorithm; De-clip: Threshold, Quality, Limiter). The full RX 8 manual is on disk at `/Library/Application Support/iZotope/RX 8 Audio Editor/HTML Help/en/`.
- First build family chosen by Victor: De-click and De-clip on top of the foundation (STFT framework, `cumple repair`, RX harness).

## Constraints

- Every candidate carries: URL, licence as read from the repo's LICENSE file, language, last commit date, what it implements, evidence of quality (paper, tests, benchmark numbers, adoption), and a read date.
- Licence classes: MIT/BSD/Apache (vendorable or dependable), LGPL (dependable, not vendorable), GPL/AGPL (subprocess or reimplement from the paper only), unknown (gap).
- Pure-Python-plus-numpy/scipy preferred; a compiled or neural dependency goes behind an optional extra as `vad` does.
- No claim without a source; estimates labelled; "no open implementation found" is a valid cell.
- Prose without em or en dashes.

## Done looks like

- Branch: a table mapping every RX module in its family to the best two or three open implementations or to "gap", plus the architecture pattern the family needs.
- Skeptic: verifies at least five cited cells per branch by fetching, finds licence or date errors, names the optimistic shortcut.
- Recommendation: a stack (which repos become dependencies, which get reimplemented from papers, which are gaps), a build order of families, and the architecture for the foundation.
- Victor: decides the stack and the order; the plan for build 1 (foundation + De-click + De-clip) follows via superpowers:writing-plans.

## Shape and nodes

Diamond, 4 branches, dispatched together, no sibling paths:
- 02a restoration classics: De-click, De-clip, De-crackle, Mouth De-click, De-plosive, Interpolate, De-hum, Azimuth, Phase, Wow & Flutter, Dither, Resample, Normalize, Gain, Fade, Trim Silence, Waveform Stats, Signal Generator, EQ, EQ Match, Mixing, Markers.
- 02b noise and reverb: Spectral De-noise, Voice De-noise, De-reverb, Dialogue De-reverb, De-rustle, De-wind, De-ess, Breath Control, Guitar De-noise, De-bleed, Ambience Match, Spectral Repair, Spectral Recovery.
- 02c separation, speech and time: Dialogue Isolate, Music Rebalance, Scene Rebalance, Center Extract, Deconstruct, Stems View, Dialogue Contour, Time & Pitch, Variable Time, Variable Pitch, Find Similar, Repair Assistant, Leveler, Loudness Control, Streaming Preview.
- 02d frameworks, hosting and editors: module-chain and offline-processing architectures in open audio software, plugin hosting (VST3/AU), spectrogram editors and spectrum analyzers, batch processing, plus a licence-compatibility ruling for the whole stack and a comparison of how Audacity, SoX, pedalboard, torchaudio, ffmpeg filters and Essentia structure their effect pipelines.
- 03 skeptic (opus) -> 04 recommendation -> Victor.

## Victor's additions mid-run (2026-10-08, after 02a to 02d were dispatched)

- The engine must be FFT based (an STFT framework), which the branches already assume.
- A really cool looking spectral editing tool, for Victor's own use first.
- Delivered as a VST plugin (and so by implication AU and CLAP on macOS). This means a compiled core; Python alone cannot ship a plugin. Added node 02e below.
- Victor pasted two lists of open DSP libraries (DaisySP, KFR, FunDSP, Glicol, Faust, Pure Data, JamesDSP, Dragonfly Reverb, SOF, freeDSP, JUCE, STK, Maximilian, pedalboard, Essentia, Audioflux, pyAudioDspTools, liquid-dsp, FFTW, KissFFT, PFFFT, SciPy, librosa, ESP32-FFT). 02e treats them as candidates to verify, not as facts.
- 02e plugin and editor stack: plugin authoring frameworks and their licences (JUCE, iPlug2, DPF, nih-plug, CLAP, VST3 SDK, Faust's plugin export), GUI stacks that can draw a GPU spectrogram with brush and lasso selection inside a plugin window, FFT libraries by licence and speed, the language question (C++ versus Rust versus a compiled core with Python bindings so that cumple's CLI and the plugin share one DSP implementation), and what a "spectral editor in a plugin" has to do that an offline editor does not (ARA for whole-file access from a DAW, latency, undo).

## Out of scope

Writing code; running RX; buying RX 12; the editor's visual design itself (02d and 02e survey what exists and what stack can draw it).

## Budget

4 research branches (opus, web and gh search), 1 skeptic (opus), 1 recommender (sonnet). Branch reports under 1500 words each.
