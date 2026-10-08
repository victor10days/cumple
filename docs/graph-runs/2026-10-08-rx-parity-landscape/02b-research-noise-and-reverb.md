# 02b Research: noise and reverb (branch report, verbatim)

Inputs read: the brief; RX 8 manual pages on disk for all 13 modules, grepped for the method each uses; `gh api repos/<owner>/<repo>` for about 55 repos (L = LICENSE file read through the contents API; A = API field only); Hugging Face model API (`?blobs=true`) for weight sizes and licence tags; Zenodo API for VoiceFixer weights; the arXiv papers named below; cumple's `pyproject.toml` (`vad = ["onnxruntime>=1.17"]`); in the venv scipy 1.18.1 has `ShortTimeFFT` and onnxruntime 1.30.0 is installed. All read 2026-10-08.

| Key | Repo | Licence | Push / stars | Implements | Type, size, runtime | Training data | Evidence |
|---|---|---|---|---|---|---|---|
| NR | timsainb/noisereduce | MIT (A) | 2025-08-19 / 1881 | Spectral gating (stationary and non-stationary); random-phase `fftnoise` | Classical, numpy/scipy, torch optional | n/a | Adoption only |
| PRA | LCAV/pyroomacoustics | MIT (A) | 2026-07-17 / 1951 | `denoise/` (spectral subtraction, iterative Wiener, subspace); `adaptive/` | Classical, numpy | n/a | None seen |
| SPX | xiph/speexdsp | BSD-3 (L; API says NOASSERTION) | 2026-09-28 / 738 | `preprocess.c` suppressor; `mdf.c` MDF echo canceller | Classical, C | n/a | Adoption |
| AUD | audacity/audacity | GPLv3, many files GPLv2+ (L) | 2026-10-07 / 18672 | Noise Reduction effect | Classical; reimplement from description only | n/a | Adoption |
| RNN | xiph/rnnoise | BSD-3 (L) | 2025-02-22 / 5886 | Hybrid DSP plus GRU suppressor | Model; weight tarball 58.6 MB (HTTP Content-Length); C | OpenSLR crowdsourced speech (SLR83 is CC BY-SA 4.0); Xiph noise contributions, licence not stated | Valin, MMSP 2018 |
| DFN | Rikorose/DeepFilterNet | MIT or Apache-2.0 for code (L); weights not addressed | 2024-10-17 / 4799 | DeepFilterNet3 | Model; ONNX tar 7.98 MB holding three graphs (`enc`, `erb_dec`, `df_dec`); STFT and ERB features stay in the Rust libDF | DNS4: CC BY 4.0, CC BY-SA 3.0 (DEMAND), ODbL, public domain, per the DNS README | VB-DEMAND PESQ 3.17, STOI 0.944 (arXiv 2305.08227) |
| GTC | Xiaobin-Rong/gtcrn | MIT (A) | 2026-08-03 / 750 | Ultra-light speech enhancement | Model, 48.2K params, torch; ONNX through sherpa-onnx | DNS3 / VCTK-DEMAND | PESQ 2.87, STOI 0.940, SI-SDR 18.83 (README) |
| CUN | NVIDIA/CleanUNet | MIT (A) | 2023-10-11 / 354 | Waveform denoiser | Model, about 177 MB, torch | DNS 2020 | README credits CC BY-NC code from FAIR denoiser |
| FBD | facebookresearch/denoiser | CC BY-NC 4.0 (L), archived | 2023-03-14 / 1900 | Demucs denoiser | Excluded | | |
| MGP | HF speechbrain/metricgan-plus-voicebank | apache-2.0 tag | 2024-02-28 | 16 kHz enhancement | Model, 7.6 MB, torch | VoiceBank-DEMAND | Tagged PESQ/STOI |
| WPE | fgnt/nara_wpe | MIT (A) | 2025-03-19 / 576 | WPE: offline, block-online, frame-online | Classical, numpy (TF optional) | n/a | CHiME-5 report: at least as good as NTT's WPE |
| FDN | helianvine/fdndlp | MIT (A) | 2019-05-10 / 158 | WPE variant | Classical, numpy | n/a | None seen |
| VFX | haoheliu/voicefixer | MIT (A); weights CC BY 4.0 (Zenodo) | 2025-02-17 / 1383 | Restores noise, reverb, bandwidth and clipping | Model, 489 MB plus 136 MB vocoder, torch | VCTK, AISHELL-3, HQ-TTS, VD-Noise, simulated RIRs (arXiv 2109.13731) | Paper |
| SGM | sp-uhh/sgmse | MIT code (A); checkpoint licence not stated | 2026-05-12 / 773 | Diffusion SE and dereverb | Model, torch | WSJ0-REVERB (LDC); EARS-Reverb (EARS is CC BY-NC 4.0, per its repo page) | Paper |
| STM | sp-uhh/storm | MIT (A) | 2024-09-13 / 257 | WSJ0+Wind and WSJ0+Reverb checkpoints | Model, torch | WSJ0 (LDC, from memory) | Paper |
| RSE | resemble-ai/resemble-enhance | MIT (A); HF tag mit | 2024-12-03 / 2447 | Denoiser plus bandwidth enhancer | Model, 713 MB, torch | "high-quality 44.1kHz speech", not named | None seen |
| BRM | lukaszliniewicz/breath-removal + HF DongYANG/Respiro-en | MIT (A); HF tag mit | 2025-05-14 / 19 | Frame-wise breath detection (Respiro-en), then gain reduction | Model, 35.4 MB `.pt`, torch | LibriTTS-R, CC BY 4.0 (OpenSLR 141) | IoU 0.836, P 0.924, R 0.897 (arXiv 2402.00288) |
| AWD | airwindows/airwindows | MIT (L) | 2026-10-04 / 1248 | DeEss, DeBess, DeBez | Classical, C++ | n/a | Adoption |
| CALF | calf-studio-gear/calf | LGPL-2.1 (A) | 2026-09-07 / 806 | Deesser | Classical, C++ | n/a | Adoption |
| LSPD | lsp-plugins/lsp-plugins-deesser | LGPL-3.0 (A) | 2026-08-31 / 0 | README is still the plugin template | Immature | | |
| PAD | matousc89/padasip | MIT (A) | 2025-10-03 / 324 | NLMS and RLS adaptive filters | Classical, numpy | n/a | None seen |
| KAMIR | members.loria.fr/ALiutkus/kamir | AGPLv3 (page) | n/a | Interference reduction | MATLAB; paper only | | ICASSP 2015 |
| INP | ondrejmokry/InpaintingRevisited; rajmic/spectrogram-inpainting | No LICENSE file: unknown | 2022-12-20 / 3; 2026-01-22 / 1 | Janssen, SPAIN, Janssen-TF | Classical, MATLAB | n/a | Papers |
| DIFF | eloimoliner/audio-inpainting-diffusion | MIT code (A) | 2024-04-04 / 76 | Diffusion inpainting | Model; weight data and licence not stated | Not stated | JAES 2024 |
| GAC | andimarafioti/GACELA | MIT (A) | 2021-04-20 / 25 | GAN inpainting | Model | Not checked | Paper |
| TXS | cordutie/texstat | MIT (A) | 2026-03-06 / 3 | Texture-statistics loss | torch | n/a | DAFx 2025 |
| WGEN | audiolabs/SC-Wind-Noise-Generator | MIT (A) | 2024-04-23 / 55 | Synthetic wind noise | Test signals only | | |
| APB | yxlu-0102/AP-BWE | MIT for code and weights (README) | 2025-04-15 / 201 | Speech bandwidth extension | Model, torch, size not stated | VCTK-0.92 | 8 to 48 kHz: LSD 0.84, ViSQOL 3.35 (arXiv 2401.06387) |
| HGB | brentspell/hifi-gan-bwe | MIT (A) | 2023-10-20 / 224 | Bandwidth extension | Model, 1M params, torch | VCTK plus DNS noise | None |
| ASR | haoheliu/versatile_audio_super_resolution | MIT (A); HF weights apache-2.0 | 2025-08-27 / 1974 | AudioSR | Model, 6.18 GB, torch | MUSDB18-HQ, MoisesDB, MedleyDB, FreeSound, OpenSLR | VCTK LSD (paper) |
| MSR | modelscope/ClearerVoice-Studio | Apache-2.0 (A) | 2025-08-14 / 4545 | MossFormer2 SE_48K (221.6 MB) and SR_48K (439 MB) | Model, torch | "open-sourced and private data" | None |
| DNSMOS | microsoft/DNS-Challenge | Code MIT (README) | 2024-07-25 / 1471 | Non-intrusive quality metric | ONNX, 1.16 MB | | For the test harness |

