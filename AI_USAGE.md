# How AI was used to build cumple

This is the honest record of who did what. It exists because the Puentes
Fellowship form asks how the applicant thinks, builds and uses AI day to day,
and because anyone evaluating this repository deserves to know which lines
came from a model.

## The short version

cumple's code was written on 3 and 4 September 2026, in two half days, by
Victor E. Diaz working with Claude (Claude Code, Anthropic's command-line
agent, model Claude Fable 5.1); the review pass, the browser re-read of the
studio specifications, the packaging and the real-dialogue check followed on
4 and 5 September. Claude wrote most of the code, the tests, the research
notes and the documents. Victor chose the problem, set the constraints that
shaped the product, approved each plan, made the calls listed below, and
brought years of delivering audio to these specifications by hand, which no
model has. Every commit carries a `Co-Authored-By` trailer that
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
  was, with a grade from READ to COMMUNITY. The first pass could reach the
  Netflix, Disney+ and Amazon MGM Studios pages only through search extraction
  (graded SE and GATED); a browser session the next day read all three
  directly, and their clauses are now quoted verbatim (grade READ), which
  changed real numbers: Disney's tolerance is ±0.4 LU, not the assumed ±2, and
  Netflix requires one mono file per channel. A third pass on 6 September,
  when Victor asked for the specifications of every major studio, added
  Disney's General Entertainment, R128 and trailer standards (read in the
  browser), the CBS, ABC and Fox broadcast documents (read from their PDFs),
  Apple's immersive audio profile and a community-graded Peacock entry, and
  recorded that Sony Pictures, Lionsgate, Starz, Universal Pictures,
  Paramount+ and the HBO and Max brand specs publish nothing a tool can quote.
  Those documents also exposed a measurement gap: an eight-channel file with a
  stereo fold-down on tracks 7 and 8 read as 7.1, so the layout meter learned
  to tell the two apart.
- **Code.** The BS.1770-5 meter with K-weighting re-derived at any sample
  rate, the true-peak filter from the ITU table, loudness range, the speech
  detector, Leq(m) from the TASA response table, the rules engine with
  either/or rules and the speech switch, the audio diff, the watch folder,
  the gain-only fix, the QC sheet, the macOS droplet, 39 profiles.
- **Tests and benchmarks.** 194 tests, including synthetic signals with
  analytic answers and the official EBU cases; cross-checks against
  libebur128, pyloudnorm, ffmpeg's `ebur128` filter, loudcheck and an
  independently designed interpolator;
  the scripts that regenerate `docs/CONFORMANCE.md`, `docs/BENCHMARK.md` and
  `docs/PERF.md`.
- **Design.** On 6 September an audit against a checklist of the tells of
  generated interfaces found the QC sheet rendering in a fallback font,
  overflowing a phone and failing contrast on its amber. The sheet was rebuilt
  on a locked system (`design.md`, `tokens.css`, embedded font subsets), and
  the audit's checks became tests: no colour outside the token block, every
  text pair above 4.5:1. The same system then gave the diff its own sheet
  (`cumple diff --sheet`): the verdict as a stamp, the alignment numbers, both
  files' levels, and the third-octave deltas as bars with the gain removed.

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

## A second pair of eyes, also a model

Before the repository went public, a separate Claude agent reviewed the source
tree read-only, with instructions to confirm every finding by running the code
and to drop anything it could not confirm. It reported seventeen findings,
three of them serious: `fix --out` pointed at the source file truncated the
source; a Broadcast WAV whose metadata carries a UMID crashed the JSON output,
which also made the watch folder skip such files silently; and 7-, 10- and
12-channel files weighted the LFE like a screen channel, a 2.5 LU error on a
7.1.2 bed. The rest ranged from a watcher that died when a bounce was moved
away mid-poll to a duration that could print as 0:60.0. All seventeen were
fixed in one commit; fourteen carry a test that pins the corrected behaviour,
and the other three were one-line changes (a rounding rule, an inert option,
a clamped option). Victor did not find these; the review pass did.

## Real dialogue, a test the tool did not pass

On 5 September Victor asked for real dialogue recordings to test the speech
gate on, since every test until then had used synthetic speech-like noise.
Claude found freely licensed material: Sintel and Tears of Steel, two Blender
Foundation films that publish both the finished mix and a music-and-effects
version without dialogue; a LibriVox narration; a NASA podcast; two
public-domain feature films; and the EBU SQAM speech tracks. Where a mix
carries more speech-band energy than its dialogue-free twin, dialogue is
present, which makes a reference no detector can argue with. Against that
reference the heuristic read the dialogue-gated loudness 1.6 LU low on one
film and 6.7 LU low on the other, finding dialogue in quiet scenes and missing
it under music; on clean speech and on music without dialogue it was right.
Silero VAD, the standard open model, was more precise on both films but
missed the same quiet dialogue on Sintel. The method, the numbers and the
recordings' licences are in docs/DIALOGUE.md, and the README's limits
paragraph carries the measured figures instead of a guess. The decision on
the meter itself (keep the heuristic and label it, or add Silero as an
optional backend) is Victor's; the numbers went into the documentation the
same day.

