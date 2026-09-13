# 02a: open-source and free command-line loudness meters, run here

Scope: tools not already in docs/RELATED.md (libebur128, pyloudnorm, ffmpeg
ebur128, loudcheck, DeltaWave). Test files: seq-3341-1 (want -23.0 LUFS)
and seq-3341-2 (want -33.0 LUFS), tolerance +-0.1 LU, at
/Users/Victor/.cache/cumple/ebu-loudness-test-set/; not copied, none below
needed it.

## 1. Inputs read

- docs/graph-runs/2026-09-12-competitive-landscape/01-frame.md
- docs/RELATED.md
- README.md lines 427-497
- /Users/Victor/.claude/skills/ecc/upstream/skills/market-research/SKILL.md
- the two EBU wav files (measured, not copied)

## 2. Findings

Correction: r128gain was wrongly marked not run here on the claim it always
mutates files. Its `--help` lists `-d, --dry-run: Do not write any tags,
only show scan results`, confirmed with matching shasum before and after on
both EBU files; that row is rewritten. Eight tools were tried: six CLI
tools, plus two PyPI libraries (`loudness`, `pyebur128`), excluded for
installing no CLI, and the GUI cask `youlean-loudness-meter`; `ebur128` and
`audio-loudness` do not exist on PyPI. Installing `rsgain` pulled `ffmpeg`
9.0.1_1 as a dependency and relinked `/opt/homebrew/bin/ffmpeg` from the 8.0
the frame named; ffmpeg-normalize below was measured earlier against 8.0,
still in the Cellar, unlinked.

| Tool | Maintainer, licence | Kind | Version, install | Command | seq-3341-1 (want -23.0) | seq-3341-2 (want -33.0) | Presets/verdicts | Report | Batch/watch | Offline | Doc, date |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sox stat/stats | SoX project, GPL-2.0-or-later AND LGPL-2.1-or-later | CLI | 14.4.2_6, `brew install sox` | `sox <f> -n stat`, `sox <f> -n stats` | no BS.1770; RMS lev -25.97 dB, Pk lev -22.94 dB | RMS lev -35.98 dB, Pk lev -32.75 dB | none | stdout text, no file | neither | yes | https://sourceforge.net/p/sox/code/ci/master/tree/sox.1, 2026-09-12 |
| ffmpeg-normalize | Werner Robitza, MIT (PyPI license_expression) | CLI, wraps ffmpeg loudnorm | 1.42.0, `uv pip install ffmpeg-normalize` (ffmpeg 8.0 at run time) | `ffmpeg-normalize <f> -n -p` | -22.95 LUFS, tp -22.94 dBTP, in tolerance | -32.95 LUFS, tp -32.75 dBTP, in tolerance | numeric target only | JSON to stdout with -p | `--batch` album mode | yes | https://github.com/slhck/ffmpeg-normalize, 2026-09-12 |
| r128gain | desbma, LGPLv2+ (PyPI classifier) | CLI tagger, dry-run flag | 1.0.7, `uv pip install r128gain` | `r128gain -d <f>`; shasum matches before/after | -23.0 LUFS, sample peak -22.9 dBFS, in tolerance | -33.0 LUFS, sample peak -32.7 dBFS, in tolerance | none | stdout line; tags without -d | `-r` recursive scan | yes | https://github.com/desbma/r128gain, 2026-09-12 |
| rsgain | complexlogic, BSD-2-Clause (`brew info rsgain`) | CLI | 3.8, `brew install rsgain` (adds ffmpeg, libebur128, taglib) | `rsgain custom -t -O <f1> <f2>` (scan-only default); shasum matches before/after | -22.95 LUFS, peak -22.94 dB true, in tolerance | -32.96 LUFS, peak -32.74 dB true, in tolerance | "easy" mode: recommended settings, no destinations | tab-delimited stdout with -O; `-s i` writes tags | easy mode recurses a folder | yes | https://github.com/complexlogic/rsgain, 2026-09-12 |
| loudness-scanner (jiixyj) | Jan Kokemuller, MIT (COPYING) | CLI, cmake build | HEAD, cloned 2026-09-12; `git clone --depth 1`, submodule init, `cmake`, `make -j4` | not run here: cmake configured clean but make failed in input_ffmpeg.c, 11 errors (AVCodecContext, avcodec_open2, av_register_all removed from FFmpeg since ~3.x). Binary never linked. | not run here | not run here | unknown | unknown | unknown | unknown | https://github.com/jiixyj/loudness-scanner, 2026-09-12 |
| bs1770gain | Peter Belkner, GPL-3.0-or-later (its site's copyright text) | CLI | not on Homebrew (install fails, formulae.brew.sh 404); a separate SourceForge project (bs1770gainmacos) ships 0.8.2 for macOS, runs under Rosetta | not run here: `bs1770gain -i -t <f>` fails both files, "wrong version of swresample: expecting 3, found 0" (bgx.c:1441); shasum confirms no write | not run here | not run here | unknown | `-f` log option documented | folder scan documented | yes, when it runs | https://bs1770gain.sourceforge.net/, http://pbelkner.de/projects/web/bs1770gain/, 2026-09-12 |

Two notes the table cannot hold: ffmpeg-normalize's true-peak reading
matches sox's sample-peak reading to the hundredth on both files
(-22.94/-22.94, -32.75/-32.75), so this cannot show its true-peak path
differs from a bare sample peak; and r128gain's and rsgain's non-writing
modes were proven safe by matching shasum before and after, so neither
needed a copy.

Nothing here gives cumple a gap against these six. Each lacks: sox no
BS.1770 mode; the other three no destinations, verdicts, or report file;
loudness-scanner does not build here; bs1770gain has no working binary.

## 3. Options from this angle

ffmpeg-normalize, r128gain, and rsgain landed in tolerance, but two
duplicate an engine already covered: ffmpeg-normalize wraps the ffmpeg
loudnorm filter loudcheck exercises in RELATED.md, and rsgain links
libebur128 directly, the library cumple's own libebur128 row measures. A
column for either shows one engine twice; r128gain's filter graph reads
closer to independent. sox is never a candidate, no BS.1770 by design;
bs1770gain and loudness-scanner stay out until one works.

## 4. Unknowns

- bs1770gain's readings: its macOS binary fails at measurement with a
  library version mismatch.
- loudness-scanner's readings: build never completed; needs input_ffmpeg.c
  patched for current FFmpeg, or disabled.
- Whether `loudness` or `pyebur128` would pass scripted: not tried.

## 5. Recommendation from this angle

ffmpeg-normalize, r128gain, and rsgain all gave in-tolerance readings
without touching the shared EBU cache, so all three are ready for a
benchmark_meters.py column; r128gain is least redundant since the other two
share an engine already covered. Keep bs1770gain and loudness-scanner off
the landing page until one works, never give sox a loudness column, and
restore ffmpeg to 8.0 before trusting any ffmpeg result again.
