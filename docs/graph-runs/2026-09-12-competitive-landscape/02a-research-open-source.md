# 02a: open-source and free command-line loudness meters, run here

Scope: tools not already in docs/RELATED.md (libebur128, pyloudnorm, ffmpeg
ebur128, loudcheck, DeltaWave, not repeated). Test files: seq-3341-1 (want
-23.0 LUFS) and seq-3341-2 (want -33.0 LUFS), tolerance +-0.1 LU, at
/Users/Victor/.cache/cumple/ebu-loudness-test-set/, not copied.

## 1. Inputs read

- docs/graph-runs/2026-09-12-competitive-landscape/01-frame.md
- docs/RELATED.md
- README.md lines 427-497
- /Users/Victor/.claude/skills/ecc/upstream/skills/market-research/SKILL.md
- the two EBU wav files (measured, not copied)

## 2. Findings

Five tools were attempted: two ran clean, one withheld to avoid mutating the
shared EBU cache, one failed to build, one not packaged for this Mac. Two
PyPI names (`loudness` 0.2.0, `pyebur128` 0.1.1) and one Homebrew cask
(`youlean-loudness-meter`) were checked and excluded before the table:
neither PyPI package installs a CLI binary (`ls .venv/bin/` shows no entry
point) and the cask is a GUI pkg installer. `ebur128` and `audio-loudness`
do not exist on PyPI (`uv pip install --dry-run`: "not found in the package
registry").

| Tool | Maintainer, licence | Kind | Version, install | Measurement command | seq-3341-1 (want -23.0) | seq-3341-2 (want -33.0) | Presets/verdicts | Report/output | Batch/watch | Offline | Doc, date |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sox stat/stats | SoX project, GPL-2.0-or-later AND LGPL-2.1-or-later (`brew info sox`) | CLI | 14.4.2_6, `brew install sox` | `sox <f> -n stat`, `sox <f> -n stats` | no BS.1770 mode; RMS lev -25.97 dB, Pk lev -22.94 dB | RMS lev -35.98 dB, Pk lev -32.75 dB | none | stdout text block, no file | neither, one file per call | yes | sox.sourceforge.net/sox.html, 2026-09-12 |
| ffmpeg-normalize | Werner Robitza, MIT (PyPI license_expression) | CLI, wraps ffmpeg loudnorm | 1.42.0, `uv pip install ffmpeg-normalize` | `ffmpeg-normalize <f> -n -p` | integrated -22.95 LUFS, tp -22.94 dBTP, in tolerance | integrated -32.95 LUFS, tp -32.75 dBTP, in tolerance | numeric target only, no named destinations, no citation | JSON to stdout with -p, no file by default | `--batch` album mode; no watch | yes, local ffmpeg | github.com/slhck/ffmpeg-normalize, 2026-09-12 |
| r128gain | desbma, LGPLv2+ (PyPI classifier) | CLI tagger | 1.0.7, `uv pip install r128gain` | not run here: tags every file scanned, no read-only flag (synthetic tone: `r128gain t2.wav` gives "loudness = -21.1 LUFS, sample peak = -21.1 dBFS" then "Tagging file"; `cmp` shows bytes changed). Not pointed at the EBU set. | not run here | not run here | none | stdout line, then mutates the file | `-r` recursive scan; no watch | yes | github.com/desbma/r128gain, 2026-09-12 |
| loudness-scanner (jiixyj) | Jan Kokemuller, MIT (COPYING) | CLI, cmake build | HEAD, clone 2026-09-12; `git clone --depth 1 ...`, submodule init, `cmake -S . -B build`, `make -j4` | not run here: cmake configured clean (glib, libsndfile, ffmpeg 8.0 all found) but make failed in input_ffmpeg.c, 11 errors: "unknown type name AVCodecContext", "no member named codec in struct AVStream", undeclared avcodec_open2, avcodec_alloc_frame, avcodec_decode_audio4, av_free_packet, avcodec_close, av_register_all (removed from FFmpeg since ~3.x; project last touched circa 2014). Binary never linked. | not run here | not run here | unknown | unknown | unknown | unknown | github.com/jiixyj/loudness-scanner, 2026-09-12 |
| bs1770gain | Peter Belkner (site meta tag); licence not confirmed here | CLI | not run here: `brew install bs1770gain` gave "Error: No formulae or casks found for bs1770gain."; `brew search bs1770` returns nothing; formulae.brew.sh/api/formula/bs1770gain.json returns 404, confirming it is absent from homebrew-core | not run here | not run here | not run here | unknown | unknown | unknown | unknown | bs1770gain.sourceforge.net, 2026-09-12 |

Two notes the table cannot hold. First, ffmpeg-normalize's true-peak reading
matches sox's plain sample-peak reading to the hundredth on both files
(seq-3341-1: -22.94 vs -22.94; seq-3341-2: -32.75 vs -32.75), expected on
these calibration tones but meaning this run cannot show its oversampled
true-peak path differs from a bare sample peak. Second, r128gain's
write-on-scan behavior was confirmed on a synthetic 1 kHz tone
(`ffmpeg -f lavfi -i "sine=frequency=1000:duration=2"`), not the EBU files,
per this branch's file-safety constraint.

Nothing here gives cumple a gap against these five: none offers
destinations, clause verdicts, a report file, a diff/null test, a watch
folder, or a desktop app that cumple lacks. Against cumple, each lacks: sox
no BS.1770 mode; ffmpeg-normalize no destinations, verdicts, or report file;
r128gain no read-only mode; loudness-scanner does not build against current
FFmpeg unpatched; bs1770gain is not on Homebrew today.

## 3. Options from this angle

ffmpeg-normalize is the only tool worth a future landing-page column: MIT,
maintained, ran clean, in tolerance on both files. sox is never a candidate,
no BS.1770 mode by design. bs1770gain, r128gain, loudness-scanner stay out
until their blockers clear (a non-Homebrew path, a read-only flag, a build
against current FFmpeg).

## 4. Unknowns

- bs1770gain's readings, verdicts, licence text: never installed here.
- loudness-scanner's readings: build never completed; needs
  input_ffmpeg.c patched for current FFmpeg, or that input disabled.
- r128gain's readings on the real EBU files: withheld to avoid mutating the
  shared cache; only a synthetic tone was measured.
- Whether `loudness` or `pyebur128` (PyPI) would pass the EBU set scripted:
  not attempted, neither installs a CLI.

## 5. Recommendation from this angle

Only sox and ffmpeg-normalize produced readings today, and only
ffmpeg-normalize gave an in-tolerance BS.1770 reading on both files, so it
alone is ready for a future benchmark_meters.py column. Keep bs1770gain,
r128gain, and loudness-scanner off the landing page until their blockers
clear, and never give sox a loudness column.