Libraries: pedalboard is GPL-3.0 (L), not vendorable, has none of these modules. torchaudio is BSD-2 (A), in a maintenance phase, features removed in 2.9 (README). librosa is ISC (A): `stft`, `istft`, `griffinlim`, `softmask`, `nn_filter`, `hpss`, `pcen`.

| RX module | What RX does (manual) | Best open picks | Classical or model | Papers that define the state of the art |
|---|---|---|---|---|
| Spectral De-noise | Learn a noise profile, then subtract | NR, PRA, SPX (AUD by description only) | Classical | Boll 1979; Ephraim and Malah 1984/85; Martin 2001; Cohen 2003 |
| Voice De-noise | Zero-latency adaptive threshold | SPX, NR (non-stationary); model option RNN, DFN or GTC | Classical first | Valin 2018; Schröter 2023; Rong 2024 |
| De-reverb | Learn wet/dry ratio per band and the tail | WPE, FDN; late-reverb subtraction from the paper | Classical | Nakatani 2010; Lebart 2001 |
| Dialogue De-reverb | Machine-learning separation | VFX, SGM (NC/LDC data), RSE | Model | Richter 2023 (SGMSE+); Lemercier 2023; Liu 2022 |
| De-rustle | Machine learning trained on rustle | Gap (searched GitHub "rustle", "lavalier", "clothing noise", plus the web); DFN as a fallback | Model | Wichern and Lukin, DAFx 2018 |
| De-wind | Low-frequency processing that tracks the noise floor | No open code (searched GitHub "wind noise reduction", "wind noise", "wind noise suppression"; also the web); STM checkpoint (LDC data); WGEN for test data | Classical | Nelke 2014 (signal centroids); Lemercier 2023 |
| De-ess | Classic (broadband gain) and Spectral (high band only) | AWD, CALF (reimplement), LSPD | Classical | No defining paper found |
| Breath Control | Detect breaths; Gain or Target mode | BRM + Respiro-en | Model (35 MB) | Yang 2024 |
| Guitar De-noise | Sections for hiss, pick and squeak (squeaks up to 1000 ms) | Gap for pick and squeak (3 searches); hiss goes to NR | Unknown | None found |
| De-bleed | Learns the relationship between the bleed track and the active track; FFT-based | SPX `mdf.c`, PAD, PRA adaptive; KAMIR from the paper only | Classical | Prätzlich 2015 (KAMIR); Soo and Pang 1990 (MDF) |
| Ambience Match | Learns the "lowest common denominator" noise and rejects silence | NR `fftnoise` plus a learned profile; TXS | Classical | McDermott and Simoncelli 2011 |
| Spectral Repair | Attenuate, Replace (interpolate from surrounding audio), Pattern | INP reimplemented from the papers; librosa `griffinlim`; DIFF, GAC | Classical first | Janssen 1986; Mokrý 2020; Janssen-TF (arXiv 2409.06392); Moliner 2024 |
| Spectral Recovery | Adds missing upper frequencies to band-limited speech | APB, HGB, VFX; ASR is 6.18 GB | Model | Lu 2024 (AP-BWE); Liu 2023 (AudioSR) |

