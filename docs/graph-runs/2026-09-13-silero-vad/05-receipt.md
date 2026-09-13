2026-09-13 | silero-vad | Chain | Ship with changes (twice) | the bundled model is Silero VAD v6.2, not the v5 every draft named; and a resampler test that could not fail | pip install as the route; measuring the first stream of nothing (n/a); a third backend

# 05 Receipt: Silero VAD as an optional dialogue-gate backend

## Decision

Victor confirmed R1 on 12 September as one of the loop's two build items. The merge of this PR was delegated the same day, after green checks and a clean fresh review. With this PR the loop's budget (research plus two builds) is spent; the next item is his to name.

## What shipped

Pull request #28, https://github.com/victor10days/cumple/pull/28, branch `loop/03-silero-vad`: `src/cumple/meters/vad.py` (new), the shared `dilate_mask` and `describe_backend` in `dialogue.py`, the bundled model and licence, the `vad` extra and dev dependency, `measure(vad=)`, `check --vad` and `CUMPLE_VAD`, the backend named on every report surface, the benchmark script on the shipped detector, `docs/DIALOGUE.md` regenerated with both backends, the LibriVox fixture, docs, 252 tests (223 in CI). Roadmap R1 merged.

## Rejected options

- `pip install "cumple[vad]"` as the documented route: cumple is not on PyPI (roadmap R8); the route is `uv tool install` from git with the extra.
- A sub-window file reporting 0 % speech from Silero: it reports unknown, as the heuristic does for files it cannot judge.
- Hiding the difference between the backends on files between 32 ms and 1.28 s: recorded in ROADMAP as a known difference instead.
- Bundling onnxruntime into the frozen apps: excluded this iteration; the model rides along as package data.

## Findings that changed the outcome

- Plan skeptic, Critical: the bundled model is Silero VAD v6.2 (upstream tags v6.2 and v6.2.1 carry its hash; v5.1.2 is a different file). Every "v5" in the frame, the plan and the strings would have been a false version on every report surface.
- Plan skeptic, Critical: the dilate test asserted silence the rule does not give; the CLI's rich markup would have eaten "[vad]" from the install hint; the block-size test could not fail (both detectors shared the chunk boundaries). Fixed in the plan; the resampler test became a chunked-versus-unchunked comparison.
- Plan skeptic, High: `pip install` is not an install route for this package.
- Task 1 review: a sub-window file reported 0 % instead of unknown; a session per detector. Both carried into Task 2.
- Task 3 review, Important: the benchmark script's docstring still described the old flow the task replaced.
- Whole-branch review, Critical: the chunked test still could not fail because the tiled fixture had no pauses (every frame speech after dilation); rebuilt with 1 s of silence per repeat and proven by mutation (doubled skip: 33 frames differ; a never-carried tail is a documented blind spot). And README's "three reports headed 0.2.0, all 8 September" was false at head.
- The measurement itself: with the shipped detector Silero reads 1.2 LU low on Tears of Steel and 9.2 LU low on Sintel (the script's earlier inference over 16 kHz intermediates said 1.3 and 9.3); worse than the heuristic's 6.7 on Sintel, and 0 % on music and effects where the heuristic reads up to 92 %. The README says both.

## Rulings

- The model version is stated as v6.2 on the strength of a tag-by-tag hash check recorded in 03-skeptic.md; the ONNX carries no version string.
- `describe_backend` returns a short inline name ("Silero VAD v6.2 gate"); licence and the words "neural speech detector" live in the README and the module docstring.
- Task 1's minors on the session cache and the sub-window fraction were carried into Task 2; Task 3's stale docstring and two doc residues into the final wave.
- M2 (Silero reports a share on files between 32 ms and 1.28 s where the heuristic reports unknown) is accepted and recorded, not changed.
- Deferred to after this PR: the resampler's chunk end computed against zero padding (0.6 ms); `model_path` assuming an on-disk package; `--vad` validated only through the ValueError path; the engine comment wording; a `Silero delta` column in the report so README's "low" can be a bound.

## The box that earned its place

The plan skeptic again: a false model version on every surface, a test that could not fail, and an install route that does not exist, all caught before code; then the whole-branch reviewer caught that the rebuilt test still could not fail.
