# 03f Skeptic: the precision round on the build-1 plan

Date: 2026-10-08.

Reviewed: diff aa79d79..e46b764 (HEAD e46b764732a08a866d41cfe786ded18a5ea7977d) against 03e, with cathar at f2c2842 (`gh api`), symphonia 0.6.1's conversion code, scratch Rust on rustfft =6.4.1 (Apple M1 Pro, NEON), and numpy re-expressions of cathar's declick and `declip_spade`. The worktree was left unchanged apart from this file.

## Steelman

Porting at cathar's own precision removes the cause of both failed tolerance designs instead of tuning a third: with the same f32 operations on the same rustfft, the comparison can demand near equality, and nothing I could find in build profiles, generics, constants or cathar's decode and write path stands in the way. The Task 4 mutations that slipped through 03e's spread now miss the 1e-6 bound by four or more orders of magnitude.

## 03e items after the round

| 03e item | Status | Checked at |
|---|---|---|
| H1 De-click drift rule one-sided | answered by design: the f32 build runs cathar's detector, so no drift is left to exclude. Two new problems sit in the replacement check (C1, C2) | plan 405 to 411, 436, 462 to 466; spec 59, 127 |
| H2 De-clip spread vacuous | answered: f32 build, 1e-6 per sample, 0.01 dB; mutations 2 and 3 now bite (Verified) | plan 485 to 492, 505 to 510; spec 128 |
| M1 stale counts | answered: 19 + 2 + 1 + 7 gives 29 and 30, flagged as an estimate; Tasks 3 and 4 match their snippets (Task 3's sentence omits the helper's own unit test); the fixture row reads "not run" | plan 42, 468, 510, 574; spec 132 |
| M2 PCM clips the clicks | answered | plan 201; spec 102 |
| M3 YAML and pwsh | answered: both snippets parse with PyYAML; Linux-only test step | plan 321 to 338 |

## Concerns

### C1. `gap_mask_from_output` cannot be written as described (High, blocking before Task 3)

Framework: inversion (when does the output diff misstate the gap?).

What I see: plan 409 asserts `ours == gap_mask_from_output(y, up)`; plan 436 defines the helper as the runs where `up != y`, "each widened to the gap the pad rule implies". But `inpaint_gap` rewrites the whole span, both 8-sample shoulders included (restore.rs 146 to 153, inpaint.rs 53 to 55), so the diff run already is the gap. In a numpy re-expression of cathar's declick on the fixture (exact float32 detector, 40 layouts, 1,014 gap runs), the diff run equals the whole gap in 1,009. The other 5 sit in digital zero runs: the AR solve's right-hand side is zero there, the fill is exactly 0, and only the click samples differ. A lone LSB in digital silence (the kind of detection 03d counted 11 times in SQAM) gives gap [2040, 2057) and diff run [2048, 2049). Widening is wrong on 99.5 % of fixture gaps; not widening is wrong on every zero-context gap. Also:
- the report's convention is never fixed: plan 456 records "each gap's start and length" (read as shoulders in), while plan 384 dilates the report by 8 (shoulders out);
- gaps overlap: 949 overlapping pairs among 5,780 gaps over 200 layouts, so a boolean mask cannot show spec 127's "every start and width equal".

Why it matters: a helper unit-tested on the simplest hand-built signal (one click in zeros) learns to widen and then fails a correct port on every gap; one that does not widen passes Task 3 and fails the harness's SQAM rows.

What to do: fix the report convention (gap start and length, shoulders included). Take cathar's gap list from the exact float32 re-expression of the detector (03e validated the cumsum against a scalar loop) and assert the port's list equals it, start for start. Then check cathar's output against that list: every sample where `up != y` lies inside a listed gap, and every listed gap holds at least one. Drop the widening.

### C2. Task 3's mutation 2 is an equivalent mutant on about half the layouts (High, blocking before Task 3)

Framework: Socratic (what does the mutant change on this input?).

What I see: plan 464 says computing `local_rms` in f64 inside the f32 build "is the drift the rule exists to catch". The fills never read the RMS, so the mutant changes the output only where a detection decision flips. Exact float32 against f64 RMS on the fixture with IMPULSE-like clicks: identical gap lists, and therefore identical output, in 108 of 200 layouts for one click shape and 100 of 200 for the other. My `add_clicks` approximates Task 1's, so whether seed 3 bites cannot be known until the real one exists.

Why it matters: on an equivalent layout, "see the upstream comparison fail" (plan 466) cannot happen; the executor stalls or reseeds without a rule.

What to do: in `test_the_precision_effect_is_measured`, assert that the f32 and f64 builds' gap lists differ on the chosen seed, and pick a seed where they do; mutation 2 then has to fail the fidelity test. Alternatively, prove mutation 2 with a Rust test: `local_rms::<f32>` on a loud burst followed by near-silence equals bits computed by a numpy float32 cumsum and written into the test.

### C3. The unchanged global constraint says "f64 throughout the core" (High, non-blocking; make the edit with C1 and C2)

Framework: consistency check.

