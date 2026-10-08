# 02a Research: restoration classics (branch report, verbatim)

Inputs read: the brief; the RX 8 manual on disk (21 module pages); the RX 8 factory preset XML; cumple meters; `gh api repos/<o>/<r>`; `gh search repos` for declipping, "audio declipping", "spade declipping", declick, decrackle, "audio restoration", "audio inpainting", dehum, "hum removal", "wow and flutter", gcc-phat, "phase rotation audio", "noise shaping dither", "plosive removal", "mouth click removal", "lip smack", "matching equalizer"; web pages ffmpeg-filters.html, ipol.im/pub/art/2015/64 and 2018/23, arxiv 2007.07663, rajmic.github.io/declipping2020, perso.ens-lyon.fr/remi.gribonval/?p=647, essentia.upf.edu/algorithms_reference.html, src.infinitewave.ca. All read 2026-10-08. GitHub search hit its rate limit once; affected queries re-run.

Candidate register. Licence classes: P = permissive, L = LGPL, G = GPL/AGPL, U = no licence found. [gh] = gh api licence field, [file] = LICENSE, COPYING or source header, [page] = publisher's page.

| ID | URL | Licence | Language | Last push | Stars | Quality evidence |
|---|---|---|---|---|---|---|
| C1 | github.com/audacity/audacity | G, GPL-2+/3 [file] | C++ | 2026-10-07 | 18672 | adoption |
| C2 | github.com/FFmpeg/FFmpeg | L, LGPL-2.1+ [file headers] | C | 2026-10-08 | 64851 | adoption; af_adeclick.c last changed 2026-06-30 |
| C3 | github.com/AlisterH/gwc | G, GPL-2+ [file] | C | 2026-03-02 | 31 | none seen |
| C4 | Oudre's IPOL articles 2015/64 and 2018/23 | G, GPL-3.0+ [page] | language not checked | published 2015-11-21 and 2018-10-17 | n/a | peer-reviewed in IPOL |
| C5 | github.com/gburlet/audio-restore | P, MIT [gh] | MATLAB | 2022-09-19 | 7 | course paper; Godsill AR and sinusoid+AR |
| C6 | github.com/rajmic/declipping2020_codes | G, GPL-3.0 [gh] | MATLAB | 2023-10-16 | 53 | IEEE JSTSP 2021 survey |
| C7 | SPADE Toolbox, hal.inria.fr/hal-03024116 | P, BSD-3 [page, author's post of 2021-02-15] | MATLAB | n/a | n/a | papers |
| C8 | github.com/andryr/spade-declipping | P, MIT [gh] | MATLAB | 2023-12-14 | 9 | none seen |
| C9 | github.com/ondrejmokry/InpaintingAutoregressive | U [gh] | MATLAB | 2026-09-18 | 3 | EUSIPCO 2025 paper with a listening test |
| C10 | github.com/eloimoliner/CQTdiff | P, MIT [gh] | Python, neural | 2023-03-14 | 123 | ICASSP 2023 |
| C11 | github.com/eloimoliner/denoising-historical-recordings | P, MIT [gh] | Python, neural | 2024-11-12 | 125 | ICASSP 2022 |
| C12 | github.com/HENDRIX-ZT2/pyaudiorestoration | G, GPL-2.0 [gh] | Python | 2026-09-30 | 117 | none seen. Tools: wow and flutter, hum speed match, differential EQ, lag and azimuth sync |
| C13 | github.com/mne-tools/mne-python | P, BSD-3 [gh] | Python | 2026-10-07 | 3537 | adoption. `notch_filter(method='spectrum_fit')` |
| C14 | github.com/nbara/python-meegkit | P, BSD-3 [gh] | Python | 2026-08-21 | 230 | ZapLine paper. `dss_line` |
| C15 | github.com/scipy/scipy | P, BSD-3 [gh] | Python | 2026-10-08 | 15090 | adoption. iirnotch, iircomb, hilbert, resample_poly, firwin2, chirp |
| C16 | github.com/x42/phaserotate.lv2 | G, GPL-2.0 [gh] | C | 2026-09-07 | 24 | none seen |
| C17 | github.com/unevens/hiir | P, WTFPL [gh] | C++ | 2021-11-01 | 48 | none seen; Hilbert allpass pairs |
| C18 | github.com/xiongyihui/tdoa | P, Apache-2.0 [gh] | Python | 2024-04-16 | 217 | none seen; GCC-PHAT |
| C19 | github.com/chirlu/sox | L for libsox, G for sox.c [file]; dither.c LGPL-2.1+ [header] | C | 2023-11-24 | 967 | adoption |
| C20 | github.com/pytorch/audio | P, BSD-2 [gh] | Python | 2026-10-07 | 2955 | adoption |
| C21 | github.com/libsndfile/libsamplerate | P, BSD-2 [gh] | C | 2026-08-13 | 746 | Infinite Wave |
| C21 binding | tuxu/python-samplerate | P, MIT [gh] | Python | 2026-03-22 | 56 | none seen |
| C22 | github.com/chirlu/soxr | L, LGPL-2.1+ [file] | C | 2023-11-14 | 181 | Infinite Wave |
| C22 binding | dofuuz/python-soxr | L, LGPL-2.1+ [file] | Python | 2026-09-26 | 114 | none seen |
| C23 | github.com/avaneev/r8brain-free-src | P, MIT [gh] | C++ | 2026-09-30 | 746 | Infinite Wave |
| C24 | github.com/sergree/matchering | G, GPL-3.0 [gh] | Python | 2026-10-07 | 2654 | adoption |
| C25 | github.com/brummer10/GxMatchEQ.lv2 | G, GPL-3.0 [gh] | C | 2021-01-20 | 19 | none seen |
| C26 | github.com/pyfar/pyfar | P, MIT [gh] | Python | 2026-10-06 | 138 | none seen. bell, shelf, allpass filters; sine, sweeps, impulse |
| C27 | github.com/csteinmetz1/pyloudnorm | P, MIT [gh] | Python | 2026-01-04 | 783 | already a cumple dev dependency |
| C28 | github.com/MTG/essentia | G, AGPL-3.0 [gh] | C++ | 2026-10-02 | 3762 | adoption |
| C29 | github.com/librosa/librosa | P, ISC [gh] | Python | 2026-10-06 | 8659 | adoption |
| C30 | github.com/jiaaro/pydub | P, MIT [gh] | Python | 2026-03-19 | 9803 | adoption |
| C31 | github.com/felixpatzelt/colorednoise | P, MIT [gh] | Python | 2023-10-09 | 222 | none seen |
| C32 | github.com/iluvcapra/wavinfo | P, MIT [gh] | Python | 2026-10-01 | 44 | none seen; reads cue markers and labels |
| C33 | github.com/MediaArea/BWFMetaEdit | public-domain intent [file License.html] | C++ | 2026-09-23 | 71 | none seen |
| C34 | github.com/szabiz/POP-FILTER-PRO-2.00 | G, GPL-3.0 [gh] | Python | 2026-09-17 | 1 | none seen |

Findings:

| RX module | Best open implementations | What they do | State-of-the-art paper where the open code is weaker | Gap? |
|---|---|---|---|---|
| De-click | C2 adeclick (L); C3 declick.c (G); C1 ClickRemoval (G) | C2 detects clicks from the AR residual and interpolates with AR. Defaults: window 55 ms, overlap 75%, AR order 2%, threshold 2. C3 uses LSAR. C1 is a threshold and width detector | Godsill & Rayner 1998; Oudre IPOL 2015 (C4); C5 | No. RX's multi-band modes have no open equivalent |
| De-clip | C7 SPADE (P); C6, 19 methods (G); C2 adeclip (L); C1 clipfix.ny cubic spline (G) | Sparse and AR reconstruction of clipped samples | Záviška et al., JSTSP 2021: social shrinkage, NMF, weighting and SPADE are "preferred choices", SPADE attractive on compute. C10 is a diffusion model | No |
| De-crackle | C3 decrackle.c (G); C11 (P, neural) | Dense small-click repair | Rajmic & Klimek, DAFx 2004 (wavelets) | Thin: no permissive classical code |
| Mouth De-click | None dedicated; C2 used generically | n/a | arXiv 2202.07750 (detection only); a USPTO patent text | Yes. Checked by GitHub search, web search and paper search |
| De-plosive | C34 only (G, 1 star) | Low-frequency pop removal | RX docs: detection at 20-80 Hz. A patent describes zero-crossing detection plus high-pass | Yes, for permissive code |
| Interpolate | C1 Repair (LSAR, maximum 128 samples; RX allows up to 4000); C9 (U); C4 2018 (G) | AR gap filling | Mokrý & Rajmic, EUSIPCO 2025: gap-wise Janssen is best among AR methods; Janssen 1986 | No, reimplement from the papers |
| De-hum | C15 iirnotch and iircomb; C13 spectrum_fit; C14 ZapLine (multichannel) | Notch banks; fitting sinusoids and subtracting them | RX adds an adaptive mode and linear-phase filters; ZapLine (de Cheveigné 2019) | Partial: no audio-specific adaptive repo found |
| Azimuth | C12 pytapesynch (G); C18 GCC-PHAT; C2 axcorrelate and adelay | Inter-channel lag estimation and correction | Knapp & Carter 1976 | Partial |
| Phase | C2 aphaseshift (L, HIIR-based); C17; C15 hilbert; C16 (G, fixed rotation only) | Fixed phase rotation | Välimäki et al., JAES 2022, "Audio Peak Reduction Using Ultra-Short Chirps", doi 10.17743/jaes.2022.0011 | The adaptive mode is a gap |
| Wow & Flutter | C12 pyrespeeder (G); a McGill MUMT501 student project (U, reports failure on gramophone records) | Speed curve, then variable sinc resampling | Godsill, ICASSP 1994; Maziewski, Archives of Acoustics 2008 | Yes, for permissive code |
| Dither | C19 dither.c (L, 8 shaping curves incl. Lipshitz, E-weighted, Shibata); C2 swresample (L); C20 `dither` (P: TPDF, RPDF, GPDF and a noise-shaping flag) | TPDF dither plus error-feedback noise shaping | Lipshitz, Wannamaker & Vanderkooy, JAES 1992 | No |
| Resample | C21 (P); C23 (P, no Python binding found); C22 (L); C15 resample_poly | Band-limited sample-rate conversion | Not weaker: Infinite Wave lists SoX VHQ, r8brain and Secret Rabbit Code next to RX 8.1 and RX 11 | No |
| Normalize | numpy; C27; C30 normalize | Gain to a sample-peak target (RX Normalize is sample peak only) | n/a | Trivial |
| Gain | numpy; cumple fix.py | Static gain | n/a | Trivial |
| Fade | C2 afade; C30 | Fade curves. RX shapes: Log, Linear, Cosine, Equal power | n/a | Trivial |
| Trim Silence (RX 12 only) | C29 effects.trim and split; C30 silence.py; C2 silenceremove | Silence detection and removal. RX 12 parameters: Threshold, Silence, Post Roll, Crossfade | n/a | Trivial |
| Waveform Stats | cumple's own bs1770.py, truepeak.py, measure.py; C2 astats; C28 detectors (G) | cumple already measures momentary and short-term maximum, LRA, true peak, clipping, DC and RMS | n/a | Mostly done already |
| Signal Generator | C15; C26; C31; C2 sine and anoisesrc | Tones, sweeps, coloured noise | n/a | Trivial |
| EQ | C15; C26; C1 Equalization (G) | Biquad (IIR) and linear-phase FIR EQ. RX offers both "Analog (IIR)" and "Digital Linear Phase (FIR)" | n/a | Trivial |
| EQ Match | C24 (G); C25 (G); C12 differential EQ (G) | C24: average STFT spectrum, LOWESS smoothing, linear-phase FIR, mid/side processing | n/a | Yes for permissive code, but the algorithm is short to reimplement |
| Mixing | numpy channel matrix; C2 pan | Left and right output mix percentages | n/a | Trivial |
| Markers | C32 (reads cue markers); C33 | WAV/BWF cue chunk read and edit. RX exports markers as tab-delimited text | n/a | Writing cue chunks from Python is a small gap |

Architecture this family needs: three engines sharing one module contract. (1) Block time-domain engine with overlap and lookahead, streamable: De-click, De-clip-AR, Interpolate, De-crackle, Dither, Gain, Fade, Mixing, IIR EQ, IIR De-hum, generators. RX ships a "LOW LATENCY" De-click mode and documents latency for its linear-phase De-hum. (2) STFT analysis and resynthesis (COLA overlap-add): multi-band click modes, A-SPADE (frame-wise ADMM), De-plosive, adaptive De-hum, linear-phase EQ, EQ Match learn. (3) Whole-file two-pass (analyse, then render): Normalize, EQ Match (Learn), Wow & Flutter (speed curve then variable resampling), adaptive Azimuth, Phase "Suggest", De-clip histogram "SUGGEST", Trim Silence. Shared contract: a parameter object mirroring RX's preset ParamIDs; per-channel or linked switch; a residual output ("OUTPUT CLICKS ONLY", "OUTPUT CRACKLE ONLY", "OUTPUT HUM ONLY"); processing limited to a selection with crossfades at its edges. Parameter names read from the factory presets: De-click "Declicker Algorithm" (manual adds Sensitivity, Frequency skew, Click widening); De-clip "Single Band Threshold" (manual adds Quality, Post-limiter); De-crackle "Decrackler Strength", "Decrackler Quality"; Mouth De-click Sensitivity, Frequency skew, Click widening; De-plosive "Upper Repair Frequency" (180), Sensitivity, Strength; De-hum "Num Harmonics", "Harmonic Gain n"; Dither "Dither Shaping Amount"; Resample "Resampler Cutoff" (0.961), "Resampler Samplingrate"; Phase "Chop Phase Left/Right", "Autophase Enable"; Wow & Flutter rates Slow 0-0.5 Hz, Medium 0.5-2 Hz, Fast 2-8 Hz, flutter 8-40 Hz.

Unknowns: SPADE Toolbox licence from the author's web page, archive licence file not opened; the IPOL code language, zita-resampler's licence, Signalsmith dsp library contents, individual airwindows plugin licences and the JUCE licence behind small plugin repos not checked; no r8brain Python binding found (one search under rate limiting); most small repos show no quality evidence and no benchmarks were run; RX 12 Trim Silence parameters come from marketing and a retailer page; RX internals are a black box.

Recommendation from this angle: build De-click, De-clip and Interpolate first as one numpy AR engine: AR-residual detection modelled on ffmpeg adeclick's published parameters; gap-wise Janssen and LSAR interpolation written from Godsill & Rayner, Janssen 1986 and Mokrý & Rajmic 2025; A-SPADE ported from Kitić 2015's pseudocode with the BSD-3 SPADE Toolbox as reference. ffmpeg's adeclick and adeclip as a subprocess are the open baseline in the RX harness. GPL sources (Audacity, GWC, IPOL) read only for behaviour, never translated.

SUMMARY: classic restoration modules have solid open code or papers; Mouth De-click, De-plosive, Wow & Flutter, adaptive Phase and permissive EQ Match are gaps or GPL-only. CONCERNS: several key references are GPL or unlicensed so clean-room discipline is needed; RX's multi-band and adaptive modes have no open equivalent; quality evidence for small repos is mostly absent.
