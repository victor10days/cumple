# 03 Skeptic: the Silero VAD plan

Date: 2026-09-13. Reviewed: `docs/superpowers/plans/2026-09-13-silero-vad.md` against `01-frame.md`, the code it modifies, the model file and the fixture candidate. Read-only; nothing in the worktree was changed (`git status` clean at the end; the wheel was built into the scratchpad).

## Inputs read

- `docs/graph-runs/2026-09-13-silero-vad/01-frame.md`
- `docs/superpowers/plans/2026-09-13-silero-vad.md`
- `docs/graph-runs/2026-09-12-competitive-landscape/05-receipt.md`, `docs/graph-runs/2026-09-12-ffmpeg-codec-conformance/05-receipt.md`
- `src/cumple/meters/dialogue.py`, `src/cumple/meters/measure.py`, `src/cumple/meters/bs1770.py` (dialogue_gated), `src/cumple/checks/engine.py` (95 to 245), `src/cumple/cli.py` (check, 280 to 330; app, 468 to 486), `src/cumple/report/json_out.py`, `src/cumple/report/qc_sheet.py` (render_html and the footer), `src/cumple/report/__init__.py`, `src/cumple/io/reader.py` (signatures), `scripts/dialogue_benchmark.py`, `scripts/fetch_real_dialogue.sh` (the model line), `pyproject.toml`, `.gitignore`, `packaging/cumple.spec`, `.github/workflows/tests.yml`, `.github/workflows/release.yml`, `tests/conftest.py`, `tests/test_dialogue_leqm_acx.py`, `tests/test_site_numbers.py`, `tests/test_counts.py`, `tests/test_engine.py` (the JSON test), `tests/test_app.py` (the `cumple[app]` test), `docs/DIALOGUE.md`, `README.md` (install, reports, honest limits), `CONTRIBUTING.md` (set up), `site/index.html` (the dialogue lines), `docs/ROADMAP.md` (R1)
- `~/.cache/cumple/silero_vad.onnx`; the fixture candidate `speech-librivox-3s.wav` in the scratchpad; the main session's `dialogue-benchmark-baseline.log` and `fetch-real-dialogue.log` in the scratchpad
- `~/.claude/skills/devils-advocate/SKILL.md` and its three references

## Steelman

The plan is the smallest shape that meets the frame: one new module whose detector has the heuristic's `feed` and `result`, composes a `SpeechDetector` for the levels and the frame count, and returns a `SpeechResult` on the same 20 ms grid dilated by the same rule, so `measure`, the meter and the engine see one interface and the only thing that changes is the mask. Bundling a 2.3 MB MIT model as package data with onnxruntime behind an extra keeps the base install untouched, and routing every report string through `describe_backend` and one field is the right way to keep the honesty promise from drifting across four surfaces. The chunked resampler with carried model state is the correct streaming design, the tests cover the two rates that matter and the centre-channel pick, and Task 3 removes a second copy of the inference so the benchmark measures the shipped detector. I ran the plan's `SileroDetector` verbatim against the real model: the design holds (fixture 100 % speech, white noise 0 %, centre channel 100 % against 6 % for the fold, chunked and one-shot resampling agree to 0.0004 in probability at 44.1, 48 and 96 kHz).

## Checks run (commands and what they showed)

All from `/Users/Victor/Code/cumple-wt/loop-03-vad`, scratch scripts under the session scratchpad `skeptic/`.

