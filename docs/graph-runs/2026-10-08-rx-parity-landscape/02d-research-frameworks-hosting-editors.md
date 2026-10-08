# 02d Research: frameworks, hosting, editors, licensing

Date: 2026-10-08. Run: `docs/graph-runs/2026-10-08-rx-parity-landscape/`. Branch report, kept verbatim as a receipt; its "GPL optional extra is legal" row is overruled in `04-recommendation.md` (section 7), which keeps the frame's rule.

Inputs read: the brief; cumple `measure.py`, `bs1770.py` (head), `reader.py`, `fix.py`, `pyproject.toml`, `CONTRIBUTING.md`; `gh api repos/<r>`, `/commits?per_page=1`, LICENSE or COPYING files; source files Audacity `ClickRemovalEffect.h`, `EffectInterface.h`, `au3/src/Experimental.cmake`, FFmpeg `filters.h`, `af_adeclick.c`, SoX `sox.h`, Essentia `framecutter.h`; pages: pedalboard reference, Audacity manual (Macros, Scripting), Essentia streaming, torchaudio transforms, GNU GPL FAQ, GNU licence list, OSI OSD, CC FAQ, MPL FAQ, Apache-2.0 text, SPDX list, PyPI JSON. All read 2026-10-08.

Pipeline architectures:

| Framework | Licence (source) | Lang | Last commit | Stars | Parameters | Streaming | Chain, presets | Channels, rate |
|---|---|---|---|---|---|---|---|---|
| Audacity github.com/audacity/audacity | GPL-3, files default GPLv2+ (LICENSE.txt) | C++ | 2026-10-07 | 18672 | `EffectParameter{member,"Threshold",200,0,900,10}` | `ProcessInitialize(settings, sampleRate, chanMap)` then `ProcessBlock`; ClickRemoval does a whole-track `Process` | Macros are .txt files; `SaveUserPreset`/`LoadFactoryPreset` | `GetAudioInCount/OutCount` |
| SoX github.com/chirlu/sox (mirror) | libsox LGPL, sox.c GPL (COPYING) | C | 2021-05-09 | 967 | argv to `getopts` | `start/flow/drain/stop` | shell line | `SOX_EFF_MCHAN`, `SOX_EFF_RATE` flags |
| FFmpeg libavfilter | LGPL-2.1+, GPL parts opt-in (LICENSE.md, adeclick header) | C | 2026-10-08 | 64851 | AVOption {name, help, type, default, min, max} | `activate()` frame push and pull | filtergraph text; `process_command` | format negotiation `query_func` |
| pedalboard github.com/spotify/pedalboard | GPL-3 (LICENSE) | C++/Py | 2026-10-07 | 6340 | properties; `parameters` dict | `process(x, sr, buffer_size=8192, reset=True)`; `reset=False` streams; 64-bit input becomes 32-bit | nestable `Pedalboard`/`Chain`/`Mix`; no saving documented; VST3 `preset_data` | channels inferred from shape |
| torchaudio github.com/pytorch/audio | BSD-2 (LICENSE) | Py | 2026-10-07 | 2955 | `nn.Module` constructor args | whole tensor | `nn.Sequential`; "maintenance phase" since 2.8/2.9 | rate passed to constructor |
| Essentia github.com/MTG/essentia | AGPL-3 (COPYING.txt) | C++ | 2026-10-02 | 3762 | `declareParameter(name, desc, "[1,inf)", default)` | network with acquire/release (frame and hop) | graph in code | n/a |
| DawDreamer github.com/DBraun/DawDreamer | GPL-3 (LICENSE) | C++ | 2026-10-02 | 1320 | `set_parameter` | `RenderEngine(sr, 512)`, `render(s)` | `load_graph` | n/a |
| pyo github.com/belangeo/pyo | LGPL-3 (LICENSE) | C/Py | 2026-10-07 | 1454 | attributes | `Server(audio="offline")` batch example | script | n/a |
| Csound github.com/csound/csound | LGPL-2.1 (COPYING) | C | 2026-10-07 | 1509 | opcode args | ksmps block | orchestra and score text | n/a |
| Faust github.com/grame-cncm/faust | compiler LGPL-2.1+ (COPYING.txt) | C++ | 2026-10-06 | 3178 | UI primitives | generated C++ | n/a | n/a |
| Ardour / Tenacity / Zrythm | GPL-2+ / GPL-2 / AGPL-3+ plus trademark terms | C++ | 10-07 / 09-25 / 10-04 | 5325 / 811 / 3144 | LV2 (ISC) ports in TTL | realtime DAW | sessions | n/a |
| cathar github.com/vbasky/cathar | MIT OR Apache-2.0 (both LICENSE files) | Rust | 2026-09-21 | 15 | CLI flags | whole file in memory (`Vec<Vec<f32>>`) | JSON `chain` preset, `batch` | `map_channels` |

