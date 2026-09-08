# Performance of cumple 0.2.0

Generated 2026-09-08 on this machine (arm64); synthetic 24-bit PCM programmes at 48 kHz. Peak memory is the maximum resident set size reported by `/usr/bin/time -l` for the whole `cumple check --json` process, Python and NumPy included.

| file | channels | duration | file size | wall time | real-time factor | peak memory |
|---|---|---|---|---|---|---|
| stereo-5min.wav | 2 | 5 min | 0.09 GB | 4 s | 72x | 428 MB |
| stereo-60min.wav | 2 | 60 min | 1.04 GB | 39 s | 91x | 704 MB |
| 5.1-30min.wav | 6 | 30 min | 1.56 GB | 52 s | 34x | 500 MB |

Memory grows far slower than the file: in this run twelve times the duration cost 1.6 times the memory. The meters never hold the audio; what they keep per programme second has not been profiled.