1. `shasum -a 256 ~/.cache/cumple/silero_vad.onnx`: `1a153a22f4509e29...`, 2,327,524 bytes. Matches the plan.
2. `curl` of `snakers4/silero-vad` at tags `v5.1.2`, `v6.0`, `v6.1`, `v6.2`, `v6.2.1` (the file `src/silero_vad/data/silero_vad.onnx`) and `shasum` of each: v5.1.2 is `2623a2953f6ff3d2`, v6.0 and v6.1 are `597d30b3ec076608`, v6.2 and v6.2.1 are `1a153a22f4509e29`. The bundled file is the v6.2 model, not v5. Latest release per the GitHub API: v6.2.1 (2026-02-24). The fetch script pulls `master`, which is that file.
3. `curl` of the upstream `LICENSE`: first line `MIT License`, then `Copyright (c) 2020-present Silero Team`. The plan's licence test and fallback text are right.
4. `uv run --with onnxruntime python skeptic/run1.py` (the plan's vad.py verbatim, importing the worktree's `dialogue.py`, `pick_channel` aliased to `_channel`): onnxruntime 1.30.0; model inputs `input [None, None]`, `state [2, None, 128]`, `sr []` int64; outputs `output`, `stateN`. Fixture at 16 kHz: fraction 1.0, 150 mask frames, 150 level frames, 93 windows, 87 % above threshold. Heuristic on the fixture: 1.0. White noise 48 kHz stereo: fraction 0.0, max probability 0.062. 44.1 kHz block-size test as written: `_resample` called once for the 1024 blocks and once for the 1<<18 blocks, 0 frames differ. Centre channel test: 1.0 with roles, 0.06 without.
5. `skeptic/run2.py` and `run3.py`: 27 s of continuous speech (the fixture tiled nine times) at 44.1, 48, 22.05 and 96 kHz, a chunked detector (3 `_resample` calls, `_tail` and `skip` exercised at 10 s and 20 s) against one with an unreachable chunk (1 call): 0 mask frames differ at every rate; max |dprob| 0.0004 at 44.1, 48 and 96 kHz, 0.031 at 22.05 kHz (the `skip` rounding of 0.3 sample). Same at native 16 kHz with 4096 and 1<<18 blocks: probabilities identical.
6. `uv run python -c` on the index mapping: `(np.arange(n) * 0.02 / 0.032).astype(int)` against `i * 5 // 8` for 2,000,000 frames: 2,359 frames floor one window low (first at frame 3208). The existing `mask_at` idiom (10 ms to 20 ms) does the same at 69,999 of 2,000,000. `int(3 / FRAME_S)` is 150; frame lengths 882 at 44.1 kHz and 441 at 22.05 kHz.
7. `uv run python` with the plan's `dilate_mask` on the plan's `test_dilate_mask...` arrays: `mask[70:75].all()` True, `mask[50:95].all()` True, `mask[150] and not mask[130:149].any()` True, `not mask[100:140].any()` **False**: frames 95 to 105 are dilated True (a 20-frame phrase carries the 0.3 density for 10 frames past its edge; frames 40 to 49 are also True before the first phrase).
8. `skeptic/run4.py`: the `speech_wav` fixture as the plan builds it (8 s, 48 kHz stereo, PCM_24) through `measure` and `evaluate(netflix-2.0)`: heuristic fraction 1.0, dialogue-gated -25.8 LKFS over 77 blocks, integrated -25.2; findings `loudness.speech` INFO, `loudness.dialogue_gated` PASS, `loudness.fallback` PASS; the notes contain "heuristic speech gate"; the sheet HTML contains "heuristic" three times (two notes, the footer). The plan's detector on the same file: fraction 1.0, 400 frames both, the same dialogue-gated value and block count through `dialogue_gated(mask_at(...))`.
9. `uv run python` with `rich.Console` printing `f"[red]cannot measure x.wav:[/] {e}"` where `e` is the plan's `VadUnavailable` message: output is `cannot measure x.wav: the silero backend needs onnxruntime: pip install "cumple" (or uv tool install "cumple")`. Rich consumes `[vad]` as a style tag. The existing `app` command escapes its own `cumple\\[app]` for this reason (cli.py 479).
10. `grep -n -i heuristic src/cumple/**/*.py`: engine.py 130, 149, 229 (the three notes the plan routes) and 215 (a comment); qc_sheet.py 217 (the footer); measure.py 51 (a field comment); dialogue.py 5 (the module docstring). Tests: `test_dialogue_leqm_acx.py:68` pins only "speech gate", which survives the rewrite.
11. `uv build -q --wheel --out-dir <scratchpad>` and `unzip -l`: the wheel carries `cumple/report/fonts/*.woff2`, `OFL-*.txt`, `app/ui/*` with the current `packages = ["src/cumple"]`, so `.onnx` and an extension-less `SILERO_LICENSE` will ride the same way; `.gitignore` ignores neither. `git status --short` empty afterwards.
12. PyPI JSON for onnxruntime 1.30.0: cp312 wheels for `macosx_14_0_arm64`, `manylinux_2_28_x86_64`, `win_amd64` (and aarch64, win_arm64); `requires_python >=3.11`. The tests workflow pins Python 3.12 on ubuntu-latest, macos-15 and windows-latest and runs `uv sync --group dev`, so the dev-group addition installs on all three. No macOS x86_64 wheel exists; the release job's `macos-15-intel` build does not sync the dev group, so it is unaffected.
13. `README.md` install section: `uv tool install --python 3.12 git+https://github.com/victor10days/cumple`; no `pip install` anywhere in README or CONTRIBUTING; the `app` command's hint uses `"cumple[app] @ git+https://github.com/victor10days/cumple"`. cumple is not installed from PyPI.
14. `docs/DIALOGUE.md` pair table: Silero-gated -28.1 on Sintel against the reference -18.8 (9.3 LU low; the heuristic is 6.7 LU low) and -14.1 on Tears of Steel against -12.8 (1.3 LU; heuristic 1.6). `tests/test_site_numbers.py::test_dialogue_gate_errors_in_the_note` reads the first two `| x.xx LU |` cells (the heuristic's delta column) and pins the page only; nothing pins README's dialogue sentences.
15. The main session's `dialogue-benchmark-baseline.log` (2026-09-13, 5:32 wall): every heuristic and Silero number reproduces the committed table with the re-fetched decodes, so Task 3's "heuristic numbers identical" expectation is supported.
16. `uv run pytest --collect-only 2>/dev/null | grep 'tests collected'`: `233 tests collected in 0.99s`, the line the plan re-pins from.
17. `packaging/cumple.spec`: `datas=collect_data_files("cumple")`, so the model rides in the frozen apps (the frame's "Open" says so); `excludes` does not name onnxruntime.

## Concerns

### 1. Every report will say "Silero VAD v5" and the bundled model is v6.2

Severity: Critical (blocking). Framework: confidence without correctness; "is this provably correct, or does it just look correct?"

What I see: the plan bundles `~/.cache/cumple/silero_vad.onnx` (sha `1a153a22f4509e29...`, plan line 9, 48, 86) and labels it "Silero VAD v5" in `BACKEND_NAMES` (plan 227), the module docstring (261), `test_describe_backend_names_both_and_refuses_others` (`startswith("Silero VAD v5")`, 104), README (600), the `models/__init__.py` docstring (49) and the frame. Check 2: that hash is the model at tags v6.2 and v6.2.1; v5.1.2 is a different file (`2623a2953f6ff3d2`). The fetch script pulls `master`, which is v6.2.1 today and something else next year.

Why it matters: the frame's whole promise on this surface is that the report says truthfully what made the mask. A version number that is wrong on every sheet, JSON and note is the exact failure the last two receipts caught ("no claim without a run"). It also means the v5 test would pass against a v6 model, so the pin does not pin.

What to do: drop the version from the label, or say the true one. Concretely: `"silero": "Silero VAD speech gate (Silero Team, MIT)"` in `BACKEND_NAMES`, with the version recorded once where it can be checked: a `SILERO_VERSION = "v6.2.1"` constant beside the hash in `vad.py` (or in `models/__init__.py`), the fetch script pinned to the tag instead of `master`, and `tests/fixtures/NOTICE.md` or the licence directory naming the tag and the sha. Update the test to `startswith("Silero VAD")` and the README and AI_USAGE prose to "Silero VAD v6.2.1" or to no version at all.

### 2. The `dilate_mask` test fails as written

Severity: Critical (blocking). Framework: boundary conditions; pre-mortem "the first implementer runs Step 3 and the test fails after Step 4 too".

What I see: plan 90 to 99. Two 20-frame phrases end at frame 94; the window is 50 frames and the density floor 0.3, so 15 voiced frames in a window keep it dialogue. Frames 95 to 105 come out True (check 7), and `assert not mask[100:140].any()` is False with the plan's own `dilate_mask` (which is the heuristic's rule verbatim, so the rule is right and the assertion is wrong).

Why it matters: the test cannot pass; an implementer under "make it green" will either widen the rule (changing the heuristic, which the frame forbids) or edit the assertion without understanding why, and the reviewer has no note saying which is intended.

What to do: assert the behaviour the rule actually has: `assert mask[95:106].all()` (a pause and a 200 ms tail after a phrase are still dialogue) and `assert not mask[110:140].any()`. Keep the isolated-frame assertion.

### 3. Rich markup eats `[vad]`: the CLI test cannot pass and the user is told to `pip install "cumple"`

Severity: Critical (blocking). Framework: inversion; "what error does the user see, is it actionable?"

What I see: plan 524 says the existing `except Exception` branch is enough. It is `console.print(f"[red]cannot measure {path}:[/] {e}")` (cli.py 305) on a Console with rich markup on. Check 9: rich treats `[vad]` as a style tag and drops it, so the output reads `pip install "cumple" (or uv tool install "cumple")`, and `test_check_without_onnxruntime_exits_two_and_names_the_extra` (plan 474 to 483, `"cumple[vad]" in result.output`) fails. The same happens to the `--vad` help string (plan 520, `needs cumple[vad]`) under `rich_markup_mode="rich"`. The `app` command already works around this by writing `cumple\\[app]` (cli.py 479).

Why it matters: the one message the frame specifies ("fails with a message naming `pip install "cumple[vad]"`") would ship without the extra's name, which is the part the user needs.

What to do: in `check`, `from rich.markup import escape` and print `escape(str(e))` (the other `cannot ...` prints in cli.py have the same latent bug; fixing them all is a two-line change, but at least this one). In the option help write `cumple\\[vad]`. Add to the test an assertion on `--help` output containing `cumple[vad]` so both stay fixed.

### 4. The block-size test cannot fail and does not touch the code it is there for

Severity: Critical by this run's scale (a test that cannot fail), non-blocking in effect because the code under it checks out. Framework: pre-mortem "which test would have caught a broken `_tail`?"

What I see: plan 168 to 178 and the note at 385 ("the 44.1 kHz test drives the `_tail` path"). The fixture is 3 s and `CHUNK_S` is 10 s, so `feed` never enters the `while` and `result()` resamples everything in one call for both block sizes (check 4: one `_resample` call each, `_tail` never non-empty). More fundamentally, chunk boundaries fall at multiples of `_chunk` whatever the block size is, so no block size can ever change the resampled stream; the test is true by construction for any implementation of `_resample`, including a broken one.

Why it matters: the resampler's overlap and `skip` rounding are the one piece of numerical code in the plan, and the suite would say nothing if they were wrong. (I drove them myself, check 5: 0 differing frames at four rates, so the plan's code is sound; the test just does not know that.)

