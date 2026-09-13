# 03b Deliverable review: the PR on loop/01-research

Date: 2026-09-12. Reviewer: fresh context, no history with the run. Inputs: `git diff main..HEAD` over README.md, docs/RELATED.md, docs/ROADMAP.md, site/index.html, AI_USAGE.md, CONTRIBUTING.md, docs/QA.md, tests/test_related.py; the run folder files 01 to 04 as the research record; the profile YAMLs under `src/cumple/specs/profiles/`; `uv run pytest` (200 passed, 200 collected), ruff (clean), and in-memory mutations of tests/test_related.py to see which assertions can fail.

## Steelman

The diff does what the frame asked and nothing more: it leaves the page's 9 by 7 comparison table byte for byte as it was, replaces one false sentence (a Dolby meter named DPLM) on the page, in README and in RELATED.md with a sourced one, and adds three tables whose 27 rows each carry a URL and a read date and whose hedges are the four permitted forms. The counts in the commercial table's closing paragraph (7 revisions, 8 true peak, 3 presets, 1 dialogue gate, 3 reports, 2 batch, 0 Atmos) reproduce exactly from the twelve cells above them, the open-source readings and failures trace line for line to 02a and to the skeptic's re-fetch, the Baton codec sentence traces to the skeptic's pdftotext of the datasheet, and the five test-count pins plus the README's "runs 171 of them" are enforced by tests/test_counts.py against pytest's own collection. The new tests fail on every real mutation I tried (URL removed, header date removed, section renamed, status word changed, run folder renamed, page note misnamed), the per-tool import follows the repository's existing pattern and works under a filtered run, and the roadmap's loop contract does not contradict CONTRIBUTING's merging rules.

## Findings, ranked

### 1. Critical, blocking: ROADMAP R4 states a false fact about cumple's own profiles

What I see: docs/ROADMAP.md:12, the Gap cell of R4 says "4 profiles accept `adm-bwf` (apple-tv, apple-immersive, disney-plus-5.1, netflix-5.1)". `grep -ln adm-bwf src/cumple/specs/profiles/*.yaml` returns three files: apple-tv, apple-immersive, disney-plus-5.1. netflix-5.1.yaml:38 reads `containers: [wav, bwf, rf64]`; its only ADM mention is inside the quoted `format.packaging` clause ("audio in an IMF, Quicktime or Atmos BWAV ADM container"), which is a muxed-source exception, not an accepted container. No branch produced this count: 04-recommendation.md:16 gives "n/e" for row 4's profile count, so the figure was added in the last commit without a run behind it.

Why it matters: this is the project's honesty rule broken on a claim that is checkable in one command, in the file that is meant to be the loop's ledger. It also feeds the frame's score formula (comparables times profiles) with a wrong factor for the row the 02b branch called cumple's one open gap.

What to do: change the cell to "3 profiles accept `adm-bwf` (apple-tv, apple-immersive, disney-plus-5.1); netflix-5.1 admits an ADM container only as a muxed-source exception" or drop the profile count and leave "n/e" as 04 has it.

### 2. High, blocking: RELATED.md attributes Dolby Dialogue Intelligence to Venera Pulsar, whose cell does not say so

What I see: docs/RELATED.md:97 (and 04-recommendation.md section 5, the sentence it was pasted from) says the algorithm "is licensed inside other vendors' tools such as Telestream Vantage and Venera Pulsar". The Vantage cell (RELATED.md:84) quotes "Dolby Dialog Intelligence" from telestream.net, so that half traces. The Pulsar cell (RELATED.md:86) quotes "Speech Gated" and nothing about Dolby; the skeptic's fetch 13 lists the Pulsar words found and Dolby is not among them. The skeptic's suggestion at 03-skeptic.md:96 ("as licensed inside Nugen, Telestream and Venera products") was a proposed wording, not a fetch result. The README version at README.md:493 avoids the vendor names and is fine.

Why it matters: it is the one sentence this run exists to fix, and it now carries an attribution no cell supports. A reader who follows the Pulsar URL will not find Dolby on it.

What to do: in RELATED.md:97, either drop "and Venera Pulsar" or write "Telestream Vantage, and a speech gate of unstated origin in Venera Pulsar". The 3 of 21 count at RELATED.md:99 is unaffected because it is already hedged as "of the Dolby Dialogue Intelligence class".

### 3. High, non-blocking: the Dolby E count applies a rule the neighbouring codec count contradicts

