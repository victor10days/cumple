# The dialogue gate on real programmes, cumple 0.1.0

Generated 2026-09-05 by `scripts/dialogue_benchmark.py`. cumple's dialogue-gated loudness uses a heuristic speech detector labelled an approximation of Dolby Dialogue Intelligence. This report measures the approximation against films that publish a music-and-effects version of their mix, and shows the speech share the detector reports on clean speech, on music and effects without dialogue, and on dialogue-driven films. Silero VAD (threshold 0.5) was available and is shown as a second, independent opinion. The recordings are fetched by `scripts/fetch_real_dialogue.sh` and are not redistributed.

## Films with a music-and-effects version as ground truth

The M&E is aligned to the mix, both are band-passed to the detector's 150 Hz to 4 kHz speech band, and the level difference per 20 ms frame is taken. Frames without dialogue sit at a baseline offset (the 10th percentile of that difference); a frame is dialogue when the mix sits 3 dB or more above that baseline, dilated over one second the way the detector dilates its own frames. The reference dialogue-gated value is BS.1770-1 (absolute gate only) over the 400 ms blocks that are at least half dialogue by that mask; the product's value is the same computation with the detector's mask instead. The two files were limited separately, so a subtraction does not null; the correlation column says how far from a null they are.

| programme | duration | M&E alignment | correlation | M&E baseline offset |
|---|---|---|---|---|
| Sintel (2010), stereo master | 14:48 | +0 samples | 0.88 | -3.20 dB |
| Tears of Steel (2012), stereo mix | 12:14 | -324 samples | 0.56 | +2.92 dB |

| programme | speech share: reference | detector | Silero | frame precision | frame recall | frames agreeing |
|---|---|---|---|---|---|---|
| Sintel (2010), stereo master | 11 % | 11 % | 4 % | 36 % | 36 % | 86 % |
| Tears of Steel (2012), stereo mix | 21 % | 8 % | 13 % | 93 % | 36 % | 86 % |

| programme | integrated (BS.1770-4) | dialogue-gated: reference | detector | delta | within 1 LU | Silero-gated | Netflix -27 ±2: reference / detector |
|---|---|---|---|---|---|---|---|
| Sintel (2010), stereo master | -16.1 | -18.8 (891 blocks) | -25.6 (928 blocks) | -6.73 LU | ✗ | -28.1 | FAIL / PASS |
| Tears of Steel (2012), stereo mix | -11.6 | -12.8 (1425 blocks) | -14.4 (579 blocks) | -1.64 LU | ✗ | -14.1 | FAIL / FAIL |

Sensitivity of the reference to how far above the M&E a frame must sit (share, gated value):

| programme | 2 dB | 3 dB | 6 dB |
|---|---|---|---|
| Sintel (2010), stereo master | 13 %, -16.94 | 11 %, -18.82 | 7 %, -21.28 |
| Tears of Steel (2012), stereo mix | 32 %, -13.25 | 21 %, -12.78 | 15 %, -13.27 |

## Speech share by regime

Several profiles switch from the dialogue rule to the full-programme rule under 15 % speech. Clean speech should read high (mark: at least 80 %), music and effects without dialogue should read under 15 %, and mixed programmes and singing are shown without a mark. The dialogue-gated value is the detector's; the integrated value is BS.1770-4 for context.

