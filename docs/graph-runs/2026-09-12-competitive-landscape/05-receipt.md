2026-09-12 | competitive-landscape | Diamond | Ship with changes | r128gain "no read-only flag" was false, and so was the roadmap's own ADM profile count | new landing-page columns for the three open-source wrappers

# 05 Receipt: competitive landscape

## Decision

Victor's, pending at the moment of this receipt: confirm the two build items the recommendation ranks first (R1, a Silero VAD dialogue-gate backend behind `cumple[vad]`; R2, delivery codec and container conformance through an optional local ffmpeg), or swap in ADM/Atmos (R4) or 2-pop (R6), which the frame expected and the evidence ranked lower; and choose between restoring the machine's ffmpeg 8.0 or accepting 9.0.1 and re-pinning the benchmark. The merge of this PR was delegated on 12 September after green checks and a clean fresh review.

## What shipped

Pull request #26, https://github.com/victor10days/cumple/pull/26, branch `loop/01-research`: `docs/RELATED.md` with three new tables (6 open-source rows, 12 commercial, 9 QC platforms) and a "Where cumple sits" section; the "Dolby DPLM" sentence replaced in RELATED.md, README.md and the page's note; `docs/ROADMAP.md` (new) with eight ranked items and the loop contract; `tests/test_related.py` (new, five tests); AI_USAGE.md section; counts re-pinned at 200 (171 in CI). The page's comparison table is unchanged.

## Rejected options

- Landing-page columns for ffmpeg-normalize, r128gain or rsgain: each re-measures an engine already in the table (loudnorm, ffmpeg's ebur128 filter, libebur128 1.2.6). What would change it: bs1770gain or loudness-scanner running here, or a CLI meter with its own BS.1770 code.
- Keeping "Nugen VisLM and Dolby's DPLM are the commercial meters the studios name": no live Dolby product by that name was found; the profiles name an algorithm and one QC vendor prints "DPLM" as a check without defining it.
- Watermark detection, automatic repair, more presets: outside a read-only QC tool, or a strength already.

## Findings that changed the outcome

- Skeptic pass 1, Critical: r128gain's row said "no read-only flag"; upstream has `-d, --dry-run`. Re-run with shasum proof; both readings in tolerance.
- Skeptic pass 1, Critical: the ranking counts in 02b and 02c did not trace to their cells (presets "10 of 12" against a column with six "n/s"; Dolby E fused with Atmos/ADM; Vidchecker credited with A/V duration its specs page never mentions). Recomputed from cells; Atmos/ADM came out 2 of 9 and 0 of 12, which is what moved it below the dialogue gate and codec conformance.
- Skeptic re-check, Critical: the rewrite's "r128gain engine is independent" was false (it measures through ffmpeg's ebur128 filter). Fixed in two sentences; the page-column verdict became "none".
- Deliverable review, Critical: the roadmap's R4 cell, written in the main session, said four profiles accept `adm-bwf`; three do (netflix-5.1 lists wav, bwf, rf64). Fixed. The main session wrote a checkable number without running the check; the boundary "no claim without a source or a run" applies to the ledger too.
- Deliverable review, High: Venera Pulsar was named as a home of Dolby Dialogue Intelligence on the strength of "Speech Gated"; the cell never says Dolby. Fixed.
- Skeptic re-check, High: `brew install rsgain` upgraded the shared ffmpeg 8.0 to 9.0.1 and the 8.0 keg cannot load its libvpx. Recorded in AI_USAGE and ROADMAP; Victor's decision; "no Homebrew install that upgrades a pinned tool" added to the loop's boundaries.

## Rulings

- Branch files may run to 900 words when the table is the deliverable (the skill's template says 600).
- One skeptic fix round means: the branches are corrected once against the skeptic's list, the same skeptic re-checks the changed cells, and residues small enough for two sentences are fixed in the same round.
- A separate reviewer reads the deliverable diff before the PR, in addition to the skeptic who read the research; the two found different errors.
- The receipt is committed after the PR opens so it can carry the PR link; CI runs on the head with the receipt in it.

## The box that earned its place

The skeptic. Two false claims in the research and one in the main session's own ledger were each caught by a context that had no history with the writing; nothing found them from inside.