Hosting and editors:

| Candidate | Licence (source) | Last commit | Stars | What it does |
|---|---|---|---|---|
| pedalboard | GPL-3 | 2026-10-07 | 6340 | Hosts VST3 on all three OSes and AU on macOS from Python; `show_editor` only on the main thread; built on JUCE 6, GPL-3 (README) |
| DawDreamer | GPL-3 | 2026-10-02 | 1320 | Hosts VST and Faust in a graph |
| Carla github.com/falkTX/Carla | GPL-2+ (README; API field empty) | 2026-03-19 | 2182 | Standalone plugin host |
| JUCE github.com/juce-framework/JUCE | AGPL-3 or the commercial JUCE 9 EULA (LICENSE.md) | 2026-09-28 | 8957 | Framework |
| VST3 SDK github.com/steinbergmedia/vst3sdk | MIT (LICENSE.txt) | pushed 2026-08-11 | 2363 | A permissive host is now legally possible, but three gh searches found no permissive Python host |
| Audacity spectral tools | GPL | as above | as above | Rectangle selection, Spectral Delete, Multi tool. Brush code exists (`BrushHandle`, `SpectralDataManager`), but `#BRUSH_TOOL` is commented out in Experimental.cmake |
| Sonic Visualiser | GPL-2+ (README) | 2025-12-07 | 904 | Analysis and Vamp plugins, no repair |
| Friture github.com/tlecomte/friture | GPL-3 (API) | 2026-08-11 | 1123 | Realtime analyzer, Python |
| spek github.com/alexkay/spek | GPL-3 (API) | 2023-07-15 | 3451 | Static spectrogram viewer |
| ISSE isse.sourceforge.net | GPL-3 (About page) | 0.2.0 alpha, 2013 | n/a | Paint on a spectrogram to separate sources |
| Noise Canvas github.com/robclouth/noise-canvas | AGPL-3 (API) | 2026-08-25 | 302 | Paints effects into a spectrogram with GPU shaders; UX reference only |
| Ampter github.com/echometerain/Ampter | GPL-3 (API) | pushed 2024-01-26 | 6 | Paint effects onto a spectrogram |
| wavesurfer.js github.com/katspaugh/wavesurfer.js | BSD-3 (LICENSE) | 2026-10-07 | 10431 | Spectrogram (web worker) and regions plugins |
| AudioMass github.com/pkalogiros/AudioMass | MIT (LICENSE) | 2026-08-20 | 3009 | Browser waveform editor |