| programme | source | duration | ch | regime | integrated | dialogue-gated (detector) | speech share: detector | Silero | mark |
|---|---|---|---|---|---|---|---|---|---|
| LibriVox, William Again, chapter 1 | public domain, LibriVox | 25:51 | 1 | speech | -27.3 | -27.5 (15318) | 100 % | 100 % | ✓ |
| NASA, Houston We Have a Podcast, National Lab 15 | NASA, public domain | 45:54 | 2 | speech | -12.0 | -12.1 (26965) | 98 % | 99 % | ✓ |
| SQAM 27, castanets | EBU SQAM (Tech 3253), R&D use | 0:20 | 2 | no dialogue | -24.2 | -24.4 (136) | 92 % | 0 % | ✗ |
| SQAM 49, female speech, English | EBU SQAM (Tech 3253), R&D use | 0:23 | 2 | speech | -19.5 | -19.7 (177) | 91 % | 95 % | ✓ |
| SQAM 50, male speech, English | EBU SQAM (Tech 3253), R&D use | 0:22 | 2 | speech | -18.5 | -18.9 (174) | 94 % | 97 % | ✓ |
| SQAM 51, female speech, French | EBU SQAM (Tech 3253), R&D use | 0:21 | 2 | speech | -17.2 | -17.8 (159) | 94 % | 92 % | ✓ |
| SQAM 52, male speech, French | EBU SQAM (Tech 3253), R&D use | 0:24 | 2 | speech | -18.6 | -19.1 (177) | 86 % | 94 % | ✓ |
| SQAM 53, female speech, German | EBU SQAM (Tech 3253), R&D use | 0:21 | 2 | speech | -20.1 | -20.4 (149) | 98 % | 98 % | ✓ |
| SQAM 54, male speech, German | EBU SQAM (Tech 3253), R&D use | 0:21 | 2 | speech | -20.0 | -20.4 (149) | 99 % | 99 % | ✓ |
| SQAM 55, trumpet (Haydn) | EBU SQAM (Tech 3253), R&D use | 0:32 | 2 | no dialogue | -19.9 | -20.6 (149) | 56 % | 0 % | ✗ |
| SQAM 58, guitar (Sarasate) | EBU SQAM (Tech 3253), R&D use | 0:16 | 2 | no dialogue | -25.1 | -26.2 (84) | 70 % | 0 % | ✗ |
| SQAM 59, violin (Ravel) | EBU SQAM (Tech 3253), R&D use | 0:29 | 2 | no dialogue | -22.6 | -25.9 (19) | 8 % | 0 % | ✓ |
| SQAM 60, piano (Schubert) | EBU SQAM (Tech 3253), R&D use | 1:32 | 2 | no dialogue | -21.7 | -26.4 (287) | 32 % | 0 % | ✗ |
| SQAM 61, soprano (Mozart) | EBU SQAM (Tech 3253), R&D use | 2:59 | 2 | singing | -20.7 | -23.2 (787) | 46 % | 0 % |  |
| SQAM 64, choir (Orff) | EBU SQAM (Tech 3253), R&D use | 0:31 | 2 | singing | -12.5 | -12.6 (10) | 4 % | 0 % |  |
| Sintel, music and effects (no dialogue) | Blender Foundation, CC BY 3.0 | 14:48 | 2 | no dialogue | -13.0 | -22.7 (574) | 7 % | 0 % | ✓ |
| Tears of Steel, music and effects (no dialogue) | Blender Foundation, CC BY 3.0 | 12:14 | 2 | no dialogue | -14.9 | -26.4 (36) | 1 % | 0 % | ✓ |
| Sintel, stereo master | Blender Foundation, CC BY 3.0 | 14:48 | 2 | mixed | -16.1 | -25.6 (928) | 11 % | 4 % |  |
| Sintel, 5.1 master | Blender Foundation, CC BY 3.0 | 14:48 | 6 | mixed | -17.2 | -22.2 (1878) | 23 % | 4 % |  |
| Sintel, trailer | Blender Foundation, CC BY 3.0 | 0:52 | 2 | mixed | -12.8 | -15.0 (13) | 3 % | 14 % |  |
| Tears of Steel, stereo mix | Blender Foundation, CC BY 3.0 | 12:14 | 2 | mixed | -11.6 | -14.4 (579) | 8 % | 13 % |  |
| Tears of Steel, 5.1 discrete package (6 mono AIFF) | Blender Foundation, CC BY 3.0 | 12:14 | 6 | package | -14.3 | -15.4 (1303) | 26 % | n/a |  |
| Sprite Fright (2021) | Blender Studio, CC BY 4.0 | 10:30 | 2 | mixed | -12.2 | -15.1 (2698) | 44 % | 42 % |  |
| His Girl Friday (1940) | public domain, Internet Archive | 91:44 | 1 | mixed | -35.1 | -35.7 (48684) | 89 % | 88 % |  |
| Night of the Living Dead (1968) | public domain, Internet Archive | 96:05 | 1 | mixed | -28.8 | -30.4 (25110) | 44 % | 35 % |  |

**Against the M&E reference the detector's dialogue-gated reading is within 1 LU on 0 of 2 programmes.** The largest gap is -6.73 LU on Sintel (2010), stereo master, where the detector marks 11 % of the programme as speech against the reference's 11 %, but in the wrong places: 36 % of its speech frames are dialogue and it finds 36 % of the dialogue. Clean speech reads 86 to 100 % speech (8 of 8 at or above 80 %). Material without dialogue reads 1 to 92 % (3 of 7 under 15 %). Silero VAD reads 0 % on all of it.