Architecture this family needs: one STFT engine on scipy's `ShortTimeFFT`, sqrt-Hann analysis and synthesis windows with 75% overlap (noisereduce defaults hop to win/4) and a COLA check; n_fft from 512 to 8192 since RX exposes FFT size as a resolution trade-off (De-bleed manual). A processor is a gain function over the complex STFT with shared stages: noise profile learning (percentile or minimum statistics over a selection, or an adaptive tracker); a gain rule (subtraction, Wiener or MMSE-LSA); a reduction floor in dB; time and frequency mask smoothing (NR's `freq_mask_smooth_hz`, `time_mask_smooth_ms`); an "output noise only" option. Learn and process are separate steps as in RX (Learn appears in Spectral De-noise, De-reverb, De-bleed, Ambience Match, Spectral Recovery); profiles save to JSON so the harness can replay them. Region processors (Spectral Repair, Ambience Match, Breath) take a time-frequency selection plus its surrounding audio; they synthesise with random phase or Griffin-Lim. De-bleed takes two inputs: align by cross-correlation, then a per-bin frequency-domain adaptive filter (MDF). Models plug in as gain providers through an optional extra as `vad` does: weights fetched on first use and pinned by sha256 (RNNoise's `download_model.sh` pattern), never in the wheel; DFN's ONNX graphs expect libDF's ERB features, so those features must be ported to numpy; torch-only models (VFX, Respiro-en, APB) need an ONNX export nobody has tried, or a separate `torch` extra. Harness: SI-SDR, PESQ and STOI with a clean reference; DNSMOS ONNX without.

Unknowns: weights licences for DFN, SGM, CUN, DIFF and HGB (only code licence stated); RNNoise's compiled model size and the Xiph noise contributions' licence; AudioSR's music training data licences, HQ-TTS's licence, MossFormer's private data; whether DFN's ONNX graphs match when fed numpy features (not tested); every classical paper cited from memory, not fetched; US patent 10249322 (single-mic wind reducer using signal centroids) assignee and scope unverified; VCTK's licence (DNS README says ODC-By v1.0, Edinburgh's `license_text.txt` not read); checkpoint sizes for NU-Wave 2 (BSD-3), AERO (MIT), FullSubNet (MIT) not checked.

Recommendation from this angle: classical wins on numpy/scipy from MIT, BSD, ISC code and the papers: Spectral De-noise, Voice De-noise, De-reverb (WPE), De-ess, De-bleed (MDF), Ambience Match, Spectral Repair (Janssen-TF), plus De-wind once the patent is checked. One optional ONNX extra carries DeepFilterNet3 (8 MB, MIT or Apache-2.0, DNS4 data) or GTCRN for the model side of Voice De-noise and as De-rustle fallback; Breath Control needs Respiro-en (35 MB, MIT, CC BY 4.0 data); Spectral Recovery uses AP-BWE (MIT weights, VCTK) with VoiceFixer as the larger option for Dialogue De-reverb; De-rustle and Guitar De-noise squeak stay gaps.

SUMMARY: seven of 13 modules can be built classically on MIT, BSD or ISC sources; four need models; De-rustle and guitar squeak have no open implementation. CONCERNS: most repos licence code but not weights; several models trained on non-commercial or LDC data; the de-wind method may be patented; DeepFilterNet's ONNX graphs need ported Rust feature code.