What to do: test chunked against unchunked. Give `SileroDetector` a keyword `chunk_s: float = CHUNK_S` (or monkeypatch `vad.CHUNK_S` before construction), tile the fixture to 12 s at 44.1 kHz, run one detector with `chunk_s=1.0` and one with `chunk_s=60.0`, and assert `np.array_equal(small.mask, large.mask)` plus a tight bound on the probabilities if they are exposed. Rename the test to say what it checks ("chunked resampling matches one pass").

### 5. `pip install "cumple[vad]"` is not a way to install cumple

Severity: High (blocking; a two-line fix). Framework: Socratic, "you are assuming cumple is on PyPI".

What I see: plan 305 (`VadUnavailable` message), 520 (help), 601 (README paragraph), and the frame line 12. Check 13: cumple installs from git (`uv tool install --python 3.12 git+https://github.com/victor10days/cumple`); README and CONTRIBUTING never say `pip install`, and the `app` command's hint uses `"cumple[app] @ git+https://github.com/victor10days/cumple"`.

Why it matters: a user following the message would install whatever package is named `cumple` on PyPI, or nothing. The frame carries the same wording, so the plan inherited it rather than checking it; the receipts have twice flagged exactly this class ("a checkable claim written without running the check").

What to do: use the project's own pattern in all three places: `uv tool install --python 3.12 "cumple[vad] @ git+https://github.com/victor10days/cumple"` (and for a clone, `uv sync --extra vad`). Keep the tests' `"cumple[vad]" in ...` assertions; they still hold. Record in the receipt that the frame's wording was corrected.

