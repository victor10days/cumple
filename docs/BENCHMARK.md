# cumple against libebur128, pyloudnorm, ffmpeg ebur128 and loudcheck on the EBU Loudness Test Set v5.0

Generated 2026-09-08 with cumple 0.2.1, libebur128 1.2.6, pyloudnorm 0.2.0, `ffmpeg version 8.0 Copyright (c) 2000-2025 the FFmpeg developers` and loudcheck 0.3.2. Expected values from EBU Tech 3341 Table 1 (±0.1 LU; true peak +0.2/−0.4 dBTP) and Tech 3342 (±1 LU). ✓ means inside the published tolerance, ✗ outside; a value without a mark has no expectation on that file. Every tool ran once on every file on the same machine. pyloudnorm has no true peak, so it is absent from that table. loudcheck's readings are ffmpeg's loudnorm filter as loudcheck runs it: loudness and range at 192 kHz, true peak as the sample peak after resampling to 192 kHz, two decimals.

## Integrated loudness, LUFS

| file | expected I | cumple | libebur128 | pyloudnorm | ffmpeg ebur128 | loudcheck |
|---|---|---|---|---|---|---|
| seq-3341-1-16bit.wav | -23 | -22.95 ✓ | -22.95 ✓ | -22.99 ✓ | -23.00 ✓ | -22.95 ✓ |
| seq-3341-2-16bit.wav | -33 | -32.96 ✓ | -32.96 ✓ | -33.00 ✓ | -33.00 ✓ | -32.95 ✓ |
| seq-3341-3-16bit-v02.wav | -23 | -23.01 ✓ | -23.01 ✓ | -23.06 ✓ | -23.00 ✓ | -23.07 ✓ |
| seq-3341-4-16bit-v02.wav | -23 | -23.01 ✓ | -23.01 ✓ | -23.06 ✓ | -23.00 ✓ | -23.07 ✓ |
| seq-3341-5-16bit-v02.wav | -23 | -22.98 ✓ | -22.98 ✓ | -23.02 ✓ | -23.00 ✓ | -23.14 ✗ |
| seq-3341-6-5channels-16bit.wav | -23 | -23.02 ✓ | -23.02 ✓ | -23.06 ✓ | -23.00 ✓ | -23.05 ✓ |
| seq-3341-6-6channels-WAVEEX-16bit.wav | -23 | -23.02 ✓ | -23.02 ✓ | -23.06 ✓ | -23.00 ✓ | -23.05 ✓ |
| seq-3341-7_seq-3342-5-24bit.wav | -23 | -22.99 ✓ | -22.99 ✓ | -23.03 ✓ | -23.00 ✓ | -23.00 ✓ |
| seq-3341-2011-8_seq-3342-6-24bit-v02.wav | -23 | -23.00 ✓ | -23.00 ✓ | -23.04 ✓ | -23.00 ✓ | -23.01 ✓ |
| seq-3341-15-24bit.wav.wav |  | -2.70 | -2.70 | -2.74 | -2.70 | -2.73 |
| seq-3341-16-24bit.wav.wav |  | -2.70 | -2.70 | -2.74 | -2.70 | -2.73 |
| seq-3341-17-24bit.wav.wav |  | -2.70 | -2.70 | -2.75 | -2.70 | -2.73 |
| seq-3341-18-24bit.wav.wav |  | -2.71 | -2.71 | -2.75 | -2.70 | -2.73 |
| seq-3341-19-24bit.wav.wav |  | 6.31 | 6.31 | 6.27 | 6.30 | 6.27 |
| seq-3341-20-24bit.wav.wav |  | -2.70 | -2.70 | -2.74 | -2.70 | -2.73 |
| seq-3341-21-24bit.wav.wav |  | -2.70 | -2.70 | -2.74 | -2.70 | -2.73 |
| seq-3341-22-24bit.wav.wav |  | -2.70 | -2.70 | -2.74 | -2.70 | -2.73 |
| seq-3341-23-24bit.wav.wav |  | -2.70 | -2.70 | -2.74 | -2.70 | -2.73 |
| seq-3342-1-16bit.wav |  | -22.59 | -22.59 | -22.63 | -22.60 | -22.90 |
| seq-3342-2-16bit.wav |  | -16.81 | -16.81 | -16.85 | -16.80 | -16.72 |
| seq-3342-3-16bit.wav |  | -20.03 | -20.03 | -20.07 | -20.00 | -20.08 |
| seq-3342-4-16bit.wav |  | -24.49 | -24.49 | -24.53 | -24.50 | -24.55 |