What I see: docs/RELATED.md:99 counts "delivery codec and container conformance, on 3 of 9 ... 4 of 9 counting Baton's Dolby AC-3, Dolby Digital Plus and Dolby-E support", then "Dolby E detection, on 3 of 9 (eFF, Aurora, Vantage's Analysis Pro tier)". The same Baton words ("supported codecs include ... Dolby-E", RELATED.md:85) count toward one gap and not the other, while eFF's cell (RELATED.md:83, "reads and writes Dolby E encoded channels") is counted as detection although it is the same kind of statement as Baton's. Only Vantage's cell contains the word "Detection". The same 3 of 9 is repeated at docs/ROADMAP.md:11 (R3) and 04-recommendation.md:15. The skeptic asked 04 at 03-skeptic.md:228 to "decide ... whether Baton's Dolby-E decode counts as a codec check"; 04 decided yes for codec and silently no for Dolby E.

Why it matters: the standard for these paragraphs is that every count re-derives from the cells above it. Here two counts read the same cell two ways, and a reader re-deriving the Dolby E count from the table gets four rows that mention Dolby E, not three.

What to do: either "Dolby E handling on 4 of 9 (eFF reads and writes it, Aurora aligns its guard band, Vantage Pro detects it, Baton lists it as a codec)" in both RELATED.md:99 and ROADMAP R3, or keep 3 of 9 and add the reason Baton's codec list is excluded, in the same clause where Baton is included for codecs.

### 4. Medium, non-blocking: "in their loudness clauses" overstates what the Netflix profiles show

What I see: README.md:493 and docs/RELATED.md:97 say Dolby Dialogue Intelligence is what "Netflix, Amazon and Disney name in their loudness clauses", and RELATED.md:99 says the six profiles "say" it. In netflix-2.0.yaml and netflix-5.1.yaml the phrase appears only at line 13, in cumple's own rule `notes` ("Netflix measures with Dolby Dialogue Intelligence"); the quoted Netflix clause (`loudness.dialogue_gated`, `clauses_verbatim: true`) says "dialogue loudness using ITU-R BS.1770-1" and does not name the algorithm. Amazon (lines 29 and 31), Disney (line 34) and Apple TV (line 29) do name it inside the quoted clause. So by the frame's own definition ("the number of cumple profiles whose clause names it") the count is four clauses plus two notes, and 02b line 12 cites netflix line 13, a note, as if it were a clause.

Why it matters: the distinction between what the destination's document says and what cumple adds in a note is the whole point of the grade system; the sentence blurs it for the two profiles the loop's first build item is most about.

What to do: "which Amazon, Disney and Apple TV name in their loudness clauses, and which cumple's two Netflix profiles record in their rule notes" in README.md:493 and RELATED.md:97, and in RELATED.md:99 "say" becomes "name, four in the quoted clause and two in cumple's rule note". Six stays the profile count; the wording is what changes.

### 5. Medium, non-blocking: two ROADMAP cells do not trace to their stated source

What I see: (a) docs/ROADMAP.md:13, R5's Gap cell gives "channel identifier against filename" as 1 of 9, and the ROADMAP header says every Gap cell comes "from RELATED.md". RELATED.md:99 does not count that capability at all, and the branch it would trace to, 02c-research-qc-platforms.md:40, counts 2 of 9 (Netflix, Baton's "Misplaced channels"); 04 changed it to 1 of 9 without saying why. (b) docs/ROADMAP.md:3 says "Status moves in one direction: queued, proposed, building, merged, accepted", but R7 at ROADMAP.md:15 carries the status "out of scope until cumple reads picture", a word the document's own vocabulary does not contain; tests/test_related.py:23 accepts it only because its STATUSES tuple has a sixth entry the document lacks.

Why it matters: the roadmap's value is that a reader can re-derive each cell; the test should pin the document's stated vocabulary, not a superset of it.

What to do: for (a), either add the channel-identifier count to RELATED.md:99 (1 of 9 with "Misplaced channels" named as a channel-placement check, not a filename check, if that is the reason) or change R5 to 2 of 9 to match 02c. For (b), add "out of scope" to the sentence at ROADMAP.md:3 as the one status outside the ladder, or give R7 the status "queued" with the picture condition in the Item cell.

### 6. Medium, non-blocking: AI_USAGE.md reads as if 9.0.1 were the pinned ffmpeg

What I see: AI_USAGE.md:250 to 252: "upgraded the machine's ffmpeg from 8.0 to 9.0.1, the version the published benchmark is pinned to, and the older binary no longer starts". The appositive attaches to 9.0.1. RELATED.md and BENCHMARK.md pin 8.0, as ROADMAP.md's "Open for Victor" says correctly.

Why it matters: AI_USAGE.md is the file a reader opens to see whether the record is honest, and this sentence says the opposite of the truth by grammar alone.

What to do: "upgraded the machine's ffmpeg from 8.0, the version the published benchmark is pinned to, to 9.0.1, and the 8.0 binary no longer starts".

