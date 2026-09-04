# cumple vs ffmpeg ebur128 and pyloudnorm on the EBU Loudness Test Set v5.0

Generated 2026-09-04 with cumple 0.1.0, `ffmpeg version 8.0 Copyright (c) 2000-2025 the FFmpeg developers` and pyloudnorm 0.2.0. Expected values from EBU Tech 3341 Table 1 (±0.1 LU; true peak +0.2/−0.4 dBTP) and Tech 3342 (±1 LU). ✓ means inside the published tolerance. pyloudnorm measures integrated loudness only (no true peak, no loudness range), so it has one column.

| file | expected | cumple I | ffmpeg I | pyloudnorm I | cumple TP | ffmpeg TP | cumple LRA | ffmpeg LRA |
|---|---|---|---|---|---|---|---|---|
| seq-3341-1-16bit.wav | I -23 | -22.95 ✓ | -23.00 ✓ | -22.99 ✓ | -22.93 | -22.90 | 0.00 | 0.00 |
| seq-3341-2-16bit.wav | I -33 | -32.96 ✓ | -33.00 ✓ | -33.00 ✓ | -32.74 | -32.80 | 0.00 | 0.00 |
| seq-3341-3-16bit-v02.wav | I -23 | -23.01 ✓ | -23.00 ✓ | -23.06 ✓ | -22.99 | -23.00 | 13.00 | 13.00 |
| seq-3341-4-16bit-v02.wav | I -23 | -23.01 ✓ | -23.00 ✓ | -23.06 ✓ | -22.99 | -23.00 | 13.00 | 13.00 |
| seq-3341-5-16bit-v02.wav | I -23 | -22.98 ✓ | -23.00 ✓ | -23.02 ✓ | -19.99 | -20.00 | 6.00 | 6.00 |
| seq-3341-6-5channels-16bit.wav | I -23 | -23.02 ✓ | -23.00 ✓ | -23.06 ✓ | -24.00 | -28.00 | 0.00 | 0.00 |
| seq-3341-6-6channels-WAVEEX-16bit.wav | I -23 | -23.02 ✓ | -23.00 ✓ | -23.06 ✓ | -24.00 | -28.00 | 0.00 | 0.00 |
| seq-3341-7_seq-3342-5-24bit.wav | I -23 LRA 5 | -22.99 ✓ | -23.00 ✓ | -23.03 ✓ | -8.90 | -9.10 | 4.98 ✓ | 5.00 ✓ |
| seq-3341-2011-8_seq-3342-6-24bit-v02.wav | I -23 LRA 15 | -23.00 ✓ | -23.00 ✓ | -23.04 ✓ | -2.66 | -2.60 | 15.01 ✓ | 15.00 ✓ |
| seq-3341-15-24bit.wav.wav | TP -6 | -2.70 | -2.70 | -2.74 | -6.20 ✓ | -6.00 ✓ | 0.09 | 20.10 |
| seq-3341-16-24bit.wav.wav | TP -6 | -2.70 | -2.70 | -2.74 | -5.96 ✓ | -6.00 ✓ | 0.09 | 20.10 |
| seq-3341-19-24bit.wav.wav | TP +3 | 6.31 | 6.30 | 6.27 | 3.05 ✓ | 3.00 ✓ | 0.09 | 20.10 |
| seq-3341-20-24bit.wav.wav | TP +0 | -2.70 | -2.70 | -2.74 | -0.15 ✓ | -0.10 ✓ | 0.09 | 20.10 |
| seq-3341-23-24bit.wav.wav | TP +0 | -2.70 | -2.70 | -2.74 | -0.08 ✓ | -0.10 ✓ | 0.09 | 20.10 |
| seq-3342-1-16bit.wav | LRA 10 | -22.59 | -22.60 | -22.63 | -19.99 | -20.00 | 10.00 ✓ | 10.00 ✓ |
| seq-3342-2-16bit.wav | LRA 5 | -16.81 | -16.80 | -16.85 | -14.99 | -15.00 | 5.00 ✓ | 5.00 ✓ |
| seq-3342-3-16bit.wav | LRA 20 | -20.03 | -20.00 | -20.07 | -19.99 | -20.00 | 20.00 ✓ | 20.00 ✓ |
| seq-3342-4-16bit.wav | LRA 15 | -24.49 | -24.50 | -24.53 | -19.99 | -20.00 | 15.00 ✓ | 15.00 ✓ |

Notes: ffmpeg's ebur128 is an independent implementation with no published conformance report. On the five- and six-channel case 6 files it reports a true peak of −28 dBFS where the centre channel sits at −24 dBFS; cumple reports the centre channel. On the true-peak burst files ffmpeg reports a loudness range of about 20 LU for what is a single steady tone; those files carry no LRA expectation in Tech 3342, so this is noted, not scored. pyloudnorm reads the whole file into memory and takes at most five channels, so the six-channel case 6 file was passed to it without its LFE channel; cumple and ffmpeg read the file as delivered.

Speed and memory on long programmes are in [PERF.md](PERF.md).
