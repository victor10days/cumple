# 06 Build 1 notes: what was measured

Build 1 is the repair foundation (R10): the Rust core, the bindings, `cumple repair` and the harness. The task reports in `.superpowers/sdd/2026-10-08-repair-foundation/` (`task-1-report.md` to `task-6-report.md`) hold the detail; this file lists the figures that the later builds and Victor need, by task. Nothing is pasted whole. `docs/REPAIR.md` holds the scored tables and is pinned by `tests/test_repair_numbers.py`.

## Tolerances

No tolerance moved. Rule 1 (port fidelity: 1e-6 per sample, 0.01 dB, the same De-click gap list, unclipped De-clip samples equal) was met bit for bit in the full harness set (Task 6 below), and the fixture figures of Tasks 3 and 4 were already bit-exact at every level. Rules 1b and 2 are reported, not gated. The one tolerance that was set from a measurement is the chain cost in `tests/test_repair_runner.py` (`CHAIN_COST_TOLERANCE = 0.25` dB, Task 5).

## Task 1: the harness and the baselines

- cathar 0.8.0 at f2c2842 built with `cargo install` in 113 s on this Mac.
- Full harness run, ffmpeg and cathar only, about 30 min.
- ffmpeg runs under a budget of 0.5 x duration + 10 s, so it covers 72 of 126 files; SQAM enters as 20 s excerpts from 2 s. Both facts are in the header of `docs/REPAIR.md`.
- The ffmpeg `adeclick` on the fixture's impulse set gives +2.37 dB with ffmpeg 9.0.1; the plan skeptic measured near zero with 6.1.1.

## Task 2: the core and CI

- Cold release build of the wheel: 9.1 s here; first `uv sync --extra repair` about 21 s. The uncached CI time is not known until the first CI run (Task 7).
- Side effect on Victor's Mac: `uv` installed a managed CPython 3.12.15 into `~/.local/share/uv/python/` while checking an `env -i` path. `uv python uninstall 3.12.15` removes it.
- `RX 8` recipe: the De-click values (Sensitivity, Click widening and the algorithm) are Victor's to read off RX 8 when it opens; `docs/repair/rx8-recipe.md` marks them "TO FILL IN (Victor)".

## Task 3: De-click

- `PRECISION_SEED = 1`: the first seed from 1 up where the f32 and f64 builds detect different gaps (the f32 build lists 70 gaps, the f64 build 10; the first only f32 finds is (22547, 17), where the float32 running sum has drifted so that sample 22555 has a local RMS of 1.98e-5 in float32 against 1.23e-4 in float64).
- Fidelity against cathar CLI on the fixture: seeds 3 and 1 bit-exact (gap lists equal, max sample 0.0, ΔSDR difference 0.0); also seeds 2, 4, 7, 8 and `method="cubic"`.
- Precision effect, seeds 1 to 20: the builds' gaps differ on 13 of 20; ΔSDR(f64) minus ΔSDR(f32) from -0.0000 to +0.0406 dB; max sample difference up to 1.39e-3.
- Mutations: the AR gap start shifted by one sample fails the fidelity test (max sample 9.83e-3 against 1e-6). The local RMS running sum held in f64 inside the f32 build fails the Rust bit test and the fidelity test on seed 1 only, which is why the test runs seed 1 as well as seed 3.
- Chunking: the f64 build matches the whole-file run exactly at blocks 1000, 4096, 8192 and 16384.

## Task 4: De-clip

