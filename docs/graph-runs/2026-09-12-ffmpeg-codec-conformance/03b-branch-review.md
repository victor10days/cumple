# 03b Branch review: loop/02-ffmpeg-codecs, 7781f29..4981675

Date: 2026-09-12. Reviewer: a fresh context reading the diff package, the frame, the plan, the plan skeptic, the ledger and the four task reports, then the tree at head. Method: the ecc security checklist re-applied to `src/cumple/io/ffmpeg.py`; each doubt in the brief answered by a run on this Mac (ffmpeg 9.0.1, libsndfile 1.2.2 through soundfile 0.14.0), not by reading alone. The suite was not re-run in full (230 collected at head, confirmed with `--collect-only`); focused runs and scratch fixtures under the session scratchpad only. Nothing in the worktree was changed except this file.

## Plan alignment

Every capability in the frame's contract is present at head and was exercised:

- Fallback conditions: `reader.probe` catches `sf.LibsndfileError`, re-raises unless the suffix is in `FFMPEG_SUFFIXES`, then asks `find_ffmpeg()`; without ffmpeg the error names ffmpeg, ffprobe and `CUMPLE_FFMPEG` (reader.py:101 to 109, test at test_ffmpeg_io.py:270). A broken `.wav` still gets libsndfile's own error (test at :282).
- Decoder named in the finding: engine.py:479 to 481 appends `, aac, decoded by ffmpeg 9.0.1` to the container finding's measured text; `cumple info` adds a `decoder` row (cli.py:265 to 266); JSON gains `container`, `codec`, `decoder` under `measurement` (json_out.py); the sheet's Format cell and meta line go through `_encoding()`.
- "not PCM": engine.py:375 to 378 prints `not PCM (aac)` and fails the bit-depth clause; `info` prints `not PCM` instead of `None-bit`.
- `fix` refusal: fix.py:115 to 118 raises before `plan()`; run here on an M4A, the message reads "tone.m4a is aac decoded by ffmpeg 9.0.1; fix writes PCM only, bounce it as WAV first".
- netflix FAIL with the quoted clause and acx PASS on an MP3, written by libsndfile so the test never skips (test_ffmpeg_io.py:229).
- CI: the Linux job installs ffmpeg with apt before Lint; macOS and Windows do not.
- Docs: README limit line and CI sentence, page FAQ and its JSON-LD twin, the honest-limits item, AI_USAGE's new section, ROADMAP R2 and the closed "Open for Victor" item, RELATED's ffmpeg and loudcheck sections.
- Benchmark re-pin: BENCHMARK.md regenerated with 9.0.1, four true-peak rows moved in the ffmpeg column, no tolerance total changed, loudcheck unchanged to the hundredth; the generator's case 6 note is now data-driven and pinned by `test_benchmark_note_agrees_with_its_table`.

Deviations, all justified and recorded in the ledger:

- The sheet's `_encoding()` renders "M4A (AAC) via ffmpeg 9.0.1" instead of the brief's "AAC via ffmpeg 9.0.1" because the sheet test for a profile without a containers clause asserts the container name. Reasonable: the container belongs on the sheet.
- Count pins ride with the task that changes them, Task 3 re-pinning last. 230 collected at head; README's CI number 201 equals 230 minus the 29 EBU cases, held by tests/test_counts.py:32.
- One consequence the frame's "nothing changes for WAV" does not quite cover: the sheet's Format strip for a WAV now reads "24-bit WAV · stereo" where it read "24-bit · stereo", and a native MP3 sheet now shows "MP3 · stereo" where it showed the layout alone. Additive and asserted by `test_json_and_sheet_name_the_container_for_a_wav`; not a regression, but a WAV user will see one new word.

What the plan did not cover and this review found: the page's "Does my audio leave the machine?" answer (Critical 1 below) and what happens to a container carrying several audio streams (Critical 2 below). Neither the plan nor the skeptic raised them; the skeptic did flag MOV and MP4 with a video track as "right in principle and untried".

## Security

Checklist applied to `src/cumple/io/ffmpeg.py` at head (blob 40d92ef):