## True peak, dBTP

| file | expected TP | cumple | libebur128 | ffmpeg ebur128 | loudcheck |
|---|---|---|---|---|---|
| seq-3341-1-16bit.wav |  | -22.93 | -22.94 | -22.90 | -22.94 |
| seq-3341-2-16bit.wav |  | -32.74 | -32.74 | -32.80 | -32.75 |
| seq-3341-3-16bit-v02.wav |  | -22.99 | -23.00 | -23.00 | -23.00 |
| seq-3341-4-16bit-v02.wav |  | -22.99 | -23.00 | -23.00 | -23.00 |
| seq-3341-5-16bit-v02.wav |  | -19.99 | -20.00 | -20.00 | -20.00 |
| seq-3341-6-5channels-16bit.wav |  | -24.00 | -24.00 | -28.00 | -24.00 |
| seq-3341-6-6channels-WAVEEX-16bit.wav |  | -24.00 | -24.00 | -28.00 | -24.00 |
| seq-3341-7_seq-3342-5-24bit.wav |  | -8.90 | -8.91 | -9.10 | -8.91 |
| seq-3341-2011-8_seq-3342-6-24bit-v02.wav |  | -2.64 | -2.64 | -2.60 | -2.64 |
| seq-3341-15-24bit.wav.wav | -6 | -6.00 ✓ | -6.00 ✓ | -6.00 ✓ | -6.00 ✓ |
| seq-3341-16-24bit.wav.wav | -6 | -5.96 ✓ | -6.03 ✓ | -6.00 ✓ | -6.00 ✓ |
| seq-3341-17-24bit.wav.wav | -6 | -6.30 ✓ | -5.99 ✓ | -6.00 ✓ | -6.00 ✓ |
| seq-3341-18-24bit.wav.wav | -6 | -6.01 ✓ | -6.00 ✓ | -6.00 ✓ | -6.00 ✓ |
| seq-3341-19-24bit.wav.wav | +3 | 3.05 ✓ | 2.98 ✓ | 3.00 ✓ | 3.01 ✓ |
| seq-3341-20-24bit.wav.wav | +0 | -0.13 ✓ | -0.13 ✓ | -0.10 ✓ | -0.13 ✓ |
| seq-3341-21-24bit.wav.wav | +0 | -0.08 ✓ | -0.09 ✓ | -0.10 ✓ | -0.12 ✓ |
| seq-3341-22-24bit.wav.wav | +0 | -0.20 ✓ | -0.18 ✓ | -0.10 ✓ | -0.14 ✓ |
| seq-3341-23-24bit.wav.wav | +0 | -0.08 ✓ | -0.09 ✓ | -0.10 ✓ | -0.12 ✓ |
| seq-3342-1-16bit.wav |  | -19.99 | -20.00 | -20.00 | -20.00 |
| seq-3342-2-16bit.wav |  | -14.99 | -15.00 | -15.00 | -15.00 |
| seq-3342-3-16bit.wav |  | -19.99 | -20.00 | -20.00 | -20.00 |
| seq-3342-4-16bit.wav |  | -19.99 | -20.00 | -20.00 | -20.00 |

## Loudness range, LU