## The desktop app and the page (7 to 9 September)

After the repository went public, Victor asked for a desktop application for
macOS, Windows and Linux and a landing page for it. He decided the shape: the
page hosted from the repository (GitHub Pages at first; since 7 September a
Render static site serves it and Pages is a mirror), the macOS app finished and
tried first, Windows and Linux built by CI and verified from its logs, the
builds unsigned. Claude surveyed the engine for platform-specific code (one
function, the Chrome lookup for the PDF), read pywebview's source at the tag
for how dropped files carry their paths, wrote the app, its tests, the
PyInstaller spec, the release and pages workflows, and the page. Three things
were caught by measuring rather than by reading: a GitHub Action major tag
that a research pass had reported as current did not exist (the first CI run
failed in three seconds); Chrome given a throwaway profile wrote the PDF and
then never exited, so the "safer" flag was dropped; and the install hint for
the app vanished from the terminal because the console markup read
`[app]` as a style. The app never runs a check against a destination it
guessed, and never measures two files at once, both by decision.

## The day-to-day pattern

- **Plan first, in writing.** The plan file holds the research matrices,
  the architecture, the ranked feature list and the definition of done. Work
  happened against it and it was revised when Victor changed direction.
- **The standard is the oracle, not the model.** Tests were written from the
  expected values printed in Tech 3341 Table 1 and from signals whose answer
  is known analytically, never from the meter's own output.
- **Independent cross-checks.** Four other implementations and one
  independent filter design were run on the same files. Where they disagree
  with cumple, the disagreement is documented rather than hidden
  (`docs/BENCHMARK.md` notes what ffmpeg reports on the case 6 centre channel).
- **Small commits, each closing one thing,** with the trailer that names
  the model.
- **The model cannot listen.** Nothing here decides whether a mix sounds
  right. That is why `fix` never limits, why the dialogue gate is labelled an
  approximation with its block count printed next to it, and why the QA log
  in `docs/QA.md` says who or what ran each check and which rows still wait
  for a person with real bounces, a DAW, or a Windows or Linux machine.

## The review loop (8 September)

With the page and the app live, Victor asked for a contrarian pass and a
loop: a devil's advocate skill (notmanas/claude-code-skills, MIT, installed
unmodified) run against the submission, its findings applied, then a code
review and a verification pass, repeated until a pass came back clean. The
first run returned seven concerns and the verdict "ship with changes". What
came out of it, under Victor's rule that claims must not outrun evidence: the
conformance, benchmark and performance reports regenerated for 0.2.0 (the
performance table now shows the real memory of the current meters and the
word "constant" is gone); a CI job that runs the 29 EBU cases when a private
link to the set is provided, and a README sentence saying that no link is set
yet; the QA log's first entries, each naming who or what ran the check and on
what; a warning on the false-pass direction of the dialogue gate, narrowed by
the code reviewer's finding to windows where a false pass is possible; the
page's caveat under the download button for the two builds nobody had run by
hand, and then the release workflow opening those two windows in CI with
screenshots; a test that fails whenever the documented test count drifts
from what pytest collects. Two things the loop caught in Claude's own work: a
test count of zero written into the docs when a collection command produced
no output, fixed within the hour, and a benchmark figure the loop itself got wrong: a pass changed the
page's 0.05 LU to 0.04 LU on a misread of the table (the checking script
dropped every cell that carried a pass mark), the code reviewer caught it,
and a test now derives that figure and the others on the page from the
reports. One process failure: a pull
request whose copy test was red merged because the repository then had no
branch protection; the fix followed within minutes, and since PR #20 main is
protected: a merge needs the four checks green on the head commit, linear
history and no direct pushes. Release 0.2.1 exists so that the downloads
carry the code these documents describe. Later that day Victor ruled that no
cell of the page's comparison table may read "not checked" (six did), and
three more cells turned out to overstate: libebur128 passing the EBU set "per
its README", which makes no such claim; pyloudnorm "integrated only", when it
also measures loudness range; DeltaWave "yes" for offline use, which its site
does not state. Claude read the five tools' documentation and source, ran four
of them on the EBU files beside cumple (the benchmark grew to libebur128
through ctypes and to loudcheck), and wrote `docs/RELATED.md`, which records
every source with its date; a test holds the page's table equal to that
document cell for cell and each run cell equal to the run's summary line. A
reader of the page took the client list in "Who made it" for the tool's
customers; the paragraph now says what it meant, a year of studio work.