### 6. "No better on quiet dialogue" undersells a worse number, and nothing pins README's Silero sentence

Severity: Medium (non-blocking). Framework: inversion on the honesty promise.

What I see: check 14: Silero's dialogue-gated value on Sintel is 9.3 LU low against the heuristic's 6.7; the AI_USAGE draft (plan 626 to 627) says Silero is "no better on quiet dialogue under music", and the README bullet it replaces said the same. The plan's README sentence rightly uses the numbers, but the frame (line 24) says README's dialogue numbers are derived by tests; `test_site_numbers.py` pins the page only (check 14), so the new README sentence with X and Y is a hand-typed number pair again.

Why it matters: the heuristic's numbers were kept honest by a test; Silero's would not be, and "no better" will read as "about the same" to a mix engineer choosing a flag.

What to do: write "worse on Sintel (9.3 LU low against the heuristic's 6.7)" in AI_USAGE and README; extend `test_dialogue_gate_errors_in_the_note` (the one test the loop's boundary lets grow) to compute the Silero deltas from the `Silero-gated` and reference cells and assert both README sentences carry them at one decimal.

### 7. The 32 ms to 20 ms mapping floors one window low on 0.1 % of frames, and a handful of hygiene items

Severity: Medium (non-blocking). Framework: boundary conditions.

What I see: plan 377, `(np.arange(n20) * FRAME_S / (WINDOW / VAD_FS)).astype(int)`; check 6: 2,359 of 2,000,000 frames take the previous window's decision (whenever `i * 5 / 8` is an exact integer the float lands just under it). After 1 s dilation this changes nothing visible, and `mask_at` has the same idiom, so this is a tidy-up, not a defect. In the same bucket: the comment "memory stays a few hundred kB per detector" (plan 284) is off by an order (10 s of float64 at 48 kHz is 3.8 MB plus one 262,144-frame block); backend names live in three places (`BACKENDS` in vad.py, `BACKEND_NAMES` in dialogue.py, the `if/elif` and its message in `_run`); `packaging/cumple.spec` should add `onnxruntime` to `excludes` now that the dev venv carries it, or a local build silently bundles it (the release job uses `--no-default-groups`, so CI is safe); `CUMPLE_VAD` is honoured by `check` only, `watch` and the app keep the heuristic, which the README paragraph should say; `silero_available()` in the benchmark loads a session per call and each `SileroDetector` loads another, so pass one `session=` through; `tests/fixtures/NOTICE.md` should say "public domain in the United States" (LibriVox's own terms; Crompton died in 1969).