- Argv only, no shell: `_version` (:93), `probe_ffmpeg` (:161) and `iter_blocks_ffmpeg` (:220) all pass lists; no `shell=True` anywhere in the module; nothing is string-joined.
- Path validation before every spawn: both `probe_ffmpeg` and `iter_blocks_ffmpeg` call `safe_path()` first (:145, :194). `safe_path` refuses text matching a scheme (`_SCHEME`) unless it is a drive letter (`_DRIVE`), resolves symlinks, and requires a regular file, so a FIFO, a device or a directory is refused. The path handed to ffmpeg is the resolved absolute one, which on POSIX starts with `/` and on Windows with a drive letter, so it can never read as a protocol even when the text check is bypassed by a name like `subfile,,x:y.m4a` (the whitelist and `resolve()` stop that; the ledger's S7 ruling says the regex does not claim to).
- stdin closed: `stdin=subprocess.DEVNULL` on all three calls; `-nostdin` on the ffmpeg decode (ffprobe has no such flag, DEVNULL covers it).
- Protocol whitelist on both tools: `-protocol_whitelist file` for ffprobe (:150), `file,pipe` for ffmpeg (:203), both placed before `-i` where they must be. Run here: a video-only MP4 probes to "ffprobe found no audio stream", a text file with an `.m4a` suffix raises with ffmpeg's words.
- Timeouts: ffprobe and `-version` use `subprocess.run(timeout=30)`; the decode uses a `threading.Timer` over a budget of ten times the duration plus sixty seconds, and `_kill` sends SIGKILL to the session the child started (`start_new_session` on POSIX), Windows falls back to `proc.kill()`. The stalled-decoder test reproduces a wrapper script whose child holds the pipe and asserts return within five seconds. The probe path kills only the direct child (Minor 4).
- stderr bounded: the decode's stderr goes to an anonymous `TemporaryFile` and only the last 4096 bytes are read (`_tail`); ffprobe's stderr is captured in memory and sliced at read time. With `-v error` both are small in practice.
- No environment or option built from user text: the only inputs that reach argv are the resolved path and the resolved executables; `CUMPLE_FFMPEG` is an operator variable, resolved through `shutil.which(path=directory)`. The child inherits the process environment untouched.
- Nothing written by the package: true in the file-system sense; the `TemporaryFile` is anonymous and unlinked on creation (the module docstring's "nothing is written" is one word too strong, Minor 8).
- Cleanup on early exit: verified by run. With a generator holding an open ffmpeg, `pgrep` shows one process; after `del` on the generator, and after a `for ... break`, zero. The `finally` at :253 to 258 cancels the timer, kills the group if still alive and closes stdout.

No security hole found. Two hardening notes are in Minor 4 and Minor 7.

## Correctness

Each doubt in the brief, with what was run:

- Generator abandoned early: cleaned up, see above.
- Child killed mid-read: the kill closes every writer of the pipe, `read()` returns empty, the loop breaks, `wait()` returns the signal code, and `expired` wins with the budget message. Confirmed by the stalled-decoder test's shape; an extra run with a 0.5 s budget on a real decode was not needed.
- ffprobe JSON without streams: `doc["streams"][0]` raises IndexError, caught with KeyError and ValueError, and becomes "found no audio stream" (run on a video-only MP4).
- Zero shape: reader.py:114 refuses `samplerate < 1 or channels < 1` before `AudioInfo` is built (test with a monkeypatched probe).
- `expired` versus exit code: `expired` is checked first (:249), so a kill that lands as the child exits normally reports a budget error rather than a spurious exit code, and a normal exit under budget reports the code. The one wrong case, a timer that fires in the microseconds between a clean exit and `timer.cancel()`, would report "exceeded its budget" for a complete decode; rare enough to leave.
- `_locate` cache key: `(CUMPLE_FFMPEG or "", shutil.which("ffmpeg") or "")`, so a changed variable or PATH re-resolves and a same-path upgrade keeps the old version string for the process lifetime. Run here: the directory form, the binary form and a bad hint with ffmpeg on PATH all resolve (the last silently falls back to PATH, Minor 6).
- `probe` binding `tools` inside `except`: the only path to reader.py:110 is through the `except` block, which either binds `tools` or raises, so the name is always bound. Correct, if a reader has to think twice; Minor 9.
- Engine mapping for MOV and MP4 with non-AAC codecs: a `pcm_s24le` MOV probes as container MOV, subtype PCM_24, bit depth 24 (run here), maps to the token `mov`, and fails any profile's container clause because no profile can list `mov`: the `Container` literal at schema.py:146 has no such token. Against `apple-immersive`, whose quoted clause says "LPCM in .mov containers with channel assignments", the run gave bit depth PASS and container FAIL with the clause printed under it, a verdict that contradicts its own quotation. Against a profile listing `mxf` or `wav`, FAIL is the right verdict (a MOV is neither). See Important 2.
- Watch folder and package paths: `watch.py` still filters on `AUDIO_SUFFIXES` (watch.py:22, :54) and `load_package` too (reader.py:305); neither knows `FFMPEG_SUFFIXES`. Untouched, as the frame required.
- `diff` on a compressed file: `cumple diff tone.m4a tone.wav` prints "cannot compare: Error opening '...tone.m4a': Format not recognised." The docs promise only that diff needs PCM files, and the tool refuses rather than mis-measures. Not blocking; a one-line guard naming ffmpeg would be kinder (ledger, can wait).
- Containers with more than one audio stream: not in the brief's list, found while probing MOV. ffprobe is called with `-select_streams a:0` and ffmpeg with `-map 0:a:0`, so an OP1a MXF with two mono PCM tracks (the shape every DPP AS-11 and broadcast MXF delivery has, with four or sixteen mono tracks) and a MOV with two mono tracks both report `channels 1` and measure the first track alone, with no warning anywhere. Built and run here with ffmpeg's `channelsplit` (files `two_mono.mxf`, `two_mono.mov` in the scratchpad). See Critical 2.

## Tests

- Real behaviour, no vacuous passes. The gated tests build their fixtures with the local ffmpeg and assert shape, codec, frame count within AAC priming tolerance, full-scale peak within 0.02, the netflix clause text, "not PCM" without "None", the decoder in JSON and HTML, the `info` row, the fix refusal and the MXF PCM decoder line. The ungated tests cover the suffix set, `safe_path`, both regexes, the budget arithmetic, the subtype mapping, the no-ffmpeg message, the broken-WAV error, the zero shape, the MP3 netflix and acx verdicts, the WAV JSON keys, and the stalled decoder (a real `#!/bin/sh` child, killed within five seconds).
- Skips: with Homebrew removed from PATH, `tests/test_ffmpeg_io.py` and `tests/test_reader.py` give 19 passed, 16 skipped; the reason string is "ffmpeg and ffprobe are not on PATH". The Windows count of 17 is the shell-script test's `sys.platform == "win32"` skip. The MP3 tests ran in that same ffmpeg-less run and passed; the fixture is written by libsndfile.
- The benchmark-note test parses the `| file | expected TP |` table, takes both case 6 rows, compares the rounded cells with the same 0.05 tolerance the generator uses, and asserts the matching sentence. It cannot pass with neither sentence present. The generator compares full-precision floats and the test rounded cells; a reading at the boundary could make them disagree (ledger, dormant, can wait).
- Gaps: `CUMPLE_FFMPEG` and `_locate` have no test (verified by hand above); no test abandons a generator early (verified by hand above); no test feeds a container with several audio streams (Critical 2); `test_the_version_is_read_from_the_binary` would fail on a git snapshot build that prints "N-123456-gabcdef" (Minor 10).
- ruff check and ruff format --check are clean at head.

## Docs

Every sentence about formats checked against the tree at head, with the runner images fetched today for the CI claim:

- README.md:459 to 465: "Reads what libsndfile reads: WAV, BWF, RF64, AIFF, FLAC and MP3" is true (soundfile 0.14.0 reports libsndfile 1.2.2 and lists MP3 among its formats; the MP3 tests write and read one). The ffmpeg sentence is true for AAC, AC-3, E-AC-3 and single-stream MXF, MOV and MP4, and overclaims for multi-stream ones (Critical 2). "`diff` and `fix` still need PCM files" is true.
- README.md:413 to 415: 230 tests, 201 on Ubuntu, "16 fewer on macOS, which has no ffmpeg for the decode tests, and 17 fewer on Windows". 16 and 17 match the run above. The runner image READMEs at actions/runner-images (macos-15-arm64, Windows2022, Windows2025, Ubuntu2404, fetched 2026-09-12, HTTP 200) list no ffmpeg; Windows lists ImageMagick, whose installer can carry an `ffmpeg.exe` but not an `ffprobe.exe`, and `find_ffmpeg` needs both. The PR's first CI run should show 45 skipped on macOS, 46 on Windows and 29 on Linux; confirm from the logs before saying so anywhere else.
- site/index.html:219 and :401: the FAQ and its JSON-LD twin match each other (test_site.py:133 holds them equal) and say the same as README, with the same overclaim on multi-stream containers.
- site/index.html:410: the honest-limits item is now true ("Without a local ffmpeg it reads only what libsndfile reads ...").
- site/index.html:215 and :397: "The only external program cumple runs is the Chrome, Chromium or Edge already on the machine, to print a PDF." False at head; cumple now runs ffmpeg and ffprobe. Critical 1. Nothing in the README makes the same claim.
- AI_USAGE.md "Compressed deliveries (12 September)": every claim traces to the module (argv, stdin, whitelist, budget, cap) and to CI; "a reviewer with the security checklist read it before merge" is true by this review.
- ROADMAP.md: R2 says "building" with an empty PR cell; the loop's own rule moves the row to "merged" with the PR number, so both cells need filling in this PR once the number exists. "Open for Victor" is closed with the reason and is accurate.
- RELATED.md:31 (ffmpeg): "differs on 4 rows, listed there" points at BENCHMARK.md, which does not list them; its note names case 6 only, and the other two moved rows (seq-3341-2 and seq-3341-7, true peak) are visible only in the table. Important 1. The loudcheck sentence "match the 8.0 run to the hundredth" is true (no loudcheck cell changed in the diff).
- BENCHMARK.md: the header names ffmpeg 9.0.1 and the date; the case 6 note now agrees with the table; the ✓ and ✗ totals are unchanged.
- No em or en dash in any changed file (grep over README, AI_USAGE, ROADMAP, RELATED, BENCHMARK, the page, the run folder, the plan, the module, the tests and the generator). "not checked" appears only inside the plan's statement of the rule.

## Production readiness

- WAV users: `probe` and `iter_blocks` take the libsndfile path unchanged when the decoder is libsndfile; `iter_blocks` gained an optional `info` argument with a `None` default; JSON gains three additive keys; the sheet's Format cell gains the container word (above). No behaviour change in the measurement.
- Frozen app (packaging/cumple.spec): the new module imports functools, json, os, re, shutil, signal, subprocess, tempfile, threading and numpy; every one is stdlib or already collected, none is in `excludes`, and `reader.py` imports it statically so PyInstaller follows it. `--selftest` measures a WAV through `measure()`, whose path is unchanged. One practical limit for the app rather than the CLI: an app launched from Finder inherits a minimal PATH without `/opt/homebrew/bin`, so a Homebrew ffmpeg is not found unless `CUMPLE_FFMPEG` reaches the app's environment; the frame left the app's dialog filter alone, so no promise is broken, but the roadmap should say it (Minor 5).
- CI: the apt step is Linux-only and precedes Lint; a transient apt failure fails the job loudly, which is the right failure.

## Findings

### Critical

1. site/index.html:215 and :397, "The only external program cumple runs is the Chrome, Chromium or Edge already on the machine, to print a PDF." A published sentence that is false at head: cumple spawns ffprobe and ffmpeg for a compressed delivery. It sits under the privacy question, the one a supervisor reads before running the tool. Fix both twins (test_site.py:133 holds them equal), for example: "No. Nothing is uploaded. The only external programs cumple runs are already on the machine: Chrome, Chromium or Edge to print a PDF, and ffmpeg and ffprobe, when installed, to decode a compressed delivery."

2. src/cumple/io/ffmpeg.py:156 to 157 and :169 (`-select_streams a:0`, `doc["streams"][0]`) and :206 to 207 (`-map 0:a:0`); README.md:461, site/index.html:219 and :401 ("the audio of MXF, MOV and MP4 files"). A container carrying several audio streams is measured as its first stream only, silently: an OP1a MXF with two mono PCM tracks and a MOV with two mono tracks both report `channels 1` here, with no finding, no note and no error. Broadcast MXF (dpp-as11 lists `mxf`) carries four or sixteen mono tracks, and Apple's immersive clause describes exactly "LPCM in .mov containers with channel assignments", so these are the deliveries the feature is for, and the verdict on them is a wrong number presented as complete. Fix before merge, smallest honest version: drop `-select_streams` from the ffprobe argv, take the streams whose `codec_type` is `audio`, and raise `FfmpegError` naming the count when there is more than one ("tone.mxf carries 2 audio streams; cumple reads a single interleaved stream, bounce the programme as one WAV or MXF track"); add one gated test with a two-track MXF built through `channelsplit`; change the three sentences to "the audio of MXF, MOV and MP4 files with one audio track" and add a ROADMAP line for merging mono tracks by their labels. A doc-only fix (say "first audio stream") is the floor; the refusal is the honest behaviour.

### Important

1. docs/RELATED.md:31, "BENCHMARK.md is that run, and it differs on 4 rows, listed there". BENCHMARK.md lists no rows; its note names case 6 only. Name the four in RELATED.md (true peak: seq-3341-2 from −32.80 to −32.70, both case 6 files from −28.00 to −24.00, seq-3341-7 from −9.10 to −8.90) or change "listed there" to "visible in its true-peak table". One sentence.

2. src/cumple/checks/engine.py:459 to 472 and src/cumple/specs/schema.py:146. The engine now emits the tokens `mov`, `mp4`, `m4a`, `ac3`, `eac3` and no profile can list them, because the `Container` literal was not extended. A PCM MOV checked against apple-immersive fails the container clause while the clause it quotes permits ".mov containers" (run here). Before this branch the file could not be opened, so this is a new contradiction rather than a regression. Add `mov`, `ac3` and `eac3` to the literal so a profile author can name them (one line, no profile changes); whether apple-immersive's list gains `mov` is a profile decision for Victor, so record it in ROADMAP rather than deciding it here. Can wait if the ROADMAP line is written now.

3. docs/ROADMAP.md:10, R2 row: status "building", PR and receipt cells empty. The loop's rule moves the row to "merged" with the PR number; fill both in this PR once the number exists, before merge.

### Minor

1. src/cumple/io/ffmpeg.py:248, `proc.wait(timeout=5)` raises a bare `subprocess.TimeoutExpired` when `block_frames` is 0 (reproduced: `read(0)` returns empty at once, ffmpeg blocks on a full pipe, the wait times out). No caller passes 0 and the CLI does not expose the block size. Add `if block_frames < 1: raise FfmpegError(...)` beside the channels guard.

2. src/cumple/io/ffmpeg.py:244 to 247, the post-loop carry block can never yield: inside the loop `carry` is always trimmed to less than one frame, so `whole` is 0 afterwards. Drop it or say why it stays.

3. src/cumple/io/ffmpeg.py:225 to 227, `on_budget` could test `proc.poll() is None` before `_kill`, narrowing the window in which a reaped pid could be re-used by an unrelated session leader. Cosmetic at these time scales.

4. src/cumple/io/ffmpeg.py:93 and :161, the `-version` and ffprobe calls use `subprocess.run(timeout=...)`, which kills the direct child only. A wrapper-script ffprobe leaves an orphan on timeout; on POSIX `run()` then calls `wait()`, not `communicate()`, so nothing hangs; on Windows `communicate()` after the kill would wait for a grandchild holding the pipe. Rare; note it or reuse `_kill` through a small `Popen` wrapper.

5. Frozen app: a Finder-launched cumple.app has a minimal PATH and will not find Homebrew's ffmpeg. Say so in ROADMAP or in the app's error text ("point CUMPLE_FFMPEG at it" is already in the message, but the app has no way to set it).

6. src/cumple/io/ffmpeg.py:77 to 88, a `CUMPLE_FFMPEG` that resolves to nothing falls back to PATH without a word. A warning on stderr, or refusing to fall back when the variable is set, would tell an operator their pin is wrong.

7. src/cumple/io/ffmpeg.py:73 and :84, `shutil.which("ffmpeg")` without `path=` prepends the current directory on Windows when the registry default allows it, so a delivered folder containing `ffmpeg.exe` and `ffprobe.exe` would be run if cumple is invoked from inside it. Inherited from `shutil.which`, not new, but `path=os.environ.get("PATH", os.defpath)` closes it in one argument.

8. src/cumple/io/ffmpeg.py:5, "nothing is written or moved": one anonymous `TemporaryFile` is created for stderr. "No file is written" is the exact claim.

9. src/cumple/io/reader.py:104 and :111, `tools` is bound inside `except` and used after it. Correct, since the `try` either returns or lands in that block, but a reader stops to check. Moving the ffmpeg branch into a helper called from the `except` would read straight.

10. tests/test_ffmpeg_io.py:149, `^[nN]?\d` rejects git snapshot builds whose version reads "N-123456-g...". Not a CI concern; widen to `^[nN]?[\d-]` or accept "unknown".

11. src/cumple/cli.py:268, `info` on an AAC prints "AAC (integer, not PCM)"; "integer" says nothing about a lossy codec. Print "AAC (not PCM)" when `bit_depth` is None.

12. src/cumple/io/ffmpeg.py:40 to 51, ALAC in an M4A comes back as subtype "ALAC", bit depth None, and the engine prints "not PCM (alac)" for a lossless stream; ffprobe's `bits_per_raw_sample` would give ALAC_16 or ALAC_24 as libsndfile names them for CAF. No profile lists m4a, so nothing passes wrongly today.

13. src/cumple/report/qc_sheet.py, an MP3 that libsndfile refused and ffmpeg decoded would render "MP3 (MP3) via ffmpeg 9.0.1". Skip the parenthesis when codec and container agree.

## Ledger triage

Must fix before merge:

- Critical 1 (page privacy answer, both twins): a false published sentence.
- Critical 2 (multi-stream containers): a silent wrong verdict on the deliveries the feature targets, plus the three overclaiming sentences.
- Important 1 (RELATED "listed there"): a published pointer to a list that does not exist; one sentence.
- Important 3 (ROADMAP R2 status and PR cell): the loop's own rule, at merge time.
- Task 4's two carried Important items (mismatch branch prints only the first case 6 file; generator compares full precision while the test compares rounded cells): dormant today, but the ledger says they were "carried into the final fix wave", and this is that wave; if the wave happens, take them, they are a few lines each. If the wave is skipped they can wait, nothing at head is wrong.

Can wait:

- Task 1 deferred: `block_frames >= 1` guard (Minor 1, no caller reaches it); unreachable carry block (Minor 2); `poll()` before `killpg` (Minor 3); docstring, renamed binary, encode() helper without a whitelist (Minor 8, test helper on trusted inputs).
- Task 1 warning about CI: resolved by Task 3's apt step.
- Task 2 deferred: the four mapping entries that equal the default (documentation); `_encoding(m)` evaluated twice; `tools` bound in `except` (Minor 9); test_watch_fix's unraisable warning under `-W error` (pre-existing, not this branch).
- Task 3 deferred: `diff` on a compressed file surfaces libsndfile's raw error; documented as PCM-only, and a refusal is not a wrong number.
- Task 4 minors: `CASE6_FILES` KeyError on rename (house style); two decimals versus whole numbers between the two branches.
- Important 2 (schema tokens and apple-immersive's list): the literal is one line and could go now; the profile change is Victor's decision, so a ROADMAP line is enough for this PR.

## Verdict

Ship with changes. The module is sound under the security checklist and the runtime behaviour matches the plan wherever the plan looked; the two Critical items are outside what the plan looked at, one is a sentence on the page and the other is a stream count that a handful of lines and one test settle. After those and the RELATED sentence, merge.
