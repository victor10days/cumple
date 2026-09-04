# How AI was used to build cumple

This is the honest record of who did what. It exists because the Puentes
Fellowship form asks how the applicant thinks, builds and uses AI day to day,
and because anyone evaluating this repository deserves to know which lines
came from a model.

## The short version

cumple was built between 3 and 9 September 2026 in half days by Victor E.
Diaz working with Claude (Claude Code, Anthropic's command-line agent, model
Claude Fable 5.1). Claude wrote most of the code, the tests, the research
notes and the documents. Victor chose the problem, set the constraints that
shaped the product, approved each plan, made the calls listed below, and
supplied the thing a model does not have: years of delivering audio to these
specifications by hand. Every commit carries a `Co-Authored-By` trailer that
says the same.

## What Victor decided

- **The problem.** A delivery QC tool for audio came out of studio work whose
  clients included Warner Bros. and Caribbean Cinemas, where compliance with
  a platform's spec sheet was checked by hand and by ear before every send.
- **Not a GitHub tool.** The first plan proposed a GitHub Action, a
  pre-commit hook and a git diff driver. Victor rejected that in one line:
  audio engineers do not deliver through git. The product surfaces became
  the ones post houses already use: the bounce folder, a watch folder, a QC
  sheet that travels with the deliverables, and a drag-and-drop app on the
  Mac. JSON output and exit codes stayed for anyone who wants to script it.
- **Gates before publishing.** No public repository until the tool was
  finished, benchmarked against independent meters, and fully tested. The
  three gates are written down in the plan and each has a document in
  `docs/`.
- **Choices proposed by Claude and approved by Victor:** a heuristic speech
  detector instead of an ML model, so the tool installs in seconds and is
  labelled an approximation of Dolby Dialogue Intelligence everywhere it
  appears; `fix` applies gain and never limits, because limiting is a creative
  decision; the Leq(m) calibration convention is printed in the profile;
  every number the source does not state is marked as the tool's default.
- **The EBU test set.** The download script was blocked by the EBU site's
  bot protection. Victor fetched the 87 MB zip in a browser; from then on all
  29 official Tech 3341 and 3342 cases ran in the test suite.

## What Claude did

- **Research.** Three passes over primary documents (ITU-R BS.1770-5 and
  BS.2217, EBU R 128 and Tech 3341/3342/3285, ATSC A/85:2026, AES TD1006 and
  TD1008, TASA and SAWA, ISDCF, the Apple, Warner Bros. Discovery, Paramount,
  Hulu, NBCUniversal, Spotify, SoundCloud, Apple Podcasts and ACX pages) and
  a survey of what already exists in open source and in commercial QC tools.
  Every profile records where each number came from and how good that access
  was, with a grade from READ to COMMUNITY.
- **Code.** The BS.1770-5 meter with K-weighting re-derived at any sample
  rate, the true-peak filter from the ITU table, loudness range, the speech
  detector, Leq(m) from the TASA response table, the rules engine with
  either/or rules and the speech switch, the audio diff, the watch folder,
  the gain-only fix, the QC sheet, the macOS droplet, 28 profiles.
- **Tests and benchmarks.** 112 tests, including synthetic signals with
  analytic answers and the official EBU cases; cross-checks against ffmpeg's
  `ebur128` filter, pyloudnorm and an independently designed interpolator;
  the scripts that regenerate `docs/CONFORMANCE.md`, `docs/BENCHMARK.md` and
  `docs/PERF.md`.

## Three times Claude was wrong and a test caught it

1. **The K-weighting shelf.** Claude first designed the high shelf from the
   audio cookbook formulas. At 1 kHz it gave +0.45 dB where the ITU filter
   gives +0.66 dB, and the coefficients did not match the values printed in
   BS.1770 for 48 kHz. The fix was the bilinear form published by De Man,
   and the test now asserts equality with the printed coefficients to seven
   decimal places.
2. **The onset overshoot.** An 8 kHz tone written at full scale read +0.2 to
   +0.36 dBTP, and Claude's first explanation was a filter error. It was
   not: a full-scale tone that starts abruptly has a real inter-sample
   overshoot, and any correct true-peak meter reports it. The synthetic
   tones in the tests now fade in and out, and one test documents the
   overshoot on purpose.
3. **The 100 ms grid.** The meter first kept energies on a 100 ms grid, which
   is what the EBU short-term and momentary hop suggests. EBU cases 13 and
   14 then read 0.22 LU low, because their 400 ms bursts sit at 20 ms
   offsets and a 100 ms grid never lines up with them. The meter moved to a
   10 ms grid, and all 29 cases passed.

Smaller ones, in the same spirit: the diff's least-squares gain fit absorbed
an EQ change into the gain figure (now the gain is the median third-octave
band delta, so EQ shows up as EQ); the LFE detector's high-pass was too
gentle to tell a low-passed LFE from a full-range channel (now sixth order
at 250 Hz); the speech detector's floor at the 30th percentile dropped
dialogue in music-heavy programmes (now the 5th percentile plus 3 dB, with a
one-second dilation); the metadata reader reports an unset BWF loudness
field as 327.67, which had to be recognised as "unset" rather than as a
loudness value.

## The day-to-day pattern

- **Plan first, in writing.** The plan file holds the research matrices,
  the architecture, the ranked feature list and the definition of done. Work
  happened against it and it was revised when Victor changed direction.
- **The standard is the oracle, not the model.** Tests were written from the
  expected values printed in Tech 3341 Table 1 and from signals whose answer
  is known analytically, never from the meter's own output.
- **Independent cross-checks.** Two other implementations and one
  independent filter design were run on the same files. Where they disagree
  with cumple, the disagreement is documented rather than hidden
  (`docs/BENCHMARK.md` notes what ffmpeg reports on the case 6 centre channel).
- **Small commits, each closing one thing,** with the trailer that names
  the model.
- **The model cannot listen.** Nothing here decides whether a mix sounds
  right. That is why `fix` never limits, why the dialogue gate is labelled an
  approximation with its block count printed next to it, and why the manual
  QA on real bounces in `docs/QA.md` is done by a person.

## What was not AI

The domain, the surfaces, the constraints, the sign-off, and the ear.
