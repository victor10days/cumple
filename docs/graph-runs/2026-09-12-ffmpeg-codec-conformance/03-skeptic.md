# 03 Skeptic: the ffmpeg codec conformance plan

Date: 2026-09-12. Reviewer: a fresh context with no history of the plan. Method: devils-advocate (steelman, pre-mortem, inversion, Socratic probing), the ecc security-review checklist applied to the subprocess module, and the AI blind-spot list (happy path, confidence without correctness, library hallucination, tests that pass for the wrong reason).

## Inputs read

- `docs/graph-runs/2026-09-12-ffmpeg-codec-conformance/01-frame.md`
- `docs/superpowers/plans/2026-09-12-ffmpeg-codec-conformance.md` (the plan under review)
- `docs/graph-runs/2026-09-12-competitive-landscape/05-receipt.md` (last run's blind spots: numbers written without a run, claims about tools that were false)
- `src/cumple/io/reader.py` (whole), `src/cumple/meters/measure.py` 170 to 310, `src/cumple/checks/engine.py` 30 to 60 and 355 to 485, `src/cumple/cli.py` 230 to 280, `src/cumple/watch.py` 1 to 120, `src/cumple/report/json_out.py` 52 to 75, `src/cumple/report/qc_sheet.py` 138 to 170, `src/cumple/specs/schema.py` 135 to 160, `src/cumple/specs/profiles/acx.yaml` and `netflix-2.0.yaml`, `src/cumple/io/__init__.py`, `pyproject.toml` (pytest, ruff, dependency groups)
- `tests/conftest.py`, `tests/test_reader.py` 1 to 30, `tests/test_site.py` 85 to 145, `tests/test_counts.py`, `tests/test_site_numbers.py` 40 to 70 and 100 to 115, `tests/test_related.py` 39 to 48 and 72 to 95
- `.github/workflows/tests.yml`, `scripts/benchmark_meters.py` 1 to 60 and 255 to 310, `docs/RELATED.md` 1 to 40, `docs/ROADMAP.md` (R2 row and section headings), `README.md` 104 to 112 and 413 to 464, `site/index.html` lines 219 and 401
- `~/.claude/skills/devils-advocate/SKILL.md` and its three references; `~/.claude/skills/ecc/upstream/skills/security-review/SKILL.md`

## Steelman

The plan puts the whole subprocess surface in one read-only module with a fixed argv, a resolved absolute path as the only user-derived token, stdin closed, a protocol whitelist on both binaries, a wall budget and a stderr that lives in a temp file rather than a pipe that can fill; that is the right shape and I could not find a way to get a string of the user's choosing into an option. The fallback sits exactly where libsndfile refuses a file and nowhere else, so WAV, BWF, RF64, AIFF, FLAC and the watch folder keep their code paths, and the engine change is additive (new tokens, a kinder wording for a None depth) with no existing test pinning the old text. The MP3 finding is real and well caught: this wheel's libsndfile 1.2.2 opens, decodes and even writes MP3, so the README and page have been wrong about MP3 and the plan fixes both in the same PR, with the JSON-LD twin held equal by an existing test.

## Checks run (commands and what they showed)

1. `uv run python -c "import soundfile as sf; print(sf.__version__, sf.__libsndfile_version__, sf.available_formats().get('MP3'))"`: `0.14.0 1.2.2 MPEG-1/2 Audio`. Subtypes MPEG_LAYER_I/II/III listed. An MP3 written by ffmpeg opened through `sf.SoundFile` as `MP3 MPEG_LAYER_III 48000 2 96000`, and `sf.blocks` returned all 96000 frames at peak 0.0675 (expected 0.0708 before lossy coding). The docs claim holds on this wheel.
2. `sf.write(path, data, 48000, format="MP3", subtype="MPEG_LAYER_III")` then `sf.SoundFile(path)`: libsndfile writes and reads back an MP3 on its own (`check_format('MP3','MPEG_LAYER_III')` is True). The MP3 fixture does not need ffmpeg.
3. `grep -rn "measure_file\|def measure(" src tests scripts`: only `def measure(` at `src/cumple/meters/measure.py:179`. `uv run python -c "from cumple.meters.measure import measure_file"`: `ImportError: cannot import name 'measure_file'`.
4. The plan's `_SCHEME` and `_DRIVE` regexes evaluated on the plan's own test strings: `_SCHEME.match("C:\\bounce\\mix.m4a")` is None (the class after the first letter is `+`, so a one-letter scheme never matches); `_SCHEME.match("subfile,,start,0,,:x.wav")` is None (commas are outside the class); `concat:`, `http:`, `data:` match.
5. `ffprobe -v error -protocol_whitelist file -print_format json -show_format -show_streams -select_streams a:0 <file>` on fixtures encoded in the scratchpad: M4A gives `format_name=mov,mp4,m4a,3gp,3g2,mj2 codec=aac sr=48000 ch=2 duration=2.000000`; MP3 `mp3/mp3`; AC-3 `ac3/ac3 duration=2.016`; E-AC-3 `eac3/eac3`; raw ADTS `aac/aac duration=2.078`; a mono OPAtom MXF `mxf/pcm_s24le ch=1`. A text file and a 64-byte zero file named `.m4a` give rc=1, stdout `{ }` (no `streams` key), stderr `moov atom not found` and `Invalid data found when processing input`. An empty `.mxf` gives rc=1 and `Invalid data found`. The plan's returncode-then-KeyError handling covers all of these.
6. `ffprobe ... -protocol_whitelist file "concat:tone.ac3|tone.ac3"`: `Protocol 'concat' not on whitelist 'file'!`. The same for `subfile,,start,0,,end,100,,:tone.ac3`: `Protocol 'subfile' not on whitelist 'file'!`. The whitelist works and it does treat the comma form of subfile as a protocol.
7. `ffmpeg -nostdin -v error -protocol_whitelist file,pipe -i <file> -map 0:a:0 -f f32le -acodec pcm_f32le - | wc -c`: M4A 768000 bytes (exactly 96000 stereo frames), MP3 768000, AC-3 774144, E-AC-3 774144, ADTS AAC 778240, mono MXF 384000. Decoded M4A peak 0.0789 against expected 0.0708, inside the test's 0.02.
8. The plan's read loop, reproduced verbatim in shape against a child that sleeps 3 s before writing 8 bytes, with a 0.5 s budget: `elapsed=3.02s`. The budget was consulted only after `read()` returned; a child that never writes and never exits is never killed.
9. `uv run python -c "from cumple.specs import load_all; ..."`: `load_all()` returns a dict with keys `netflix-2.0` and `acx`; `evaluate`, `app`, `iter_blocks`, `probe` import as the tests expect. `sf.LibsndfileError` is a `RuntimeError` subclass, so `pytest.raises(RuntimeError)` catches the untouched WAV path.
10. `grep -n "containers:" src/cumple/specs/profiles/*.yaml`: 14 of 39 profiles carry a containers clause (youtube, spotify, apple-podcasts, ebu-r128-s1-short and 21 others do not). `grep '"container"\|"decoder"' src/cumple/report/json_out.py`: nothing; the JSON format block has no container or decoder field. `qc_sheet.py:142` and `:168` print the container only when `bit_depth` is truthy.
11. `ls ~/.cache/cumple/ebu-loudness-test-set | head -3`, `brew --prefix libebur128`, `uv run python -c "import loudcheck, pyloudnorm"`: all present; `ffmpeg -version` is 9.0.1 at `/opt/homebrew/bin`. a grep for the em and en dash characters in `docs/BENCHMARK.md` counts 0 (the script's minus signs are U+2212, not dashes).
12. `.github/workflows/tests.yml`: the Test step comment says only the 29 EBU cases skip; `README.md:413-414` says "CI runs 171 of them on Ubuntu, macOS and Windows"; `tests/test_counts.py` checks only the number before "of them on Ubuntu".
13. `pyproject.toml`: ruff selects `E`, so E402 (imports after code) is enforced on `tests/`.

## Concerns

### 1. `measure_file` does not exist; Task 2 cannot pass as written
Severity: Critical. Blocking.
Framework: Library hallucination; confidence without correctness.

What I see: `tests/test_ffmpeg_io.py` (plan, Task 2 Step 1) imports `from cumple.meters.measure import measure_file` and calls it in four tests; Task 2 Step 3 says "In `src/cumple/meters/measure.py`, `measure_file` (around line 199)". The function at line 179 is `measure`; nothing named `measure_file` exists anywhere in `src`, `tests` or `scripts` (check 3). A module-level ImportError fails collection of the whole file, taking Task 1's passing tests down with it.

Why it matters: Step 2's expected failure ("probe raises LibsndfileError, iter_blocks rejects info=, AudioInfo has no decoder") never happens; the file errors before any test runs, and after Step 3 it still errors. An implementer either invents `measure_file` (a second entry point for one call) or silently edits the test, the pattern the receipt warns about.

What to do: replace every `measure_file` with `measure` in the four tests and in the Step 3 instruction ("in `measure`, line 199, pass `info=info`"). Check that `measure(path)` with no profile arguments is what the tests want (it is; `measure_args` is only for Leq(m) and LFE).

### 2. The Windows-drive regex test asserts something the regex cannot match
Severity: Critical. Blocking.
Framework: Inversion (what would make this test fail every time?).

What I see: `test_safe_path_accepts_a_windows_drive_prefix_shape` asserts `_SCHEME.match("C:\\bounce\\mix.m4a") and _DRIVE.match(...)`. `_SCHEME` is `^[A-Za-z][A-Za-z0-9+.\-]+:`, which needs at least two characters before the colon, so a one-letter drive never matches it (check 4). The assertion is False on every platform.

Why it matters: a red test in Task 1 on the first run, and the test's comment ("the scheme regex must not mistake C:\ for a protocol") describes a defence that the code takes by accident of the `+` quantifier rather than by the `_DRIVE` carve-out the module documents. Either the regex or the test is wrong; today both disagree with each other.

What to do: decide which is the design. If drive letters should be caught by `_SCHEME` and excused by `_DRIVE` (what `safe_path` reads as), change `_SCHEME` to `^[A-Za-z][A-Za-z0-9+.\-]*:` (star, not plus). If a one-letter scheme is meant to be impossible, change the assertion to `not _SCHEME.match("C:\\...")` and drop the `_DRIVE` clause from `safe_path`. Either way the resolved absolute path handed to ffmpeg starts with `/` or `X:\`, so the security holds; the test does not.

### 3. The decode budget is only checked between reads; a stalled ffmpeg is never killed
Severity: High. Blocking (hang risk, and the frame promises a timeout on every call).
Framework: Pre-mortem ("the watch folder stopped at 3 am and nobody knew why").

What I see: `iter_blocks_ffmpeg` checks `time.monotonic() - started > budget` at the top of the loop, then calls `proc.stdout.read(want)`, which on a `BufferedReader` blocks until `want` bytes or EOF. A child that emits nothing (a demuxer waiting on a truncated index, a decoder spinning on a corrupt frame, a hung network filesystem behind the "file" protocol) keeps the reader inside `read()` forever; my reproduction with a 0.5 s budget waited the full 3.02 s of a sleeping child (check 8). `test_decoding_stops_when_the_budget_expires` passes because with a zero budget the pre-read check fires before the first read; it never exercises a stall. `PROBE_TIMEOUT_S` on ffprobe is real (`subprocess.run(timeout=)` kills); the decode budget is advisory.

Why it matters: `cumple check` and the desktop app would sit on the file with no message; in the frame's own words the fixed policy is "a timeout" on every subprocess call. The security checklist's "expensive operations bounded" item is only half met.

What to do: arm a `threading.Timer(budget, on_budget)` before the loop, where `on_budget` sets a flag and calls `proc.kill()`; cancel it in `finally`. After the loop, if the flag is set raise `FfmpegError("... exceeded its N s budget ...")` regardless of the exit code (a killed child returns -9 and the current code would report "ffmpeg exited -9"). Change the budget test to a child that stalls: monkeypatch `tools` to a `Ffmpeg` whose `ffmpeg` is a tiny script that sleeps (`sys.executable -c "import time; time.sleep(30)"`) and assert the call returns within a second with "budget" in the message. Also close `proc.stdout` in `finally` (or use `with proc:`) so a killed pipe does not leak a file descriptor per file in the watch folder.

### 4. The frame's MP3 promises have no test, and the one MP3 test is gated on the wrong tool
Severity: High. Blocking.
Framework: Socratic evidence ("which test proves the acx pass?"); test that does not test what its name says.

What I see: 01-frame.md line 12 promises that `format.container` "fails a netflix-2.0 check on an MP3 with the quoted clause ... and passes an acx check, whose profile lists mp3". The plan's only engine test, `test_netflix_fails_the_container_and_names_the_codec_and_acx_bit_depth_says_not_pcm`, evaluates netflix-2.0 on an M4A and never loads acx; the name promises acx, the body does not deliver it, and acx has no `bit_depths` at all (`acx.yaml`), so "acx bit depth" cannot be a finding. No test anywhere puts an MP3 through `evaluate`. Separately, `test_mp3_reads_through_libsndfile_and_says_so` skips when ffmpeg is absent, only to write the fixture, so the claim "libsndfile reads MP3" is verified on Linux CI and this Mac and skipped on the macOS and Windows jobs, where the wheel differs. libsndfile writes MP3 itself (check 2).

Why it matters: the acx pass is the one place the new `MP3 -> mp3` engine token is load-bearing (a typo there fails every audiobook delivery and nothing is red), and "libsndfile reads MP3" is about to go into the README, the FAQ and AI_USAGE on the strength of one platform.

What to do: write the MP3 fixture with `sf.write(..., format="MP3", subtype="MPEG_LAYER_III")` at 44100 Hz in `conftest.py` or the test, no skip; add `test_an_mp3_fails_netflix_with_the_clause_and_passes_acx`: `evaluate(profiles["netflix-2.0"], measure(mp3))` has `format.container` FAIL with "compression is never allowed" in the clause, and `evaluate(profiles["acx"], measure(mp3))` has `format.container` PASS with `measured == "MP3"`. Rename the netflix M4A test to what it does.

### 5. "Reported with the decoder named" holds only under 14 of 39 profiles
Severity: High. Non-blocking if Victor accepts the finding as the sole carrier; otherwise two lines.
Framework: Socratic implications (follow the AAC through every report surface).

What I see: the decoder appears in exactly one place, the `measured` text of `format.container`, which exists only when the profile has a `containers` clause (check 10). For youtube, spotify, apple-podcasts, ebu-r128-s1-short and 21 more, an AAC delivery produces a report in which nothing names the container, the codec or ffmpeg: `json_out.py`'s format block has no container field, and `qc_sheet.py:142` and `:168` print the container only when `bit_depth` is truthy, which is never for a lossy file, so the sheet header says "48 kHz · stereo" and drops "M4A" entirely. Only `cumple info` names it.

Why it matters: the frame's user-visible promise is that a compressed file is "reported with the decoder named"; a post supervisor reading the PDF for a YouTube delivery cannot tell the measurement came from a decoder, or that the file was not PCM.

What to do: add `"container": m.info.container if m.info else None`, `"codec"` and `"decoder"` to the JSON format block; in `qc_sheet.py:142` and `:168` print the container unconditionally and the depth when present (`"AAC via ffmpeg 9.0.1"` where "24-bit WAV" would go). One test: `report_to_dict(evaluate(profiles["youtube"], measure(aac_file)))` contains "ffmpeg", and `write_sheet` HTML contains "M4A".

### 6. The README's CI sentence becomes false and the plan re-pins only its number
Severity: High. Blocking (one sentence; the run's scale treats a doc left saying something false as a constraint violation).
Framework: Pre-mortem, and the receipt's own lesson (a checkable number written without the check).

What I see: `README.md:413-414` says "CI runs 171 of them on Ubuntu, macOS and Windows on every push. The 29 EBU cases ..." Task 3 Step 5 updates the number to N-29. After this PR the eleven ffmpeg-gated tests (five in Task 1, five in Task 2, one in test_reader) run on Ubuntu, where apt installs ffmpeg, and skip on the macOS and Windows jobs, which the plan itself says will skip them. `tests/test_counts.py` matches only `runs (\d+) of them on Ubuntu`, so the false clause about macOS and Windows survives the suite. The comment at `tests.yml:29-30` ("The 29 EBU conformance cases skip here") is likewise stale on two of three runners.

Why it matters: the README's numbers are the thing the last run's skeptic caught the ledger getting wrong; this one would be wrong on the day it merges.

What to do: reword to "CI runs N-29 of them on Ubuntu, and N-29-11 on macOS and Windows, which have no ffmpeg; the 29 EBU cases ..." (keep the regex shape `runs (\d+) of them on Ubuntu`), and add a line to the workflow comment. If the count of gated tests is re-derived, do it from `uv run pytest -rs` on a machine without ffmpeg (or with `CUMPLE_FFMPEG` pointed at an empty directory and PATH stripped), not by counting decorators.

### 7. Smaller traps, bundled
Severity: Medium. Non-blocking, all cheap.
Framework: Blind spots (environment gaps, cross-platform, tests passing for the wrong reason).

- `ruff check` will fail Task 2 Step 4: the appended block starts with five `from ... import` lines after the existing functions, and ruff's `E` set includes E402 (check 13). Put the imports at the top of the file.
- `find_ffmpeg` with `CUMPLE_FFMPEG` naming a directory tries `p / "ffmpeg"` and never `ffmpeg.exe`, so the documented override does nothing on Windows; and it resolves symlinks before deriving `ffprobe`, so a snap or shim `ffmpeg` whose real target has no sibling `ffprobe` returns None with the "install ffmpeg" message on a machine that has it. Use `shutil.which("ffmpeg", path=str(p))` and `shutil.which("ffprobe", path=...)` (PATHEXT-aware), and derive `ffprobe` from the unresolved directory, falling back to `shutil.which("ffprobe")`.
- `_SCHEME` does not match `subfile,,start,0,,:x.wav` (check 4), so that entry in `test_safe_path_refuses_protocols_and_non_files` passes only because the file does not exist; the whitelist and `resolve()` still stop the real attack (check 6). Either drop the comma-form string from the test or add `^subfile,` to the refusal so the test means what it says.
- `find_ffmpeg()` runs `ffmpeg -version` on every `probe` and again on every `iter_blocks`, two extra process spawns per file. Cache it (`functools.lru_cache` keyed on `os.environ.get("CUMPLE_FFMPEG")` and `shutil.which("ffmpeg")`) or carry `tools` on `AudioInfo`.
- The FAQ replacement text omits "diff and fix still need PCM files", which the frame's user-visible promise asks of the page as well as the README. Six words.
- Five containers are claimed in README, FAQ and AI_USAGE; the plan fixtures only M4A. AC-3, E-AC-3, ADTS AAC and a mono OPAtom MXF each encode in one ffmpeg call and decode through the plan's argv (checks 5 and 7). Parametrize `aac_file` into a `compressed_file` fixture over `("-c:a aac", ".m4a")`, `("-c:a ac3", ".ac3")`, `("-c:a eac3", ".ec3")`, `("-ac 1 -c:a pcm_s24le -f mxf_opatom", ".mxf")` and assert container, codec, and `is_pcm` for the MXF; then the docs claim rests on a run.
- `test_the_version_is_read_from_the_binary` asserts the first character is a digit; static nightly builds print `ffmpeg version N-118000-g...` and some distributions `n7.1`. Accept a leading `n` or `N`, or drop the test.

## Contradictions

- Frame line 14 says every subprocess call carries `-nostdin`; ffprobe has no such option, and the plan correctly uses `stdin=DEVNULL` for it. Wording in the frame, not a defect in the plan; the receipt should say "stdin closed on every call, `-nostdin` on ffmpeg".
- Plan Task 2 Step 2 expects the new tests to fail on `LibsndfileError`, a rejected `info=` and a missing `decoder`; they fail on an ImportError before any of that (concern 1).
- The frame promises an MP3 that fails netflix-2.0 and passes acx; the plan tests netflix on an M4A and acx on nothing (concern 4).
- Frame line 29 says "four tasks, each with its failing test first"; Tasks 3 and 4 have no new failing test and lean on the existing site, counts, related and site-numbers tests. Acceptable for docs and a regenerated report, and worth saying so in the receipt rather than leaving the frame's sentence to read as met.
- The test name `..._and_acx_bit_depth_says_not_pcm` names a finding the acx profile cannot produce (no `bit_depths`).

## Unsupported claims

- "libsndfile 1.2.2 already reads MP3 natively": supported on this wheel (check 1), and by the CI Linux job once ffmpeg writes the fixture; unsupported on the macOS and Windows jobs until the fixture is written by libsndfile (concern 4).
- "decodes AAC, AC-3 and E-AC-3 and the audio of MXF, MOV and MP4 files" (README, FAQ, AI_USAGE): supported here by my scratch fixtures for AAC, AC-3, E-AC-3 and MXF (checks 5 and 7), by no test in the plan for anything but M4A, and by nothing at all for MOV and MP4 with a video track (the `-select_streams a:0` and `-map 0:a:0` path is right in principle and untried).
- AI_USAGE's "a reviewer with the security checklist read it before merge" is written in Task 3, before the review in the build phase happens. True by merge if the graph runs as framed; the sentence should be added by the session that has the review, not by the docs task.
- "AAC priming and padding may add or trim a frame or two of samples": M4A decoded to exactly 96000 frames (the edit list trims priming); raw ADTS decoded to 97280. The 4096 tolerance covers both; the comment slightly misstates which container needs it.
- Task 3's "if a one-line note under `info` fits" at README:108 names a "Commands" heading with no `info` subsection at that line. Harmless; the implementer will hunt.

## Verdict

Ship with changes. Two of the concerns are mechanical and would stop the first `uv run pytest` of Tasks 1 and 2 cold (a name that does not exist, an assertion that cannot be true); the third is a real hang in the one place the frame promised a timeout; the fourth and sixth are the frame's own promises left without a run. None of them argue against the design, which is the right one: one module, one argv, resolve-then-whitelist, and a fallback that only wakes when libsndfile has already said no. Fix 1, 2, 3, 4 and 6 before the implementers start; 5 and 7 can ride in the same tasks or be listed in the receipt as accepted residue.

Counts: Critical 2, High 4, Medium 1 (bundled).

## Re-check after the amendment

Plan re-read from disk at commit `ab68adb` (1042 lines). Same reviewer, same scale, still reading only the files named above plus the amended plan.

### Status per concern

1. `measure_file` does not exist. Addressed. Global Constraints line 19 says so outright; the tests import `measure` (line 501) and call it (540, 541, 549, 561, 565, 574, 584); the edit instruction names `measure` (line 764).
2. The drive-letter regex test. Addressed. `_SCHEME` now uses the star quantifier (line 249, constraint line 17); the test at lines 103 to 111 asserts the four shapes the regex and the carve-out now produce, and `safe_path`'s refusal list gains `C:relative.m4a` (line 94). All four assertions and the two refusals evaluate True on this machine (check 5 below).
3. The budget only checked between reads. Partly. The design is fixed: a daemon `threading.Timer` sets `expired` and kills the child (lines 420 to 431), the loop reads until EOF, the `expired` check wins over the exit code (449 to 452), the `finally` cancels the timer, kills a survivor and closes stdout (453 to 458). Against a real ffmpeg this works: a 600 s file decoded with `-re` and a 1 s budget unblocked at 1.02 s with exit -9 and no ffmpeg left behind, and closing the generator after one block ran the `finally` in 2 ms with the timer thread gone (checks 1 and 2). The test that is supposed to prove it cannot pass: see new finding A.
4. MP3 promises untested and the fixture gated on ffmpeg. Addressed. `mp3_file` is written by libsndfile (lines 510 to 518), the acx pass and the netflix fail are asserted on an MP3 with no ffmpeg (558 to 567), the reader test writes its own MP3 and never skips (620 to 630), and the netflix M4A test is renamed to what it does (547). Fixture verified: check 6.
5. Decoder named only inside one finding. Addressed. JSON gains `container`, `codec`, `decoder` after `samplerate` (lines 766 to 772; the anchor key exists at `json_out.py:44`), the sheet gets `_encoding()` for the Format cell and the meta line (774 to 795), and two tests cover youtube (no containers clause) for an AAC and a WAV (571 to 588). `render_html` and `report_to_dict` import from where the tests say (check 7). No existing test pins the old "24-bit" text (check 7).
6. README's CI sentence. Partly. The sentence is rewritten with a per-platform count and the workflow comment is corrected (lines 912 to 919, 974 to 984), but the command that derives G undercounts and the path to `uv` in it does not exist on this Mac: new findings B and C.
7. The bundle:
   - E402 from appended imports: addressed (line 493, "TOP import block", with the sorted list at 496 to 504).
   - `CUMPLE_FFMPEG` on Windows and the resolved-symlink ffprobe: addressed (lines 289 to 301, `shutil.which` for both binaries, no `resolve()`; PATHEXT-aware by `which`). Verified with the hint as the binary, as its directory and as a symlinked directory (check 4). Residue: a hint naming a binary not called `ffmpeg` is silently ignored and the PATH pair is used instead; the docstring at 282 should say the binary must be named `ffmpeg`.
   - `subfile,,` passing vacuously: addressed by removal (line 94 no longer lists it); the whitelist still refuses that form (first-pass check 6).
   - Two `ffmpeg -version` spawns per file: addressed (lines 284 to 290, `lru_cache` keyed on the hint and `which("ffmpeg")`). The key changes when PATH changes and comes back (check 4: two cache misses across a PATH change and its reversal, no stale hit).
   - FAQ omits the diff and fix clause: addressed (line 948).
   - Only M4A fixtured: addressed (lines 178 to 198, four containers parametrized; the MXF row uses the mono OPAtom shape I verified in the first pass).
   - Version regex: addressed (line 175, `^[nN]?\d`).

### Checks run

1. The amended loop, reproduced verbatim in shape, against the plan's stand-in `#!/bin/sh\nsleep 30\n` (chmod 755, `Popen([path])`, no shell) with a 0.5 s budget on this Mac (`/bin/sh` is bash 3.2.57): `budget: exceeded 0.5 s elapsed=30.02s`. The Timer killed `sh` on time; `sleep 30`, forked by `sh`, inherited the pipe's write end and held it open, so `read()` returned only when sleep exited. `pgrep` showed the orphaned `sleep 30` still running after the kill. The shebang itself was honoured (the script ran without a shell), which answers the (b) question in the affirmative; the stall is the problem.
2. The same loop with two candidate fixes and the real binary. Stand-in changed to `exec sleep 30` with `proc.kill()`: `elapsed=0.51s`. Original forking stand-in with `start_new_session=True` and `os.killpg(proc.pid, SIGKILL)`: `elapsed=0.52s`. Real ffmpeg on a 600 s WAV with `-re` (throttled to real time) and a 1 s Timer: `expired=True exit=-9 bytes=589824 elapsed=1.02s`, no ffmpeg process left. GeneratorExit: `next()` once then `close()` on the generator: `close() took 0.002s`, no ffmpeg left, `threading.active_count()` back to 1.
3. `pytest -rs -q` on a scratch file with the plan's marker shape (two plain gated tests and one parametrized over four cases): the summary prints `SKIPPED [1] ...:6`, `SKIPPED [1] ...:11`, `SKIPPED [4] ...:16` and `6 skipped`; `grep -c "ffmpeg and ffprobe are not on PATH"` prints `3`.
4. `shutil.which("ffmpeg", path=d)` and `which("ffprobe", path=d)` for the hint `/opt/homebrew/bin/ffmpeg` (a file, so `d` is its parent), `/opt/homebrew/bin` and `/opt/homebrew/opt/ffmpeg/bin`: both binaries found in all three; `which("ffmpeg", path="/usr/bin")` is None. An `lru_cache` keyed on `("", which("ffmpeg") or "")` across `PATH=/usr/bin:/bin` and back: 2 misses, keys `('', '/opt/homebrew/bin/ffmpeg')` and `('', '')`.
5. The amended regexes on the plan's strings: lines 108, 109, 110, 111 all True; `C:relative.m4a` and `data:audio/aac;base64,AAAA` refused; `/Users/Victor/mix.m4a` untouched. Side effect noted: a relative name such as `Mix:final.m4a` is refused before `resolve()` runs.
6. The plan's `mp3_file` fixture verbatim (`sf.write(..., 48000, format="MP3", subtype="MPEG_LAYER_III")`): 9288 bytes; `sf.SoundFile` reports `MP3 MPEG_LAYER_III 48000 2 96000`; the current `probe()` returns container `MP3`, bit depth None, 96000 frames.
7. `grep -n "bit\b|-bit|24-bit|WAV\b|· stereo|Format" tests/test_qc_sheet.py tests/test_pdf.py`: nothing; `test_qc_sheet.py`'s assertions pin "FAIL", the profile name, the SVG, the source URL and CSS tokens, not the depth text. `uv run python -c "from cumple.report import render_html; from cumple.report.json_out import report_to_dict"`: both import. `tests/test_app.py` exists for Step 4.
8. `ls ~/.local/bin/uv`: `No such file or directory`; `which uv` is `/opt/homebrew/bin/uv`. `PATH=/usr/bin:/bin /opt/homebrew/bin/uv run pytest tests/test_reader.py --collect-only -q`: collects 6 tests; on that PATH `shutil.which("ffmpeg")` is None, so the hiding works once uv is addressed by its real path (the venv's python is the Framework 3.12 at an absolute path, so uv needs nothing from PATH).

### New findings

#### A. The stalling-child test blocks for 30 s and fails its own timing assertion
Severity: Critical. Blocking.
Framework: Pre-mortem on the test itself; the integration-point blind spot (a child of a child).

What I see: `test_a_stalled_decoder_is_killed_when_the_budget_expires` (plan lines 154 to 170) writes `#!/bin/sh\nsleep 30\n` and asserts the call returns in under 5 s. `sh` forks `sleep` and waits for it; SIGKILL to `sh` leaves `sleep` alive holding the pipe's write end, so `read()` blocks until sleep exits (check 1: 30.02 s on this Mac; dash on the Linux runner forks the same way). The test raises the right error with the right word in it, 25 s too late, and leaves an orphan `sleep`. Task 1 Step 4 would be red here and on Linux CI.

Why it matters: the test exists to prove concern 3 fixed; as written it proves the opposite. The same shape bites in production wherever `ffmpeg` on PATH is a wrapper script that forks the real binary (snap's `/snap/bin/ffmpeg` on Ubuntu desktops does exactly this): the budget kills the wrapper and the decode runs on.

What to do: two options, and I would take both. (i) In the module, open the child with `start_new_session=True` and kill with `os.killpg(proc.pid, signal.SIGKILL)` when `hasattr(os, "killpg")`, falling back to `proc.kill()` (Windows); check 2 shows the forking stand-in then dies in 0.52 s. Keep the stand-in as it is, since it now proves the group kill. (ii) If only the test is to change, write `#!/bin/sh\nexec sleep 30\n` (0.51 s in check 2) and accept the wrapper case as residue in the receipt. Also catch `subprocess.TimeoutExpired` from the two `proc.wait(timeout=5)` calls and re-raise as `FfmpegError`: a child stuck in uninterruptible I/O (a dead network mount is one of the stalls this budget exists for) survives SIGKILL until the I/O returns, the wait raises after 5 s, and today that surfaces as a `SubprocessError` that `reader.iter_blocks` does not translate.

#### B. The command that derives G counts summary lines, not skipped tests
Severity: High. Blocking (a checkable README number that would be wrong on the day it merges, the exact failure the last receipt recorded).
Framework: Socratic evidence ("what does this command actually count?").

What I see: Task 3 Step 5 (plan line 980) pipes `pytest -rs -q` into `grep -c "ffmpeg and ffprobe are not on PATH"`. pytest folds skips that share a file, line and reason into one line with a bracketed count, and every case of a parametrized test shares its definition line, so `test_each_claimed_container_probes_and_decodes` prints once as `SKIPPED [4]`. Check 3 reproduces it: six gated tests, `grep -c` says 3. With the plan's own tests G would come out three short. A second inaccuracy: the sentence says "G fewer on macOS and Windows", but the stall test carries its own `win32` skip (line 154), so Windows runs G+1 fewer.

What to do: take G from pytest's last line instead (`... passed, G skipped in ...`) with `tail -1`, or sum the bracketed counts (`grep -o 'SKIPPED \[[0-9]*\]' | awk -F'[][]' '{s+=$2} END {print s}'`). Then either word the sentence so it is true on all three runners ("runs N-29 of them on Ubuntu; macOS skips G more that need ffmpeg, Windows G+1") or drop the per-platform figure and say "the ffmpeg-gated decode tests skip on macOS and Windows", keeping the `runs (\d+) of them on Ubuntu` shape the counts test matches.

#### C. `~/.local/bin/uv` does not exist on this Mac
Severity: Medium. Non-blocking (the step fails loudly and the fix is the path).
Framework: White hat (missing data about the machine).

What I see: plan line 980 addresses uv as `~/.local/bin/uv`; the binary is `/opt/homebrew/bin/uv` (check 8), and the plan's own bare PATH excludes Homebrew on purpose. The command as written prints `no such file or directory`.

What to do: write `UV=$(command -v uv); PATH=/usr/bin:/bin "$UV" run pytest ...`, which captures uv before the PATH is narrowed and works on any machine. Check 8 shows `uv run` needs nothing else from PATH here.

#### D. Small residue, for the receipt
Severity: Medium, non-blocking.
- A relative path whose first characters are letters followed by a colon (`Mix:final.m4a`) is refused as a protocol before `resolve()` runs (check 5). Checking the resolved string instead of the raw one keeps the whole defence (the resolved string is what ffmpeg sees) without the false refusal. Rare on macOS, where Finder writes such names with a slash internally.
- `_locate` ignores a `CUMPLE_FFMPEG` that names a binary not called `ffmpeg` and silently uses PATH; say so in the docstring or in the "install ffmpeg" message.

### Verdict after re-check: Ship with changes

The amendment took every one of the seven findings and the design is now the right one, including the budget kill that check 2 shows working against the real ffmpeg. What remains is one test that cannot pass as written (A: a forking stand-in the kill does not reach), one number derived by a command that does not count what the sentence claims (B), and a wrong path to uv (C). Fix A and B before Task 1 and Task 3 run; C rides with B.

Counts remaining: Critical 1, High 1, Medium 2 (C, and the D bundle).
