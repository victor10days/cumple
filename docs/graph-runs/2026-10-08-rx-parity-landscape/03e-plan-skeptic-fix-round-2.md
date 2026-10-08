# 03e Skeptic: the second fix round on the build-1 plan

Date: 2026-10-08.

Reviewed: diff 4a1705c..269008d, against 03d, cathar at f2c2842 (`gh api`), numpy re-expressions of cathar's detector, `inpaint_gap` and `declip_spade` in float32 and float64, and a scratch Cargo mirror (pyo3 0.29.3, numpy crate 0.29.0). The worktree was left unchanged apart from this file.

## Steelman

The fix round took every 03d finding at face value and mostly landed it: the rename compiles, the refill bound and the click preset now match measurement, locality is scored against the module's own gaps, the edge rule matches `inpaint.rs`, and CI can no longer go green on a skip. What remains sits in the two tolerance rules, where the new wording does something other than what it says.

## 03d concerns after the fix round

| 03d item | Status | Checked at |
|---|---|---|
| C1 crate name (E0659) | answered: mirror compiles, clippy clean | plan 285; spec 64 |
| C1 refill bound | answered: 6.39e-3 under 1e-2 | plan 412 |
| C2 IMPULSE at threshold 5 | answered; side effect M2 | plan 52, 98 to 106, 133 to 135; spec 92 to 95 |
| C3 De-click tolerance | partly answered: drift handled one way only (H1) | plan 385 to 391; spec 115 to 118 |
| C3 De-clip tolerance | not answered in substance (H2) | plan 443 to 447; spec 119 to 120 |
| C3 Task 4 (b) at seven levels | answered | plan 441 |
| C4 rule 3 against LSB detections | answered | plan 360 to 362, 506 to 508; spec 52, 126 |
| C5 file-edge AR | answered | plan 334, 409 to 416; spec 56 |
| C6 silent CI skip | answered; YAML slip M3 | plan 28 to 29, 311 to 315; spec 129 |
| C7 rebuild rule | answered | plan 26, 302 to 307; spec 74 |
| Window i - 32 to i + 31 | answered | plan 133 |
| Task 3 count | answered at plan 424; new count error at plan 35 (M1) | plan 35, 424 |
| Spec "measured in 03c" | answered | spec 92, 95 |
| Rule 3 heading against body | answered | spec 125 to 126 |
| "past the slice" | answered | plan 409 |
| `user_dir()` folder | answered | plan 472, 477; spec 79 |
| No "Default" preset file | answered | plan 208 to 209; spec 104 |
| 0.03 dB at 262,144 | answered | spec 60, 124; plan 452 |
| ΔSDR(clipped) a second check | answered: same ratio when unclipped samples match | spec 121 |
| "stays under both bounds" | partly answered: replacement is one-sided (H1) | spec 117 |
| "about two minutes uncached" | answered | plan 201, 317; spec 145 |

## New concerns

### H1. The De-click fidelity test fails a correct port where cathar's f32 RMS hides a click (High, blocking before Task 3)

Framework: inversion (drift has two signs).

What I see: plan 387 asserts every port gap is a cathar gap; only cathar-only gaps count as drift (388 to 389). cathar's f32 running sum reads up to 6.9 times high in the fixture's pause with no clicks at all, and with clicks it errs both ways. Where it reads high, cathar misses an injected click the f64 port finds. My float32 `local_rms` matches a scalar float32 loop bit for bit, so the gap decisions are exact. Over 200 click layouts per shape, the test fails 24 times (sin(pi(k + 0.5)/w)) and 33 times (sin(pi(k + 1)/(w + 1))), every failure on that assertion. Example: a width-3 click at |y| 6.8e-4 has ratio 6.33 in f64 and 4.64 in cathar. The cathar-only side holds: worst |y| inside drift 9.16e-4, ΔSDR gap at most 0.048 dB.

Why it matters: whether seed 3 passes depends on how `add_clicks` draws (about one layout in seven fails), and rule 1 gates every harness file. The failure reads as a port bug and invites a "fix" or a new seed.

What to do: in the test and the harness, compute cathar's detection mask exactly in numpy (a float32 cumsum of the interleaved running-sum terms, restore.rs 171 to 194) and treat every gap where the f32 and f64 decisions differ, in either direction, as drift. Apply the subset check and 1e-3 to the rest.

### H2. The per-file De-clip tolerance is vacuous on one reading and the flat 0.1 dB on the other (High, blocking before Task 4; Victor's rule)

Framework: Socratic (what does each run change?).

What I see: spec 119 and plan 443 name four runs, "as given, rounded to float32, scaled by 1 ± 2^-50", and never say what happens to the threshold.
- Every harness file is float32-exact (the fixture is PCM_16, the threshold is stored as float32), so "rounded to float32" equals "as given" at all seven levels. It does not reproduce cathar's arithmetic: `declip_spade` runs `FftPlanner::<f32>` throughout.
- Threshold kept: at 1 - 2^-50 every clipped sample falls under it, the early return fires, and ΔSDR is 0 at all seven levels. The window becomes [-D, 2D]; periodic Hann, RELAX_BY 1 and RELAX_BY 3 mutants all pass at 5 and 20 dB.
- Threshold scaled with the file: the spread is under 5e-14 dB at all seven levels, so the window is D ± 0.1 dB, which is 03d's flat rule. 03d's "a 2^-50 nudge moves ΔSDR by up to 0.24 dB" did not reproduce.
- My float32 re-expression sits 0.00 to 0.03 dB from f64, 03d's 0.01 to 0.44: the real gap depends on FFT rounding, which no run in the rule measures.

