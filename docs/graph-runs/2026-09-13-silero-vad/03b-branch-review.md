# 03b Branch review: Silero VAD as an optional dialogue-gate backend

Date: 2026-09-13. Range: `9bc9ee4..f98b1b4` (six commits) on `loop/03-silero-vad`, read from the diff file and `git show`. Read-only: the worktree was clean before and after (`git status --short` empty); the wheel was built into the session scratchpad; the probes ran from scratch scripts there. The full suite was not re-run (252 passed at head per three reviews); `uv run pytest --collect-only` reports 252, ruff check and format are clean at head.

## Inputs read

`01-frame.md`, the plan, `03-skeptic.md` (both passes), the ledger `progress.md`, the three task reports, the previous receipt (`2026-09-12-ffmpeg-codec-conformance/05-receipt.md`), the diff in passes, then at head: `src/cumple/meters/vad.py`, `dialogue.py`, `measure.py`, `cli.py`, `checks/engine.py`, `report/json_out.py`, `report/qc_sheet.py`, `io/reader.py` and `io/ffmpeg.py` (block yielding), `scripts/dialogue_benchmark.py`, `scripts/fetch_real_dialogue.sh`, `packaging/cumple.spec`, `pyproject.toml`, `uv.lock` (the onnxruntime entry), both workflows, `tests/test_vad.py`, `tests/test_site_numbers.py`, `docs/DIALOGUE.md`, `README.md`, `AI_USAGE.md`, `CONTRIBUTING.md`, `site/index.html`, `docs/ROADMAP.md`, `tests/fixtures/NOTICE.md`, `src/cumple/models/*`, the six profile YAMLs that mention the speech detector.

## Plan alignment

Every capability in the frame's contract is present and wired the way the plan says:

- `src/cumple/meters/vad.py`: `SileroDetector(samplerate, channels, roles=None, session=None)` with `feed` and `result`, composing one `SpeechDetector` for levels and frame count; chunked `resample_poly` to 16 kHz with a 50 ms native tail and a rounded skip; model state and 64-sample context carried across 512-sample windows; the 20 ms grid mapped with exact integers (`i * 320 // 512`); `dilate_mask` shared from `dialogue.py`; `BACKENDS = tuple(BACKEND_NAMES)` so the list lives once.
- `measure(vad=)`, `measure_package(vad=)`, `_run(vad=)`, validated through `describe_backend`; `check --vad` and `CUMPLE_VAD`; the two `console.print` calls in `check` escape rich markup.
- The three engine notes, the sheet footer and the JSON `measurement.speech_backend` all derive from `describe_backend` and `SpeechResult.backend`; `grep` over `src/` finds no report string naming a backend on its own. Probed at head: the terminal table, the `.qc.html` footer and the `.qc.json` all say "Silero VAD v6.2" under `--vad silero` and contain no "heuristic"; the heuristic run says "heuristic speech gate" and no "Silero".
- The model, `SILERO_LICENSE` and `models/__init__.py` ride in the wheel (rebuilt into the scratchpad: 2,327,524 bytes, 1,075 bytes, 102 bytes); `vad` extra and the dev group carry `onnxruntime>=1.17`; `packaging/cumple.spec` excludes `onnxruntime`.
- The fixture and its NOTICE; `scripts/dialogue_benchmark.py` runs `SileroDetector` with one shared session and no inference of its own; `docs/DIALOGUE.md` regenerated with the heuristic's loudness numbers byte-identical; README, CONTRIBUTING, page, AI_USAGE, ROADMAP updated; the README pin test extended.

