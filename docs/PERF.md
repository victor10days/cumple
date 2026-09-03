# Performance of cumple 0.1.0

Generated 2026-09-03 on this machine (arm64); synthetic 24-bit PCM programmes at 48 kHz. Peak memory is the maximum resident set size reported by `/usr/bin/time -l` for the whole `cumple check --json` process, Python and NumPy included.

| file | channels | duration | file size | wall time | real-time factor | peak memory |
|---|---|---|---|---|---|---|
| stereo-5min.wav | 2 | 5 min | 0.09 GB | 4 s | 73x | 405 MB |
| stereo-60min.wav | 2 | 60 min | 1.04 GB | 39 s | 92x | 622 MB |
| 5.1-30min.wav | 6 | 30 min | 1.56 GB | 52 s | 35x | 497 MB |

Memory should not grow with duration: the meters keep 10 ms energies and filter state, never the audio.