Why it matters: Task 4 (b) either cannot fail or fails exactly where 03d said a flat 0.1 dB would.

What to do: say the threshold scales with the file; replace the float32-input run with the port computed in f32 (make `declip.rs` generic over the float type and add its f32 instantiation to the spread), or gate only files of 15 s or more, as 03d offered. Re-run Task 4 Step 3's mutation against the final rule.

### M1. Counts and cross-references the fix round made stale (Medium, non-blocking)

Framework: consistency check.

What I see: plan 35 says Task 4 adds one cathar-gated test and the macOS and Windows figures end at 23 and 24. Plan 441 now parametrises (b) over seven levels, which collects as seven items, so the figures end at 29 and 30. Plan 460 still says "one cathar-gated and three core-gated" after (c) gained the tiled cases. Spec 124 ("only references longer than one block are chunked") leaves the new `fixture` row (48,000 samples) without a chunking figure, while plan 524 asserts that column "on every row".

Why it matters: the 03b-6 and 03c-11 count error, a third time.

What to do: correct plan 35 and 460 or drop the figures; let plan 524 accept "not run" on rows shorter than a block.

### M2. Gain 32 puts 40 % of the fixture's clicks above full scale (Medium, non-blocking)

Framework: environment gaps.

What I see: a click peaks at 32 times the local RMS. On the fixture 801 of 2,000 clicks exceed 1.0 (median peak 0.77, max 4.34); louder material raises the share (an estimate, SQAM not measured). Plan 194 never names the damaged files' subtype, and soundfile writes 2.0 to PCM_16 as 0.99997.

Why it matters: a PCM damaged file changes the clicks the harness scores, and Task 6's in-memory re-run of the `fixture` row (the 0.05 dB pin) would not match it.

What to do: write every damaged file as 32-bit float and say so, or cap the click peak below full scale and re-check visibility.

### M3. The cathar version step is invalid YAML as written (Medium, non-blocking)

Framework: run the line.

What I see: plan 314, `run: "$HOME/.cargo/bin/cathar" --version`, raises a PyYAML ParserError (text after a closing quote). Plan 315's variables must also live in a Linux-only step: the current Test step serves all three runners, and pwsh on Windows rejects `VAR=value` prefixes.

Why it matters: tests.yml fails to load at the first push.

What to do: `run: '"$HOME/.cargo/bin/cathar" --version'` or a block scalar, and a Linux-only pytest step.

## Verified

| Claim | Source | Result |
|---|---|---|
| cathar's window is i - 31 to i + 32 | restore.rs 171 to 194, traced | confirmed |
| A lone LSB in zeros has ratio exactly 8 | numpy, cumsum and direct loop | confirmed (8.0) |
| IMPULSE 1 to 3 at gain 32 clears 5 at every peak | 4,000 clicks per shape, fixture and tone | confirmed; minimum 5.25 (fixture), 5.54 (tone) |
| `dsp = { package = "cumple-dsp", ... }` beside `#[pymodule] fn cumple_dsp` | scratch mirror | confirmed: clippy clean, `PyInit_cumple_dsp` exported, imports |
| The old wiring fails | same mirror | confirmed (E0659, E0425, E0432) |
| 200-sample sine refill within 1e-2 | numpy `inpaint_gap` | confirmed (6.39e-3 at 0.5, 1.28e-3 at 0.1) |
| AR at a file end, linear at a chunk end | inpaint.rs 41 to 42; numpy | confirmed |
| float32 cumsum reproduces cathar's `local_rms` | against a scalar float32 loop | confirmed (identical) |
| Every port gap is a cathar gap | 400 layouts | contradicted (57 failures) |
| cathar-only drift sits where abs(y) < 1e-3; ΔSDR within 0.1 | same | confirmed (9.16e-4; 0.048 dB) |
| "Rounded to float32" differs from "as given" | fixture clipped at seven levels | contradicted (identical) |
| A 2^-50 nudge moves ΔSDR by up to 0.24 dB | numpy A-SPADE, threshold scaled | not reproduced (under 5e-14 dB) |
| rust-cache caches `~/.cargo/bin`; its key hashes Cargo.lock | README, action.yml | confirmed |
| `user_dir()` returns `.../cumple/profiles` | registry.py 28 to 30 | confirmed |
| The 36 s tiled fixture spans more than two blocks | reader.py 38 | confirmed (576,000 against 262,144) |
| `run: "$HOME/..." --version` parses | PyYAML | contradicted |

## Verdict

**Ship with changes.** Eighteen of the twenty-one rows are answered, and the rename, refill bound, preset and edge rule hold under measurement. Before Task 3: make the De-click drift rule two-sided (H1). Before Task 4: Victor decides how the De-clip spread is generated (H2), since as written it measures nothing about cathar's float32 arithmetic. The three Medium items go with their tasks. Checked hardest: the De-click fidelity test (400 layouts with an exact float32 detector) and the De-clip rule (seven levels, both readings, three mutants).

Counts: Critical 0, High 2 (H1, H2), Medium 3. Blocking: H1, H2.