### 7. Medium, non-blocking: two assertions in tests/test_related.py check less than their names say

What I see: (a) tests/test_related.py:76, `for folder in re.findall(r"`docs/graph-runs/([^`/]+)/`", ROADMAP)`: with the backticks removed from every run-folder mention in ROADMAP.md the loop body never runs and the test passes (confirmed by mutation); nothing asserts that at least one folder was found. (b) tests/test_related.py:60, `assert DATE.search(cell) or DATE.search(source_col)`: every Source cell in the three tables is a bare URL, so the per-row date clause is satisfied by the column header "Source, read 2026-09-12" for all 27 rows; the test's name promises a date per row, the assertion checks a date per table. DATE itself is fine: it matches both "2026-09-12" and "8 September 2026", the two forms the file uses, and rejects "12 September" and "September 12, 2026". The `_tables` helper drops any row whose cell count differs from the header, which today drops nothing (6, 12 and 9 rows parsed against 6, 12 and 9 present) but would hide a row with an unescaped pipe in a future edit.

Why it matters: a test that can pass with its subject removed is a receipt that proves nothing; the loop's done condition 7 ("research rows carry a URL and a read date") leans on this file.

What to do: for (a), bind `folders = re.findall(...)` and `assert folders` before the loop. For (b), either drop the `or DATE.search(source_col)` fallback and require the date in the header by name (`assert DATE.search(source_col)` once per table) with the test renamed to say so, or keep the fallback and rename. Optionally assert that the number of parsed rows equals the number of body lines starting with "|" so a dropped row fails loudly.

## What was checked and found sound

- "not checked" appears nowhere in the diff as a hedge; the two hits are the rule stated in ROADMAP.md:36 and a pre-existing sentence at AI_USAGE.md:224 about the old table. No em or en dash in any deliverable file or in the run folder (the only occurrences are the two literals inside the test itself).
- site/index.html changes are exactly two lines (340, 391), both `<p class="note">`; the compare table at 375 to 389 is untouched and `test_compare_table_matches_related_and_benchmark` still pins it at 9 by 7 against RELATED.md's first table.
- Test count: `uv run pytest --collect-only` reports 200; README, CONTRIBUTING, docs/QA.md, AI_USAGE.md and the page all say 200; README says "runs 171 of them"; tests/test_counts.py asserts all six against the live collection. The five new tests do not skip, so 200 minus 29 EBU cases is 171.
- Commercial table closing counts (7, 8, 3, 1, 3, 2, 0) re-derived by hand from the twelve cells: all correct. Dialogue gate 3 of 21, codec 3 of 9 and 4 with Baton, ADM 2 of 9 and 0 of 12, silence 3, dual mono 2, test tones 2 (Baton "Test tones", Vidchecker "BLITS, GLITS"), slate 1, duration and sync 1: all re-derive from the cells. The 0 of 21 claims hold as a conjunction (no row is offline, account-free and MIT together; none quotes a clause with a grade; none describes a stem-null diff).
- Six profiles naming the algorithm: verified by grep, with the exact Disney and Apple TV wording present at disney-plus-5.1.yaml:34 and apple-tv.yaml:29; Amazon naming VisLM2 at amazon-2.0-package.yaml:52 and amazon-5.1-package.yaml:55; the Amazon leader clause at padding.head with "forbidden without a number" in the tool-default note.
- Open-source table: every reading, version, failure message and the second-pass "loudness = SKIPPED (ffmpeg exit status 8)" sentence trace to 02a or to 03-skeptic.md:174 and 184; the machine's ffmpeg symlink still points at 9.0.1_1 as stated.
- AI_USAGE's "eighteen cited cells" and "two false claims" match the skeptic's fetch list (18 entries) and its Critical findings 1 and N2.
- ROADMAP versus CONTRIBUTING: done condition 6 (CI success on the PR head) is CONTRIBUTING's four green checks by another name; "no push to main" matches the protected branch; delegated merge after green checks and a fresh review does not conflict with any CONTRIBUTING rule.
- tests/test_related.py imports `_tables` from tests.test_site_numbers the way six other test modules already import helpers from siblings; tests/ is a package and the file passes alone, under `-k`, and under ruff check and format.

## Verdict

Ship with changes. Findings 1 and 2 are one-line corrections each and should land before merge; 3 through 7 are worth a follow-up commit on the same branch but do not by themselves make a published number false. The two things checked hardest were the count paragraph at RELATED.md:99 against its 27 cells and the profile YAMLs against every "profiles name" claim; the first held except for the Dolby E rule and the Pulsar attribution, the second is where the one false statement was.