What to do: `idx = np.minimum(np.arange(n20) * round(FRAME_S * VAD_FS) // WINDOW, len(probs) - 1)` (exact integers, 320 and 512). `BACKENDS = tuple(BACKEND_NAMES)` and have `_run` call `describe_backend(vad)` once to validate before dispatching. Fix the comment, the spec's `excludes`, the README sentence about scope, the session reuse, and the NOTICE wording.

## Contradictions

- Plan 385 says "the 44.1 kHz test drives the `_tail` path"; with a 3 s fixture and a 10 s chunk it does not (check 4).
- Plan 227 and 104 say v5; the file is the v6.2 model (check 2).
- Plan 524 says the `except` branch already prints the exception correctly; through rich markup it prints `cumple` without `[vad]` (check 9).
- Plan 284 says a few hundred kB; the chunk buffer alone is 3.8 MB at 48 kHz.
- Frame line 24 says README's dialogue numbers are test-derived; only the page's are (check 14).
- Plan 18 says no report string names a backend on its own, and then Task 2 hard-codes "heuristic or silero" in `_run`'s error and keeps `BACKENDS` apart from `BACKEND_NAMES`. Error strings are not report strings, so this is a hygiene note, not a violation.
- The AI_USAGE draft says "no better"; the table says 9.3 LU low against 6.7.

## Unsupported claims

- "Silero VAD v5" (false; see 1).
- `pip install "cumple[vad]"` as an install route (no PyPI package is offered; see 5).
- "The Silero columns may move by rounding at most" (plan 592): the old script ran the model on ffmpeg's `-ac 1` fold of the source, resampled by ffmpeg and quantised to 16-bit; the detector runs on the centre channel when roles has one (Sintel 5.1 master: C alone instead of a 5.1 fold) and on scipy's polyphase resample of the float mean fold otherwise. The stereo rows will move by threshold flips at most; the 5.1 row changes meaning and may move by more. That is the better measurement, so nothing to fix, but the plan should say the 5.1 row is expected to move and why, so the implementer does not stop on it.
- Plan 21: "none in this plan is gated on ffmpeg", true; the 18 new tests are gated on onnxruntime, which the dev group installs on all three runners (check 12), so README's "19 fewer on macOS, 20 fewer on Windows" holds.
- "The previous run took under ten minutes": the baseline log says 5:32 wall; the refactor adds a second pass of the heuristic's levels per file inside `SileroDetector` and a native-rate resample, so expect a few minutes more, still inside the cap.

## Verdict

**Ship with changes.** The architecture and the numerical core are right; I ran the plan's detector against the real model and could not make the resampler or the grid mapping disagree with a one-pass reference. What is wrong is checkable text: the model's version on every report surface, one assertion in the dilation test, a rich markup escape the `app` command already knows about, an install command that does not exist for this project, and a test that cannot fail on the path it names. Each is a few lines; none changes the design. Fix 1 to 5 in the plan before the first implementer runs; 6 and 7 can ride in the tasks or the fix wave.

Counts: Critical 4 (concerns 1 to 4), High 1 (concern 5), Medium 2 (concerns 6 and 7). Blocking: 1, 2, 3, 5. Concern 4 is Critical by the run's scale and non-blocking in effect because the code under it is verified; it should still be fixed before merge so the suite guards the resampler.