Licence ruling (the branch's reading, not legal advice):

| Licence | Core dependency | Optional extra | Subprocess | Vendor code | Frozen app |
|---|---|---|---|---|---|
| MIT, BSD, ISC | yes | yes | yes | yes, keep notice | yes |
| Apache-2.0 | yes | yes | yes | yes, carry NOTICE (section 4(d)) | yes |
| MPL-2.0 | yes | yes | yes | MPL files stay MPL ("file-level" copyleft, MPL FAQ) | yes |
| LGPL | yes, as a shared library | yes | yes | no, reimplement from the paper | yes if dynamic, with a source offer (FAQ #LGPLStaticVsDynamic) |
| GPL-2/3 | no: "the work as a whole must be licensed under the GPL" (#IfLibraryIsGPL) | legal, since MIT is GPL-compatible, but any bundle is then GPL | yes: "pipes, sockets and command-line arguments" (#MereAggregation) | no | no |
| AGPL-3 | no | no | yes | no | no |
| CC-BY-NC weights | no: fails OSD 6; SPDX lists it as neither FSF-free nor OSI-approved; CC advises against CC for software | no | no | no | never bundled; at most a path the user supplies, off by default |

Precedents already in cumple: soundfile wheels ship their own libsndfile (LGPL-2.1), the LGPL pattern already in use; PyInstaller carries a bootloader exception (PyPI); `pywebview[qt]` pulls in PyQt6, which is GPL-3.0-only (PyPI); PySide6 is LGPL-3.0, so switching would avoid this.

Existing open RX-like suites: cathar is the closest: a CLI and library with declick, declip (A-SPADE), dehum, WPE dereverb, JSON chains, batch, and a `stats` command that "prints a suggested `de-*` command"; young (created 2026-06-17, 15 stars). CleanTake (github.com/pavangupta352/cleantake; MIT, Python, 2026-09-08, 12 stars) recovers dialogue from backup recorders. Audacity and Tenacity are general editors with some repair effects. No dialogue-first open suite comparable to RX found (three web searches plus gh "audio repair" and the gh spectrogram topic).

Recommended architecture for cumple: module interface (`cumple/repair/`): each module declares `id`, `version`, and `Params`, a pydantic model with `extra="forbid"` and ranges, units and help text (the AVOption, EffectParameter and declareParameter pattern); the JSON schema drives the app's forms; it also declares `kind` (stream, two_pass, region), `context_frames` and `latency_frames`; methods `__init__(fs, channels, roles, params)`, `process(block)`, `flush()`, `report()`; a two-pass module's analyser is a meter that keeps statistics, never audio, like `LoudnessMeter.feed/result`. Runner: reads with `iter_blocks` at `DEFAULT_BLOCK_FRAMES`, float64 throughout; keeps a context overlap per module (SoX flow/drain, Essentia acquire/release) and compensates latency; writes as `fix.apply` does (same subtype, temporary name, `os.replace`, refuses dst == src); a shared streaming STFT/ISTFT class holds window and hop state. Streaming is the default; region modules read only the selection plus context; a whole-file module must say so and the runner checks memory first. Per channel by default with a `linked` option and roles passed through; only a resample module may change rate. Chains and presets: YAML in the strict style of the specs profiles; a one-line CLI form `declick(sensitivity=5),declip(threshold=-1)` that round-trips to YAML; built-in presets in `src/cumple/repair/presets/`, user presets in `~/.config/cumple/repair/` override by id. Receipt: every output gets a sidecar JSON with the chain, module versions, input SHA-256, before and after `measure()` summaries, each module's report; `--residual` writes input minus output. Models: one extra per neural module, imported only when asked; weights out of the wheel, fetched to `~/.cache/cumple/models/` with a pinned hash, checked against a licence allowlist that refuses NC. Desktop app: a Repair tab where numpy computes spectrogram tiles and a canvas draws them (own code or wavesurfer.js, BSD-3); selection starts with rectangles; brush later; preview renders only selection plus context; Render writes the copy and the receipt; the edit list doubles as undo. Batch: `cumple repair DIR --preset ... --out DIR2`, one process per file; `watch` can trigger it; `--suggest` maps findings to light, medium or strong chains (cathar `stats` pattern; Repair Assistant page not fetched). Plugin hosting: none in process; if ever needed, a separate GPL helper built on pedalboard, distributed apart, talking through files and arguments.

Unknowns: whether the Linux frozen build bundles PyQt6 and whether builds are onefile or onedir (affects LGPL relinking; workflow files outside the brief); sox_ng's GPLv2 change from a commit title only; Faust's exceptions for generated code from secondary sources; Carla's licence from README only; ocenaudio and SpectraLayers being closed not verified; gh "audio restoration" search rate-limited; whether a GPL helper fed audio through files counts as a separate program is, per GNU, "a legal question".

Recommendation from this angle: build cumple's own streaming module runner in pure numpy/scipy: pydantic parameters, YAML chains, a receipt per output, copy-only writes; FFmpeg (LGPL) and SoX as subprocess references for scoring; GPL and AGPL code (pedalboard, Essentia, Audacity) studied from papers and run as references, never imported. Read cathar's design and Audacity's spectral tools as references; since cathar is MIT/Apache its code can be ported; build the spectrogram canvas on BSD or MIT web code.

SUMMARY: no open dialogue-first RX suite exists; cathar (MIT/Apache, Rust) is the closest; build a native streaming pydantic and YAML module runner; GPL and AGPL code goes subprocess-only or nowhere. CONCERNS: cumple's `app-qt` extra already pulls in GPL PyQt6; the VST3 SDK is now MIT but no permissive Python host exists.