- Fidelity against cathar CLI on the fixture: bit-exact at all seven levels, both methods; A-SPADE reaches the 100-iteration cap at every level in both builds.
- Precision effect on the fixture, ΔSDR(f64) minus ΔSDR(f32): -0.1332, +0.2207, +0.0727, +0.0756, -0.2232, +0.0214, -0.0578 dB at 1, 3, 5, 7, 10, 15 and 20 dB, max sample difference 4.35e-2 to 3.09e-1; the cubic method at most 2.5e-8.
- Mutations: the projection dropped (ΔSDR differs by -4.57 to -26.7 dB), the periodic window (max sample 2.82e-2 to 3.02e-1; at 10 dB only the sample bound catches it) and `RELAX_BY = 1` (max sample 4.83e-2 to 4.69e-1, ΔSDR -0.46 to -2.63 dB) each fail all seven fidelity items.
- Chunking cost (f64, whole minus chunked): fixture 5 dB at block 8,192 -0.1250 dB (context 4,096); a 36 s file at 5 dB, block 262,144 (`DEFAULT_BLOCK_FRAMES`) +0.0273 dB, max sample 6.38e-2; at block 65,536 +0.0530 dB.
- The f64 build's peak error on the fixture: -0.89 dB at 1 dB, -1.05 dB at 3 dB and +3.04 dB at 10 dB, which no test asserts; `docs/REPAIR.md` reports every level.
- A receipt's `iterations` and `frames` are summed over calls and channels, so a chunked run reports more than one call.

## Task 5: the runner

- libsndfile 1.2.2 truncates toward minus infinity when writing 24-bit integers; the runner rounds integer output to its grid (half to even) and clips to `[-1, 1 - LSB]`, so the residual identity is exact for PCM_16, PCM_24, PCM_U8, FLAC 16-bit, AIFF and RF64 24-bit. It differs from libsndfile's own conversion by at most one LSB.
- Chain cost (`declick(),declip(threshold=thr)` on the fixture at 8,192-frame blocks): +0.0125 dB against two `process_whole` passes, split into De-clip's own chunking (-0.1326 dB) and the raw right context (+0.1451 dB); over 24 layouts from -0.124 to +0.056 dB. The pinned tolerance is 0.25 dB.

## Task 6: cumple in the harness

Full run of `scripts/benchmark_repair.py` on the 126 damaged files (14 references): 51 min 31 s (ffmpeg's budgets dominate; run as a background process of the session because a foreground call is limited to 10 minutes). The tables are in `docs/REPAIR.md`; the figures:

- Rule 1 met on all 126 files. Largest sample difference between the f32 build and cathar 4.66e-10 (a16-clarinet burst12; the bound is 1e-6); ΔSDR differences all 0.0000 dB; the De-click gap lists equal on 28 of 28 files; De-clip unclipped samples equal on 98 of 98.
- Rule 1b, precision effect (f64 minus f32): ΔSDR from -2.4704 to +12.9479 dB, largest sample difference 5.36e-01. The +12.95 dB is a35-glockenspiel impulse11, where cathar's float32 running sum drifts and the two builds list 382 different gaps; across the 28 click files the builds list different gaps on 22. The effect on De-click is large on real music, not the 0.04 dB seen on the fixture.
- Rule 2, chunking cost at `DEFAULT_BLOCK_FRAMES` (262,144 frames): De-click +0.0000 dB with a largest sample difference of 0 (26 of 28 files are longer than one block); De-clip from -0.1806 to +0.1796 dB, largest sample difference 1.36e-01 (91 of 98 files). The fixture rows read "not run (shorter than one block)".
- cumple (f64) against cathar, by damage type, over the same files: De-clip +8.32 dB against +8.48 dB (98 files; paired over the 44 ffmpeg also ran, +11.36 against +11.46 and ffmpeg +4.47); impulse De-click +36.95 dB against +35.99 dB and ffmpeg +16.12, with 0 of 578 clicks missed and 0 false detections against cathar's 52 and 20; burst De-click about 0 dB for all three tools.
- cumple left 9 of 126 files unchanged (cathar 6), all burst files.
- The f64 build's De-click misses 0 of 578 clicks where cathar's f32 build misses 52; the gap lists differ on 22 of 28 files, which fits the running-sum drift Task 3 found, though this run did not isolate the cause. Build 2's detector is scored against both.
- Test count: `tests/test_repair_numbers.py` adds 8 tests (7 parse `docs/REPAIR.md` and need nothing; 1 needs the core). The fixture row is pinned with the harness's own seed (11), not seed 3 as the brief says, because seed 3 is not a row of the table.