| file | expected LRA | cumple | libebur128 | pyloudnorm | ffmpeg ebur128 | loudcheck |
|---|---|---|---|---|---|---|
| seq-3341-1-16bit.wav |  | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| seq-3341-2-16bit.wav |  | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| seq-3341-3-16bit-v02.wav |  | 13.00 | 13.00 | 13.00 | 13.00 | 13.00 |
| seq-3341-4-16bit-v02.wav |  | 13.00 | 13.00 | 13.00 | 13.00 | 13.00 |
| seq-3341-5-16bit-v02.wav |  | 6.00 | 6.00 | 6.00 | 6.00 | 6.00 |
| seq-3341-6-5channels-16bit.wav |  | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| seq-3341-6-6channels-WAVEEX-16bit.wav |  | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| seq-3341-7_seq-3342-5-24bit.wav | 5 | 4.98 ✓ | 4.97 ✓ | 4.96 ✓ | 5.00 ✓ | 4.90 ✓ |
| seq-3341-2011-8_seq-3342-6-24bit-v02.wav | 15 | 15.01 ✓ | 14.99 ✓ | 14.97 ✓ | 15.00 ✓ | 14.90 ✓ |
| seq-3341-15-24bit.wav.wav |  | 0.09 | 0.00 | 2.68 | 20.10 | 0.00 |
| seq-3341-16-24bit.wav.wav |  | 0.09 | 0.00 | 2.68 | 20.10 | 0.00 |
| seq-3341-17-24bit.wav.wav |  | 0.09 | 0.00 | 2.68 | 20.10 | 0.00 |
| seq-3341-18-24bit.wav.wav |  | 0.09 | 0.00 | 2.68 | 20.10 | 0.00 |
| seq-3341-19-24bit.wav.wav |  | 0.09 | 0.00 | 2.68 | 20.10 | 0.00 |
| seq-3341-20-24bit.wav.wav |  | 0.09 | 0.00 | 2.68 | 20.10 | 0.00 |
| seq-3341-21-24bit.wav.wav |  | 0.09 | 0.00 | 2.68 | 20.10 | 0.00 |
| seq-3341-22-24bit.wav.wav |  | 0.09 | 0.00 | 2.68 | 20.10 | 0.00 |
| seq-3341-23-24bit.wav.wav |  | 0.09 | 0.00 | 2.68 | 20.10 | 0.00 |
| seq-3342-1-16bit.wav | 10 | 10.00 ✓ | 10.00 ✓ | 10.00 ✓ | 10.00 ✓ | 10.00 ✓ |
| seq-3342-2-16bit.wav | 5 | 5.00 ✓ | 5.00 ✓ | 5.00 ✓ | 5.00 ✓ | 5.00 ✓ |
| seq-3342-3-16bit.wav | 20 | 20.00 ✓ | 20.00 ✓ | 20.00 ✓ | 20.00 ✓ | 20.00 ✓ |
| seq-3342-4-16bit.wav | 15 | 15.00 ✓ | 15.00 ✓ | 15.00 ✓ | 15.00 ✓ | 15.00 ✓ |

## Readings inside tolerance

**cumple: 24 of 24 readings inside tolerance**

**libebur128: 24 of 24 readings inside tolerance**

**pyloudnorm: 15 of 15 readings inside tolerance**

**ffmpeg ebur128: 24 of 24 readings inside tolerance**

**loudcheck: 23 of 24 readings inside tolerance**

Notes: ffmpeg's ebur128 is an independent implementation with no published conformance report. On the five- and six-channel case 6 files it reports a true peak of −28 dBFS where the centre channel sits at −24 dBFS; cumple, libebur128 and loudcheck report the centre channel. On the true-peak burst files ffmpeg reports a loudness range of about 20 LU, and pyloudnorm 2.7 LU, for what is a single steady tone; those files carry no LRA expectation in Tech 3342, so this is noted, not scored. loudcheck reads case 5 at −23.14 LUFS, 0.04 LU outside the tolerance, where ffmpeg's own ebur128 filter reads −23.00 on the same file; loudnorm measures after resampling to 192 kHz, and the cause was not traced further. pyloudnorm reads the whole file into memory and takes at most five channels, so the six-channel case 6 file was passed to it without its LFE channel; the other tools read the file as delivered. libebur128 was called through ctypes on its Homebrew build with the channel map L R C Ls Rs for the five-channel file and L R C unused Ls Rs for the six-channel one, which is the library's own default; its header calls the true-peak algorithm implementation defined.

Speed and memory on long programmes are in [PERF.md](PERF.md).