Deviations, all justified in the plan or the reports: the JSON key is `measurement.speech_backend` rather than the frame's `speech.backend` (the plan chose it; the frame's line was shorthand); the frame's `pip install` route became the git route (frame amended in `1afd451`); `functools.cache` instead of `lru_cache(maxsize=None)` (ruff UP033); `result()` returns `fraction=None` when the model never ran (Task 1 review addition, tested); the session cache (Task 1 review addition, checked by hand, not by a test). The Task 3 reviewer's Important (the script's docstring) and two minors (AI_USAGE:147, README:434) were routed to this wave by the ledger and are still open at head; findings below.

## Honesty and licensing

- "v6.2": the bundled file's sha256 begins `1a153a22f4509e29` (recomputed here), the hash the skeptic matched to upstream tags v6.2 and v6.2.1 (v5.1.2 is `2623a295...`). The label is true on every surface: `BACKEND_NAMES`, the module docstring, `models/__init__.py`, README:118. One place still says "v5": `scripts/fetch_real_dialogue.sh:52` (finding I2).
- `SILERO_LICENSE`: MIT, "Copyright (c) 2020-present Silero Team", the full permission and warranty text; no trailing newline (cosmetic). It is in the wheel and, through `collect_data_files("cumple")`, in the frozen apps, which satisfies MIT's notice clause for both.
- Fixture: `tests/fixtures/speech-librivox-3s.wav` is 16 kHz, mono, PCM_16, 48,000 frames, 3.0 s (checked with `sf.info`). NOTICE names the reading, the chapter, the offsets, the ffmpeg route and the US public-domain basis with the text's caveat. `git ls-files` matched by audio extension returns only this file (and the `.onnx`, which is not audio), so "the one audio file in the repository" is true.
- README against DIALOGUE.md at head: Silero 0 % on both M&E rows (true); Tears of Steel -14.0 against -12.8 (1.2); Sintel -28.0 against -18.8 (9.2); heuristic 6.7 from the -6.73 delta cell; "worse than the heuristic's 6.7 LU there" is true. "Silero VAD reads 0 % on all of it" (the closing line) is true of all seven no-dialogue rows. One wording concern on "within 1.2 LU" (finding M1): the table gives Silero to one decimal and no delta column, so the true delta is anywhere in 1.17 to 1.27 LU and "within" is a bound the table cannot support; the heuristic sentence's form ("read 1.6 LU low") is the honest form.
- Install route: the README, the `VadUnavailable` message and the CLI help all use `uv tool install --python 3.12 "cumple[vad] @ git+https://github.com/victor10days/cumple"`; no `pip install` anywhere in the diff. "Only `check` takes the flag": `grep` for `measure(` callers confirms `watch.py`, `fix.py`, `app/api.py` and `app/selftest.py` pass no `vad` and read no env, so the sentence is true.
- AI_USAGE: the file calls itself "the honest record" and now contradicts itself. Line 147 (5 September) says Silero "was more precise on both films"; the new section (line 279) says "worse on quiet dialogue under music" and "reads further under the reference than the heuristic does". On the gated number Silero was already 9.3 LU under against the heuristic's 6.7 in the 8 September table, so the old line was loose then and is contradicted now. The dated form does not excuse it because the new section does not say it supersedes the old one, and a reader has no other way to know which is current. One reconciling sentence in the new section is due (finding I3); leave the old entry as written.
- README:434 ("Three reports are headed cumple 0.2.0 and the benchmark 0.2.1: all were generated on 8 September 2026") is false at head: CONFORMANCE.md and PERF.md are 0.2.0 from 8 September; BENCHMARK.md is 0.2.1 from 12 September (already so at base); DIALOGUE.md is now 0.2.1 from 13 September. Two of the three claims are wrong (finding C2).
- The profile clause notes ("approximates that gate with an open speech detector and says so on every sheet") stay true for both backends; the page's FAQ ("cumple uses a heuristic speech detector, labelled as such on every sheet") stays true for the default and was rightly left alone.

## Correctness

Probed with the shipped module from a scratch script (fixture tiled nine times, 27 s, fed in blocks, a default 10 s chunk against `CHUNK_S` patched to 1000 s):

- 44.1, 48, 96 and 22.05 kHz: 0 mask frames differ between chunked and one-pass, 1350 frames both sides, fraction 1.0 both. The `gcd` path gives (160, 441), (1, 3), (1, 6), (320, 441); the residual chunk at `result()` runs through the same tail path.
- Very short files at 48 kHz stereo (no centre): 0 samples gives an empty mask and `fraction None`; 10 ms gives an empty mask and `None`; 25 ms gives one frame and `None` (the sub-window path); 1.0 s gives 50 frames and `fraction 0.0`; 1.28 s gives 64 frames and `0.0`. The heuristic on the same inputs gives `None` up to 1.28 s (`MIN_FRAMES`), so between 32 ms and 1.28 s the two backends disagree on whether the share is knowable, and the engine picks a different rule for each (the heuristic's "not measurable, assumed dialogue-led" against Silero's "0 %" and the full-programme switch). Real deliveries are longer; finding M2.
- No centre channel: `pick_channel` folds to the mean; the white-noise test covers it. The centre pick is covered by its test.
- Block buffers: `sf.blocks` yields a fresh array per block and the ffmpeg path builds one from fresh bytes, so `_native = x` holding a reference to the first picked block is safe.
- Session cache: `_session_for` is keyed on the resolved path string, lives for the process, and is only reached after the import and `is_file` checks, so a missing extra or model is never masked. A relative `CUMPLE_SILERO_MODEL` with a changing cwd could alias two files under one key; not a real use.
- `_run` validation order: `describe_backend(vad)` runs after the meters are built and before any audio is read, so an unknown name never costs a decode; it does run after `probe()` and, for packages, after `load_package`, so a bad path is reported before a bad backend name. Acceptable; moving the call to the top of `measure()` would be tidier (M4).
- CLI: `vad or os.environ.get("CUMPLE_VAD", "heuristic")` means `CUMPLE_VAD=""` exits 2 with "unknown speech detector ''" rather than falling to the default (probed); M3. `--vad dolby` exits 2 naming both choices; `--help` renders "(needs the vad extra)" with no bracket lost; the escaped `VadUnavailable` message keeps `cumple[vad]` (the test pins it).
- Engine notes for both backends read as sentences (probed on noise): "Silero VAD v6.2 gate, an approximation of Dolby Dialogue Intelligence"; "approximation of Dialogue Intelligence: Silero VAD v6.2 gate, N speech blocks, BS.1770-1 (no relative gate)"; "the Silero VAD v6.2 gate reads low on dense mixes (docs/DIALOGUE.md), so this pass may be a false pass"; the last is true of Silero on both films. Sheet footer: "Dialogue-gated rules use the Silero VAD v6.2 gate, an approximation of Dolby Dialogue Intelligence, and say so above."
- Benchmark script: one `_SESSION`, passed as `session=`; `probe` and `iter_blocks` with `default_roles`, the same roles `measure()` uses, so the report's Silero columns are the shipped detector's. `grep` for `mono16k`, `vad16k`, `SILERO_MODEL`, `SILERO_CHUNK`, `SILERO_CONTEXT`, `VAD_FS`, `ort` finds nothing live; `sf` and `resample_poly` are still used by the alignment code. The module docstring (lines 16 to 20) is stale (I1).
- `scripts/fetch_real_dialogue.sh:52-54` still labels the model "v5", downloads it from `master` into `~/.cache/cumple/`, and tells the user to run the benchmark with `--with onnxruntime`; nothing reads that file any more (I2).

## Tests

- Each new test was read for whether it can fail. Sixteen of the nineteen can. Three concerns:
  - `test_chunked_resampling_gives_the_unchunked_decisions` (tests/test_vad.py:110-124) cannot fail on the bug class its own comment names. The tiled fixture is continuous speech: after dilation the chunked mask has 0 False frames of 1350, so no window shift can change it. Probed: with `skip` doubled (800 samples dropped per chunk) the test's signal gives 0 differing frames; with the tail removed entirely, 0. The skeptic's N1 signal (3 s speech plus 1 s of zeros, tiled seven times, 28 s at 44.1 kHz) gives 218 False frames, 0 differing with the shipped code and 33 with `skip` doubled. Commit `1afd451` ("Make the resampler test able to fail") wrote "pauses at the joins" into the plan without running it; the implementer followed it verbatim. Finding C1.
  - `test_the_bundled_model_is_the_known_file` and every `SileroDetector` test read `model_path()`, which honours `CUMPLE_SILERO_MODEL`; a developer with that variable set gets a failure or tests a different file. `monkeypatch.delenv("CUMPLE_SILERO_MODEL", raising=False)` in a fixture fixes it (M5). CI is unaffected.
  - The sub-window test asserts `fraction is None` and one mask frame on 25 ms; it can fail and does test the early return. It does not cover the 32 ms to 1.28 s band where the backends diverge (M2).
- The README pin (`test_site_numbers.py:104-111`) parses the leading float of the reference and Silero cells, takes `abs`, formats to one decimal. Simulated: README with 9.3 in place of 9.2 fails; the report at -28.1 (needing 9.3) fails against the current README. Each key appears exactly once in README. The assertion checks presence anywhere, not association with the film (the heuristic pin has the same shape); acceptable.
- Nothing in `tests/test_vad.py` touches `~/.cache/cumple` or the network: the model is read from the package, the fixture from the repo, and the session cache is in-process. `needs_onnx` gates the nine tests that need the runtime; the dev group installs it on all three runners.
- The dilation spy test proves the heuristic's `result()` goes through `dilate_mask` once. The heuristic's own tests are untouched and were green in every task run.
- Count pins: 252 collected at head, README 252 and 223 on Ubuntu, CONTRIBUTING, QA, AI_USAGE and the page all 252.

## Packaging

- Wheel (rebuilt here): `cumple/models/SILERO_LICENSE`, `cumple/models/__init__.py`, `cumple/models/silero_vad.onnx` present; wheel 2,330,597 bytes, of which the model is 2,327,524.
- `packaging/cumple.spec`: `"onnxruntime"` in `excludes`; `datas = collect_data_files("cumple")` will carry the 2.3 MB model and the licence into every frozen app (the frame accepts this; the apps are about 150 MB, so it is 1.5 %).
- `release.yml:57` runs `uv sync --extra app --group packaging --no-default-groups`, so the `macos-15-intel` job never asks for onnxruntime; `uv.lock` lists onnxruntime 1.30.0 wheels for macOS arm64, manylinux x86_64 and aarch64, win_amd64 and win_arm64, and none for macOS x86_64. The tests workflow's three runners (ubuntu-latest, macos-15 arm64, windows-latest) all have a wheel.
- Assumption to note, not verified: `uv tool install "cumple[vad] ..."` on an Intel Mac depends on whether some `onnxruntime>=1.17` release still has a macOS x86_64 wheel; the README does not mention the platform limit.

## Production readiness

- Heuristic and WAV users: the measurement path is unchanged (`dilate_mask` is the heuristic's block moved verbatim; `pick_channel` is a rename; `_run` builds the same `SpeechDetector`). Two report strings changed for them, both through `describe_backend`: the speech-share INFO note was "heuristic speech detector, an approximation of Dolby Dialogue Intelligence" and is now "heuristic speech gate, an approximation of Dolby Dialogue Intelligence"; the sheet footer was "Dialogue-gated rules use a heuristic speech detector, an approximation ..." and is now "Dialogue-gated rules use the heuristic speech gate, an approximation ...". The dialogue-gated note and the false-pass WARN already said "heuristic speech gate" and are byte-identical. No test, doc, page sentence, profile note or app UI string depends on the two old strings (`grep` over `tests/`, `docs/`, `README.md`, `site/`, `src/cumple/app/ui`); the JSON `note` field is free text and the new `speech_backend` key is additive. Acceptable.
- The desktop app (`app/api.py:371`, `selftest.py:36`), `watch.py:66` and `fix.py` call `measure()` without `vad` and do not read `CUMPLE_VAD`, so they keep the heuristic, as the README says.
- Base install: no new dependency; one 2.3 MB file. `import cumple.meters.vad` happens only inside `_run` when `vad == "silero"`, so a base install never imports onnxruntime.

## Findings

### Critical

C1. tests/test_vad.py:110-124, `test_chunked_resampling_gives_the_unchunked_decisions`. Why: it is the one test guarding the resampler's tail and skip, and it passes with the skip doubled and with no tail at all (probed), because the tiled fixture leaves 0 False frames after dilation; its comment ("a doubled or dropped tail shifts the windows and dozens of frames differ") is false for its signal. A test that cannot fail is this run's Critical by the calibration. What to do: build the signal as `np.tile(np.concatenate([x16[:, 0], np.zeros(16000)]), 7)` before resampling to 44.1 kHz (28 s, 218 False frames), assert `len(chunked) == len(whole) == int(28 / FRAME_S)`, keep `<= 2`; fix the two comments. Verified here: shipped code 0 differing frames, doubled skip 33.

C2. README.md:434-435. Why: "Three reports are headed cumple 0.2.0 and the benchmark 0.2.1: all were generated on 8 September 2026" is false at head on the count (two are 0.2.0: CONFORMANCE, PERF) and the date (BENCHMARK 12 September, already at base; DIALOGUE 13 September, this branch). What to do: "CONFORMANCE.md and PERF.md are headed cumple 0.2.0 (8 September 2026); BENCHMARK.md (12 September) and DIALOGUE.md (13 September) are headed 0.2.1; 0.2.1 changed no measurement code."

### Important

I1. scripts/dialogue_benchmark.py:16-20 (module docstring). Why: it still describes Silero as "an independent design" that "needs `onnxruntime` (run with `uv run --with onnxruntime ...`)" and "the 2.3 MB model that scripts/fetch_real_dialogue.sh places in ~/.cache/cumple/"; all three are false since Task 3, and the docstring is the first thing a contributor reads. What to do: say it runs `cumple.meters.vad.SileroDetector`, the detector behind `check --vad silero`, on the bundled model, and that the dev group carries onnxruntime.

I2. scripts/fetch_real_dialogue.sh:13 and 52-54. Why: the comment labels the model "Silero VAD v5" (the version the skeptic's Critical 1 corrected everywhere else), the `get` downloads `master`'s model into `~/.cache/cumple/silero_vad.onnx` which nothing reads any more, and the instruction says `uv run --with onnxruntime`. A false version string in a committed script the README tells users to run before the benchmark. What to do: delete lines 52 to 54 and the line 13 credit (the licence now lives beside the bundled model); if a copy in the cache is wanted for `CUMPLE_SILERO_MODEL` experiments, pin the URL to tag `v6.2.1` and say so.

I3. AI_USAGE.md:147-148 against 269-283. Why: the file calls itself the honest record and now says both "more precise on both films" and "worse on quiet dialogue under music" about the same two films with no link between the two entries. What to do: one sentence at the end of the new section, e.g. "The 5 September entry above called Silero more precise on both films; that was true of which frames it calls speech and not of the gated number, which was already further under the reference on Sintel than the heuristic's, so this section supersedes it." Leave line 147 as written.

### Minor

M1. README.md:448-449, "comes within 1.2 LU of the reference on Tears of Steel". Why: the table prints Silero to one decimal and no delta column, so the true delta is in 1.17 to 1.27 LU and "within" is a bound the report cannot support; the heuristic's sentence uses the honest form. What to do: "reads 1.2 LU low on Tears of Steel" (the pin test still passes); can wait: a `Silero delta` column at two decimals in the generator, and the pin reading it.

M2. src/cumple/meters/vad.py:122-140. Why: between one window (32 ms) and `MIN_FRAMES` (1.28 s) Silero returns a number where the heuristic returns `None`, so the engine picks a different loudness rule per backend on the same short file and prints "too short for the speech detector (it needs 1.3 s)" for one backend only. The frame's "the engine cannot tell them apart except by name" does not hold there. What to do: `if n20 < MIN_FRAMES: return SpeechResult(..., None, backend="silero")` beside the existing early return, and extend the sub-window test to a 1 s signal.

M3. src/cumple/cli.py:307. Why: `CUMPLE_VAD=""` exits 2 with "unknown speech detector ''" instead of falling back to the default (probed). What to do: `vad or os.environ.get("CUMPLE_VAD") or "heuristic"`.

M4. src/cumple/meters/measure.py:259. Why: the name is validated after `probe()` and `load_package`; moving `describe_backend(vad)` to the top of `measure()` reports a bad name before any file work and once for both paths.

M5. tests/test_vad.py:56-63 and the `SileroDetector` tests. Why: `model_path()` honours `CUMPLE_SILERO_MODEL`, so a developer's environment can redirect the hash test and the detector tests. What to do: an autouse fixture in `test_vad.py` that `delenv`s it.

M6. README.md:419, "with Silero VAD as a second opinion". Why: since this branch it is a second backend measured beside the heuristic, not an opinion in a script. What to do: "with Silero VAD, the `--vad silero` backend, beside it".

M7. AI_USAGE.md:279, "Silero is more precise on clean speech". Why: on the eight clean-speech rows both read 86 to 100 %; where Silero is clearly better is the seven no-dialogue rows (0 % against 1 to 92 %). What to do: "reads 0 % on music and effects where the heuristic reads up to 92 %, and is worse on quiet dialogue under music" (can be folded into the I3 sentence).

M8. src/cumple/checks/engine.py:217, the comment "The heuristic gate reads low on dense mixes" beside logic that now serves both backends and a WARN that names either. What to do: "The speech gate (either backend) reads low ...".

M9. src/cumple/models/SILERO_LICENSE has no trailing newline. Cosmetic.

M10. README.md:117-121 does not say Silero needs a platform onnxruntime supports (no macOS x86_64 wheel for 1.30). Assumption, see Packaging; one clause if confirmed.

## Ledger triage

Must fix before merge:

- Task 3 Important, the benchmark script's module docstring (I1): three false sentences at the top of the script that generates a published report.
- Task 3 minor, AI_USAGE.md:147 superseded (I3): the honest record contradicts itself on the branch's headline number.
- Task 3 minor, README:434 "Three reports are headed cumple 0.2.0" (C2): a false published sentence, and this branch moved the fact it describes.
- New, C1: the resampler test cannot fail; the fix is the skeptic's verified signal.
- New, I2: `fetch_real_dialogue.sh` says "v5" and fetches a model nothing reads.

Can wait:

- Task 1 minor, the chunk end resampled against zero padding: 0.6 ms per 10 s at every rate probed, 0 decisions flipped at four rates; a correct fix (resample the tail region again with the next chunk and splice) costs more than it returns.
- Task 1 minor, `model_path` assumes an on-disk package: wheels and the frozen apps are on disk; zipimport is not a supported install.
- Task 1 minor, `SILERO_LICENSE` trailing newline (M9): cosmetic.
- Task 2 minor, `--vad` validated only through the broad `except` (part of M3, M4): the message names the choices and the exit code is 2; a typer enum would still need the env path validated the same way.
- Task 2 minor, engine.py:217 comment (M8): a comment, and the WARN it sits beside already names the backend.
- M1, M2, M5, M6, M7, M10: wording and parity; none makes a published number false. M1 is one word and could ride in the wave since README is being edited anyway.

## Verdict

**Ship with changes.** The design is right and the numerical core holds under the probes (four sample rates, chunked against one pass, short inputs, the centre pick); every report surface names the backend through one function; the model, its licence and the fixture are what they claim to be; heuristic users see two reworded strings and no changed number. What blocks are five checkable-text items, each a few lines: a test that cannot fail on the path it names (C1), a README sentence that is false at head (C2), a stale docstring (I1), a script that still says "v5" and fetches a file nothing reads (I2), and a self-contradiction in the honest record (I3).

Counts: Critical 2, Important 3, Minor 10.