What I see: plan 38 still reads "f64 throughout the core", against `Declick<F>` and `Declip<F>` instantiated at f32 (plan 357, 481; spec 58 to 59). Smaller slips nearby:
- plan 566 keeps "any tolerance that had to move and why" beside spec 129's "never widened";
- plan 456 reads "Then wrap the result then wrap";
- the docstring at plan 416 says rule 3 holds for both builds, but nothing asserts it for f32.

Why it matters: Task 7's fresh reviewer checks the branch against "this plan's constraints" (plan 588) and will flag the f32 build as a violation.

What to do: "f64 in the shipped build; the f32 instantiation exists only for the fidelity comparison", and "any tolerance other than rule 1's".

### C4. The f32 build's window precision is left implicit, and the obvious generic code gets it wrong (Medium, non-blocking)

Framework: pattern attraction.

What I see: cathar's `hann_window` is f32 from end to end (util.rs 5 to 13: f32 PI, `cosf`). The plan already has an f64 `Window::HannSymmetric` (Task 2), and generic code invites `F::from(<f64 expression>)`. In a Rust scratch, a Hann computed in f64 and cast differs from cathar's in 712 of 1,024 samples. In the numpy A-SPADE re-expression, that moves the output by 2.4e-4 to 2.5e-2 across the seven levels. It fails 1e-6 at every level, yet ΔSDR stays within 0.01 dB at four of them. `num-complex`, which supplies `norm_sqr` and the complex add and subtract in the thresholding, is locked but not pinned.

Why it matters: the bound catches it, but plan 490 ("a window, a scale, ...") never says which window is right.

What to do: in plan 501, say that `hann_window` is computed in F with `F::cos` and F's PI (`cosf` at f32), and that the f32 build never uses the shared `Stft` window. Pin `num-complex = "=0.4.6"` beside rustfft, or state that `Cargo.lock` holds it.

## Verified

| Claim | Source | Result |
|---|---|---|
| cathar's release profile and flags | root Cargo.toml; tree listing; workflows | `lto = "thin"`, `codegen-units = 1`; no `.cargo/config`, no rustflags, no target-cpu |
| The plan's pins equal cathar's lock | Cargo.lock | rustfft 6.4.1, realfft 3.5.0 (num-complex 0.4.6, num-traits 0.2.19): confirmed |
| Profiles change f32 FFT bits | scratch: raw FFTs at four sizes plus an A-SPADE-shaped pipeline under cathar's profile, the plan's, plain release, opt-level 1, debug | not observed: identical hashes under all five |
| Generic `F: Float` at f32 equals concrete f32 | same | 0 of 48,000 samples differ; `iter().sum()` and a loop give the same eps |
| `F::from(f64)` constants equal f32 literals | same | 1e-3, 1e-9, 1e-10, PI: identical bits |
| The SIMD path matters, so the same machine is required | `FftPlanner` against `FftPlannerScalar`, 1,024 points | 953 of 1,024 bins differ (max 7.6e-6): spec 62 confirmed |
| The CLI's decode and write are exact for float WAV | audio.rs 28 to 128; symphonia 0.6.1 conv.rs 606; main.rs 1420 to 1446 | f32 to f32 identity, no clamp above 1.0; hound writes f32 as given; no resample, normalisation or dither; `map_channels` sequential, no rayon |
| `inpaint_gap`'s f64 interior | inpaint.rs 18 to 56 | exact f32 to f64 copy, f64 solve, one cast back; the f32 linear pre-fill is dead for AR gaps |
| Order-dependent code in declick or `declip_spade` | restore.rs 116 to 194; declip.rs 133 to 276 | none: `sort_unstable` over values, sequential sums, no hash maps or threads |
| The cubic edge branch at window 64 | restore.rs 128 to 162, traced | unreachable: `gap_start >= 24`, `gap_end <= n - 24` |
| Task 4 mutation 2 (periodic Hann) bites | numpy float32 A-SPADE, seven levels | max diff 2.7e-2 to 1.98e-1: yes |
| Task 4 mutation 3 (`RELAX_BY = 1`) bites | same | 7.3e-2 to 4.5e-1: yes; every level runs all 100 iterations (k = 201) |
| 1e-6 is right in kind | `np.spacing`; perturbation runs | 1e-6 is 16.8 ulps at 0.5, 8.4 at 1, 2.1 at 4. Computed outputs sit under about 1; clicks above full scale that go undetected are copied, not computed. One ulp in one window sample moved A-SPADE by 6e-8 (passes); an f64 window, by up to 2.5e-2 (fails). Absolute works; an ulp assertion would state the intent better |
| The 0.01 dB bound alone would catch an f64 window | f64-window variant, seven levels | no: within 0.01 dB at 4 of 7; the sample bound is the one that bites |

## Verdict

**Ship with changes.** The approach holds: nothing in profiles, generics, constants or cathar's I/O stops a faithful f32 port from matching bit for bit, and the Task 4 mutations now fail by hundredths or more. Before Task 3, recover cathar's gaps from its detector instead of from a widened diff (C1), and pin a seed where mutation 2 changes a decision (C2); C3 is a line or two in the same edit, and C4 goes with Task 4. Checked hardest: whether the f32 build can match cathar at all (five profiles, generic against concrete code, the decode path) and the gap recovery (1,014 gap runs and the lone-LSB case).

Counts: Critical 0, High 3 (C1, C2, C3), Medium 1 (C4). Blocking: C1, C2.
