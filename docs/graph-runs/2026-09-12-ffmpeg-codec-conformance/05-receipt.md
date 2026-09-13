2026-09-13 | ffmpeg-codec-conformance | Chain | Ship with changes (twice) | a multi-stream MXF was measured on its first track silently, and the page still named Chrome as the only external program | restoring ffmpeg 8.0; merging multi-track containers by label in this PR

# 05 Receipt: delivery codec and container conformance through an optional ffmpeg

## Decision

Victor confirmed R1 and R2 as the loop's two build items on 12 September and chose to accept the machine's ffmpeg 9.0.1 and re-pin the benchmark rather than restore 8.0 (exact 8.0 was not restorable: its libvpx, svt-av1, x264 and x265 had been upgraded underneath it). The merge of this PR was delegated the same day, after green checks and a clean fresh review.

## What shipped

Pull request #27, https://github.com/victor10days/cumple/pull/27, branch `loop/02-ffmpeg-codecs`: `src/cumple/io/ffmpeg.py` (new), the reader fallback, engine and report changes, `fix` refusal, CI apt step, docs, the benchmark re-pin, `Container` literal, 233 tests (204 in CI). Roadmap row R2 merged; R9 queued (merge multi-track MXF and MOV by channel labels); two questions added to Victor's list (apple-immersive and `mov`; the desktop app's PATH for ffmpeg).

## Rejected options

- Restore ffmpeg 8.0 by relinking four old dylibs: would break ffmpeg 9, opencv and rsgain; `ffmpeg@8` is 8.1.2, not 8.0. A re-pin was needed either way.
- Measure the first audio stream of a multi-track container and note it: a wrong number presented as complete is the failure the tool exists to prevent; refused with the count instead, merging by label is R9.
- A doc-only fix for the multi-stream case ("first audio stream"): the floor, not the honest behaviour.

## Findings that changed the outcome

- Plan skeptic, Critical: the plan named `measure_file`, which does not exist (`measure` does); and its drive-letter regex test could never pass. Both fixed before any implementer ran.
- Plan skeptic, High: the decode budget only checked between reads, so a stalled ffmpeg was never killed; the plan gained a `threading.Timer` and, after the re-check showed `sh` forks `sleep` past a plain kill, a process-group kill.
- Plan skeptic, High: no test put an MP3 through the engine; libsndfile writes MP3 itself, so the MP3 tests now never skip. Found along the way: libsndfile 1.2.2 reads MP3 natively, so the README's "does not decode MP3" had been false for as long as the wheel bundled it.
- Task 2 review, Important: a zero shape from ffprobe reached the meters as a ZeroDivisionError; `cumple fix` decoded a compressed file and then died at the write. Both guarded.
- Task 3 review, Critical: the page's honest-limits list still said "does not decode delivery codecs or MXF" under the rewritten FAQ.
- Task 4, surfaced by the implementer: the benchmark generator hardcoded ffmpeg 8.0's case-6 anecdote; with 9.0.1 the table said -24 and the note said -28. The note is data-driven now and a test pins it to the table.
- Whole-branch review, Critical: the page's privacy answer named Chrome as the only external program cumple runs; a multi-stream MXF or MOV was measured on its first track silently. Both fixed; the second narrowed three published sentences.

## Rulings

- Count pins ride with whichever task changes the count; the last task re-pins.
- `_encoding()` names the container on the sheet ("M4A (AAC) via ffmpeg 9.0.1") because the plan's own test required it; the plan's wording was wrong.
- The `fix` guard was in scope though fix.py was outside the plan's file list: the docs promise `fix` needs PCM, so saying so first is the honest behaviour.
- The generator's note became data-driven and a pin test was added to `tests/test_site_numbers.py`, the one place the boundary allows a test change (extending a pin for a report artefact).
- Task 4's two Important items (per-file numbers in the mismatch branch; rounded comparison) went to the final fix wave rather than a second round.
- Multi-stream containers are refused with the count named; merging by label is R9.
- `Container` gains `mov`, `ac3`, `eac3`; whether apple-immersive lists `mov` is Victor's.
- Deferred to after this PR: wrapper-script ffprobe orphan on timeout, silent fallback when `CUMPLE_FFMPEG` resolves to nothing, `tools` bound inside `except`, the version regex on git snapshot builds, ALAC bit depth, `diff` on a compressed file surfacing libsndfile's raw error, and `shutil.which(path=...)` being a no-op for Windows curdir insertion.
- For Victor's notes: the Puentes package's pitch.md and code-crib.md describe ffmpeg's 4 dB centre-channel miss on EBU case 6; true of ffmpeg 8.0, not of 9.0.1.

## The box that earned its place

The plan skeptic: two Critical defects in a plan the main session had just written, caught before a single line of code, and a hang the first fix would have hidden.
