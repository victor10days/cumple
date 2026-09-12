# 03 Skeptic: competitive landscape branches

Date: 2026-09-12. Fresh context; no history with the branches. Inputs were the files below and the web, used only to re-fetch cited cells.

## Inputs read

- `01-frame.md`, `02a-research-open-source.md`, `02b-research-commercial-meters.md`, `02c-research-qc-platforms.md` (this folder)
- `docs/RELATED.md` (the standard every cell must meet)
- `README.md` lines 427-497 (Honest limits, Related work)
- `~/.claude/skills/devils-advocate/SKILL.md` and its three reference files
- Mechanical checks run here: `wc -w` per branch (02a 897, 02b 1053, 02c 898); `grep` for em and en dashes (none in any branch); `grep -i` for "not checked", "unchecked", "unconfirmed", "unverified", "not confirmed" (hits in 02a line 33 and 02b lines 26, 29, 30, 31)
- Eighteen web fetches, listed in full under "Cells fetched and verified". Every fetched page was treated as data; nothing on them set scope.

## Steelman

The three branches answer the frame's question in the frame's own shape: one table each, a per-row "cumple lacks / it lacks" pair, a ranked options list, an honest unknowns list, and a one-paragraph recommendation, with the prose kept short and the date stated. Where a page blocked the fetch (Avid 403, Steinberg shell, Netflix JS app, iZotope 403) the branches said so in the cell instead of guessing, and 02a recorded the exact compiler errors and Homebrew responses that stopped two installs, which is more evidence than most research runs leave behind. The 02c quotations are the strongest work here: six of six Vidchecker phrases, three of three eFF phrases, five of five Pulsar phrases and four of four Netflix NPFP phrases exist word for word on the cited pages, and the Aurora end-of-sale date and Qualify migration sit exactly where 02c said they would, in Telestream's own PDF.

## Cells fetched and verified

Format: branch, product, URL fetched, the quoted words, result.

1. 02a r128gain, `https://github.com/desbma/r128gain` and `raw.githubusercontent.com/desbma/r128gain/master/r128gain/__init__.py`. Cell: "no read-only flag". Found on the README: "Scan a single file and display its loudness information: `r128gain -d an_audio_file.mp3`". Found in source: `"-d", "--dry-run", action="store_true", default=False, help="Do not write any tags, only show scan results"`. Cell contradicted.
2. 02a ffmpeg-normalize, `https://github.com/slhck/ffmpeg-normalize` and `https://pypi.org/pypi/ffmpeg-normalize/json`. "--batch", "--print-stats", "-n / --dry-run": found. Version 1.42.0 and `license_expression: MIT`: found.
3. 02a bs1770gain, `https://formulae.brew.sh/api/formula/bs1770gain.json`: HTTP 404, as the cell says. Found.
4. 02b VisLM2, `https://nugenaudio.com/vislm`. "$449", "£314", "€384": found. "flags & alerts": found as "Navigable flags & alerts". "rev 1-4" in quotation marks: page says "ITU-R B.S. 1770, revisions 1, 2, 3 and 4", a paraphrase, not a quote. Leq(m) TASA/SAWA and Leq(a): found. No dialogue gating words anywhere on the page, which matches the cell's "dialogue n/s" and contradicts 02b section 3 (see Contradictions).
5. 02b LM-Correct 2, `https://nugenaudio.com/lm-correct`. "$399", "£279", "€339": found. "dialog-gated measure": found. DynApt, "Leq(m) (TASA)": found. No BS.1770 revision on the page: matches the cell.
6. 02b AMB, `https://nugenaudio.com/amb`. "stand alone application for Windows": found. Sixteen queues: found as "you can purchase up to a total of 16". "watched folders" in quotation marks: page says "automatically watching output folders" and "Queue/watch folder", a paraphrase. "text logs, and graphical logs": found.
7. 02b Youlean, `https://youlean.co/youlean-loudness-meter/`. "$29+ tax": found. "only doing the analysis": found. "ITU-R BS.1770-4": found. PDF, PNG, SVG export Pro only: found. Nineteen named presets (8 standards, 11 services) counted on the page: matches "19+".
8. 02b DRMeter MkII, `https://www.maat.digital/drm2` (the two URLs I guessed from the cell's bare "maat.digital" returned 404 first). "$129" perpetual and "$149" bundle: found. "SPPM": found. Six presets: found verbatim as "Spotify, iTunes Music & MfiT, YouTube, TIDAL, R128 & A/85 and Pandora". "2dB too loud": not found on this page or on `/drmeter`. No dialogue gating, no iLok or account wording: matches the cell and the unknown.
9. 02b RX Loudness Control, `https://support.izotope.com/hc/en-us/articles/8960898268305`: HTTP 403, page unreachable, same as the branch. `https://www.izotope.com/en/products/rx-loudness-control.html` serves the RX 12 Advanced page listing "Loudness Control" as a module, consistent with "folded into RX Advanced". The date 2022-09-07 stays unverified.
10. 02c eFF, `https://emotion-systems.com/products/eff`. "True Peak, Loudness Range (LRA), short term and momentary loudness, and legacy PPM": found. "EBU R128, ATSC A85 and TR-B32": found. "PDF reports and XML log files": found. Dolby E, watch folder, "Windows, Mac, and Linux": found. No price: matches.
11. 02c Vidchecker, `https://www.telestream.net/vidchecker/specs.htm`. "channel mapping", "phase coherence between channels", "DialNorm", "BS-1770", "BLITS", "GLITS": all found. "Windows Server 2016, 2019, 2022, 2025, Windows 10 or 11": found. A second targeted fetch for "duration", "sync", "A/V", "lip", "offset": none on the page.
12. 02c Vantage, `https://www.telestream.net/vantage/vantage-analysis.htm`. "ITU 1770-3" and "Dolby Dialog Intelligence": found in one sentence. "dialog loudness": found. The page's feature table also lists "Dolby E Detection" and "Dolby Atmos Loudness Measurement", which the cell does not carry.
13. 02c Pulsar, `https://veneratech.com/pulsar-automated-file-qc`. "Speech Gated", "Mosquito Tone", "Dual Mono", "Phase Mismatch", "Language ID": found. Six templates, four editions including Pay-Per-Use, watch folders, SOAP API: found. The page also lists Duration, Timecode and Container checks, which neither the cell nor the section 3 counts credit.
14. 02c Aurora, `https://www.telestream.net/pdfs/support/Telestream_Aurora_EOS-Announcement.pdf` (linked from `telestream-support/aurora/support.htm`; the `/aurora/` product URL is a 404). Read directly: "Effective May 1, 2025, Telestream will no longer offer new licenses of Aurora QC Software products for sale"; "Qualify QC Product Suite. This serves as a direct replacement for Aurora"; End of Support May 1, 2030. Found. "Discontinued" means end of sale; support runs five more years.
15. 02c AudioTools Server, `https://www.telosalliance.com/minnetonka/audiotools-server`: HTTP 404 at the only path I could infer from the cell's "telosalliance.com Minnetonka AudioTools Server". Page unreachable; the "1000+ templates" and "REST API" cells stay unverified.
16. 02c Auphonic, `https://auphonic.com/`. "2 hours of audio per month": found. "target loudness, true peak limit, MaxLRA": found. Watch Folders, API, CLI, Zapier, account required: found. The presets cell "Spotify, YouTube, Apple Podcast, EBU R128": not on this page; `auphonic.com/help/algorithms/loudness.html` is a 404; the row cites no deeper URL.
17. 02c Loudness Penalty, `https://www.loudnesspenalty.com/`. "Your file will not be uploaded, stored or shared": found. "-2.4 on YouTube": found. No account: found. The page names eight services (the cell's seven plus "Apple Legacy").
18. 02c Netflix NPFP, `https://npfp.netflixstudios.com/program-conditions`. "detect silence, audio labelling and dual mono audio": found. First 2 minutes, 25%, 50%, 75%, last 2 minutes: found. "technical properties of WAV files": found. "correct channel identifiers": found. No true peak, LRA or 2-pop: matches.

Tally: 13 cells confirmed word for word or by the exact fact, 3 paraphrases presented inside quotation marks (VisLM "rev 1-4", AMB "watched folders", DRMeter "2dB too loud"), 1 cell contradicted by the source (r128gain), 2 pages unreachable (iZotope 403, AudioTools Server 404), 1 cell whose cited page does not carry it (Auphonic presets).

## Concerns

### 1. The r128gain row rests on a false fact, and the run lost its second set of readings to it

Severity: Critical. Blocking.
Framework: Socratic, probing evidence; ai-blind-spots 8 (a flag denied that exists) and 3 (confidence without correctness).

What I see: 02a line 31 says "not run here: tags every file scanned, no read-only flag" and repeats the blocker in the note under the table, in section 4 ("withheld to avoid mutating the shared cache") and in section 5 ("a read-only flag" as the condition for r128gain to return). Upstream, r128gain 1.0.7's own README and source define `-d, --dry-run`, help text "Do not write any tags, only show scan results" (fetch 1). The branch measured a synthetic tone with the default write mode, saw bytes change, and stopped, without reading `r128gain -h`.

Why it matters: the frame's "done" for 02a is readings on seq-3341-1 and seq-3341-2 for every tool that could run. r128gain could. As written, 04 would carry "r128gain: no read-only mode, off the page until it has one" into the roadmap as a fact, and the landing-page candidate list would be one tool shorter than the evidence allows.

What to do: run `r128gain -d` (state version 1.0.7) on both EBU files, `cmp` each file before and after to prove no write, record integrated loudness and sample peak with the +-0.1 LU verdict, and rewrite the row, the note, section 4 and section 5. If it lands in tolerance it is the second candidate for a `scripts/benchmark_meters.py` run, beside ffmpeg-normalize.

### 2. Both ranking sections count capabilities the table cells never recorded, and 04's gap score is computed from those counts

Severity: Critical. Blocking.
Framework: Inversion (the surest way to a wrong roadmap is a capability count that does not trace to evidence); Socratic, probing evidence.

What I see, 02b section 3:
- "Named presets (10 of 12)". The Presets column reads n/s for LM-Correct 2, AMB, Dolby, Adobe, Avid and WaveLab, and "unconfirmed" for WLM Plus. Five rows carry a preset list. Ten is not derivable from the table.
- "Dialogue gating named (VisLM, LM-Correct, DRMeter ...)". The VisLM2 cell says "dialogue ... n/s" and the live page has no gating words (fetch 4). The DRMeter cell's "gate R128/A85" is the BS.1770 relative gate, not a dialogue gate, and the live page has no dialogue gating (fetch 8). Only LM-Correct 2 is supported (fetch 5).

What I see, 02c section 3 and the bold paragraph above it:
- "Dolby E/Atmos/ADM metadata: 4 of 9 (eFF, Baton, Aurora, Vantage)". This fuses two capabilities. Dolby E is a legacy broadcast codec; Atmos and ADM are what README:456-457 admits cumple lacks. None of the four quoted cells contains the words Atmos or ADM; the Vantage cell names "Dolby Dialog Intelligence", a gating algorithm. (Vantage's live page does list "Dolby Atmos Loudness Measurement", fetch 12, but the cell does not carry it, so the count is right by accident for one row and unsupported for three.)
- "Codec/container conformance (AC-3, AAC, MXF): 4 of 9 (eFF, Baton, Aurora, Netflix)". The Baton and Aurora quoted cells contain no codec or container wording. Pulsar's page lists Container checks (fetch 13) and is not counted.
- "A/V duration/sync: 3 of 9 (Baton, Vidchecker, Aurora)". The Vidchecker specs page contains no "duration", "sync", "A/V", "lip" or "offset" (fetch 11). The Baton and Aurora cells carry no duration wording either. Pulsar's page lists Duration and is not counted.
- "Channel-identifier-vs-filename: 2 of 9 (Netflix; Baton's 'Misplaced channels')". "Misplaced channels" appears nowhere in the Baton cell.
- The paragraph opens "Every platform here has, cumple does not:" and then names four of nine; Auphonic and Loudness Penalty have none of the three items.

Why it matters: 01-frame defines the 04 roadmap score as "number of comparables that have the capability, times the number of cumple profiles whose clause names it". Feed it these counts and the roadmap's top item (Atmos/ADM, which both 02b and 02c recommend) is ranked on vendors who do Dolby E, and the second and third items are ranked on cells that say nothing. The table was supposed to be the deliverable; here the prose outran it.

What to do: recompute every count strictly from the cells, and where a count needs a fact the cell lacks, fetch the page and put the words in the cell first (Baton and Aurora for codec, container and duration; Vantage for "Dolby Atmos Loudness Measurement"; Pulsar for Duration and Container). Split "Dolby E" from "Atmos/ADM" into two lines in 02c section 3. Change 02b's preset count to what the Presets column shows, and drop VisLM and DRMeter from the dialogue-gating line unless a Nugen or MAAT page is quoted for it.

### 3. The Avid row asserts two facts it also says it could not read

Severity: High. Blocking before any of this reaches RELATED.md or the page.
Framework: Socratic, clarification; the frame's "not checked" rule.

What I see: 02b line 30. The Measures cell says "No native LUFS meter in Pro Tools; Pro Limiter's BS.1770-3/TP/LRA claims unchecked (403)". The "it lacks vs cumple" cell says "ships no loudness meter at all". The Price cell says "avid.com 403 twice; unverified". The row therefore claims Pro Limiter carries BS.1770-3, true peak and LRA metering and, three cells later, that the product ships no loudness meter at all. Both statements are unsourced and one of them must be wrong. "unchecked" is "not checked" by another spelling, which 01-frame forbids in a cell.

Why it matters: this is the only row in the three tables that states a negative capability as fact without a page behind it, and it does so in the column 04 reads for gap lists. RELATED.md's standard is that nothing is copied from a third party's description and every cell traces to the vendor; a cell traced to nothing is worse.

What to do: replace the three cells with "not read here: avid.com returned 403 twice on 2026-09-12" and remove "ships no loudness meter at all", or fetch Avid's Pro Limiter documentation from a host that serves it (Avid's PDF guides live on `resources.avid.com`) and quote it. Do not let the "no native meter" sentence survive without a URL.

### 4. The frame's "Dolby DPLM" premise is contradicted by 02b and resolved by nobody

Severity: High. Blocking for 04's answer to "where cumple sits".
Framework: Socratic, meta-question (is the comparison target real?); Five Whys in reverse.

What I see: 01-frame Context, RELATED.md "Not compared" and README "Related work" all say "Nugen VisLM and Dolby's DPLM are the commercial meters the studios name". 02b's grep of cumple's own profiles found Amazon naming "Nugen Audio VisLM2" and four profiles naming "Dolby Dialogue Intelligence", an algorithm, with "no SKU given"; 02b then reports "No page names a live 'Dolby Professional Loudness Meter (DPLM)'", lists it as an unknown, and fills the Dolby row with the Atmos Renderer, whose cell has no dialogue-gating entry. Dolby Media Meter is reported dead since 2018 on a third-party news page. 02c, meanwhile, shows the Dolby algorithm shipping inside Telestream Vantage ("Dolby Dialog Intelligence", fetch 12) and Venera Pulsar ("Speech Gated", fetch 13).

Why it matters: the run exists to say where cumple sits against the meters the studios name. If one of the two named meters is not a product, RELATED.md's published sentence is wrong today and 04 cannot place cumple against it. The evidence in hand says the studios name a Dolby algorithm that third parties license, which is a different competitive fact from a Dolby meter.

What to do: 04 must either produce a Dolby URL for a product called DPLM, or recommend rewriting the RELATED.md and README sentence to name "Dolby Dialogue Intelligence, as licensed inside Nugen, Telestream and Venera products" and treat Vantage and Pulsar as the file-based homes of the algorithm. 02b's profile-grep claim itself (which profiles name what) is outside my inputs and should be re-run by the recommend agent before it is relied on.

### 5. Rows in 02b and 02c do not carry a fetchable URL, which is the loop's own done condition

Severity: High. Blocking for the loop gate ("research rows carry a URL and a date").
Framework: Inversion (what would make the skeptic step impossible: cells nobody can re-fetch).

What I see: 02b's URL column holds bare domains: "nugenaudio.com" for three products, "maat.digital", "waves.com", "adobe.com", "avid.com", "steinberg.help". Finding the DRMeter MkII page took three guesses (fetch 8). 02c's Src list mixes real paths with descriptions: "[7] telestream.net Aurora datasheet 2NW-60054-10", "[9] telosalliance.com Minnetonka AudioTools Server" (404 at the only path I could infer, fetch 15), "[10] auphonic.com" (the presets cell is not on that page, fetch 16), "[13] partnerhelp.netflixstudios.com Welcome-to-Asset-QC". 02a is the only branch whose every row carries a resolvable address. The date is fine: both 02b and 02c state one read date for the whole table, which honours "the date read".

Why it matters: 01-frame's first constraint is a URL per cell, and the loop's machine-judged done condition is "research rows carry a URL and a date". Two of three branches would fail that check today, and the skeptic step the frame requires ("fetched at least five cited cells") had to guess its way to the pages.

What to do: put the full page URL in each 02b row and each 02c Src entry, including the exact URL for the Auphonic presets, the Telos AudioTools Server page, and the Telestream Aurora datasheet. Where the page was reached through a search index rather than fetched (iZotope, Adobe helpx, Waves presets, Clarity M reseller), say "via search index, page not fetched" in the cell, which is what the frame's "not run here and the reason" form looks like for a page.

### 6. 02a stopped at self-imposed limits the frame did not set

Severity: Medium. Non-blocking.
Framework: Pre-mortem (the optimistic shortcut); ai-blind-spots 2 (scope acceptance).

What I see: 02a declares the EBU files "not copied" and treats that as a constraint; 01-frame allows a scratchpad venv and Homebrew installs and says nothing against copying two wav files. A copy would have let r128gain run even without the dry-run flag. bs1770gain is marked "not run here" because it is absent from Homebrew, but the branch's own cited URL is the project's source site, and the frame's scope is tools "installed and run here", not "installed from Homebrew". The sweep for "any other CLI meter found on PyPI or Homebrew" produced two PyPI names and one cask; Homebrew carries `rsgain` 3.8 (BSD-2-Clause, states ITU-R BS.1770 and true peak on its README, fetches this run), which was not tried; I did not confirm whether it has a scan-only mode. Finally, ffmpeg-normalize wraps ffmpeg loudnorm, the same engine RELATED.md already shows through loudcheck, and 02a's own note admits its true-peak figure equals sox's sample peak on both files, so a page column for it would show one engine twice unless the benchmark run shows otherwise.

Why it matters: the 02a table has one BS.1770 reading set where the frame asked for a table of readings. 04's "which 02a tools would earn a page column later" will be decided on the thinnest branch.

What to do: on the r128gain re-run (concern 1), also try `rsgain` from Homebrew and bs1770gain from source with the exact failure recorded if it does not build; copy the two wav files into the scratchpad if any tool insists on writing. State in section 3 that ffmpeg-normalize shares loudcheck's engine so 04 weighs the column on that basis.

### 7. 02b is over the word cap, and three quoted cells are paraphrases in quotation marks

Severity: Medium. Non-blocking.
Framework: Socratic, clarification (what the quotation marks promise).

What I see: 02b is 1053 words by `wc -w` against "under 900". VisLM "rev 1-4" (page: "revisions 1, 2, 3 and 4"), AMB "watched folders" (page: "watching output folders", "Queue/watch folder"), DRMeter "2dB too loud" (not on `/drm2` or `/drmeter`) are presented in quotation marks. Loudness Penalty names eight services, the cell says seven. 02c's Aurora "Discontinued" is end of sale; the PDF gives End of Support May 1, 2030.

Why it matters: 01-frame allows close paraphrase but the quotation marks claim verbatim, and RELATED.md's standard quotes verbatim throughout; a reader who re-fetches will find the words missing and doubt the rest.

What to do: drop the quotation marks on paraphrases or replace them with the page's words; trim 02b's prose under the table (the dead-products paragraph can move to section 4); write "end of sale 1 May 2025, support to 1 May 2030" for Aurora.

## Contradictions

- 02a r128gain cell "no read-only flag" versus upstream `-d, --dry-run` "Do not write any tags, only show scan results" (fetch 1).
- 02b table VisLM2 "dialogue ... n/s" versus 02b section 3 "Dialogue gating named (VisLM ...)"; the live page carries no gating words (fetch 4).
- 02b table DRMeter "gate R128/A85" (the BS.1770 relative gate) versus 02b section 3 counting DRMeter for dialogue gating.
- 02b section 3 "Named presets (10 of 12)" versus a Presets column with six n/s and one unconfirmed.
- 02b Avid row: Pro Limiter "BS.1770-3/TP/LRA claims" versus "ships no loudness meter at all" in the same row.
- 02c "Every platform here has, cumple does not" versus four of nine named, and none of the three items in the Auphonic or Loudness Penalty rows.
- 02c section 3 crediting Vidchecker with A/V duration/sync versus a specs page with no such words (fetch 11).
- 02c section 3 "Dolby E/Atmos/ADM: 4 of 9" versus cells that name Dolby E, Dialog Intelligence and guard bands and never Atmos or ADM.
- 01-frame, RELATED.md and README naming "Dolby's DPLM" as a meter the studios name versus 02b finding no such live product and the profiles naming "Dolby Dialogue Intelligence".
- Between branches on capability claims for the same product: none found. The three branches cover disjoint products, so the cross-branch contradiction the frame worried about (one branch calling a product discontinued, another treating it as current) does not arise; the discontinued products (Aurora, RX Loudness Control, Dolby Media Meter) appear in one branch each.

## Unsupported claims

Ranked by how much 04 would lean on them.

1. 02a: r128gain "no read-only flag" (false, fetch 1).
2. 02b section 3: "Named presets (10 of 12)"; dialogue gating attributed to VisLM and DRMeter.
3. 02c section 3: the 4 of 9, 4 of 9, 3 of 9 and 2 of 9 counts, and "Misplaced channels" for Baton, none traceable to the quoted cells.
4. 02b Avid: "No native LUFS meter in Pro Tools"; "ships no loudness meter at all" (no source; 403).
5. 02b: the profile-grep results (Amazon names VisLM2; four profiles name Dolby Dialogue Intelligence). Outside my inputs; not verified here.
6. 02b: RX Loudness Control "Discontinued 2022-09-07" (search index; 403 for me too). The live iZotope page listing Loudness Control as an RX 12 module supports "folded into RX Advanced" but not the date.
7. 02b: Clarity M "$319" and "9 libraries" from a reseller; Adobe "BS.1770-3, ATSC A/85, EBU R128" via search; WLM Plus presets "per search only"; Audition Radar "licensed from TC Electronic, unconfirmed". All flagged by the branch; none meets the frame's cell rule.
8. 02b prose: Dolby Media Meter 2 "discontinued 2018-08-23" from production-expert.com, a third-party description RELATED.md's standard excludes. Flagged by the branch; kept out of the table.
9. 02c Auphonic presets "Spotify, YouTube, Apple Podcast, EBU R128": not on the cited page (fetch 16).
10. 02c AudioTools Server "1000+ templates", "REST API", "floating licenses": page unreachable at any URL the row allows me to infer (fetch 15).
11. 02c Baton row: from a 2021 datasheet hosted by SDVI, flagged as an unknown by the branch; not re-fetched here.
12. 02a bs1770gain "licence not confirmed here": a "not checked" by another name; the project's site is the row's own cited URL.
13. 02b DRMeter "2dB too loud": not on the MAAT pages fetched.

## Verdict

Ship with changes. The shape is right and most quoted cells survive a re-fetch, but two things must be redone before 04 runs: r128gain has to be measured with `-d` and its row rewritten (concern 1), and every count in the two ranking sections has to be recomputed from cells that actually contain the words, with Dolby E separated from Atmos/ADM (concern 2). Then the Avid row loses its unsourced negatives (3), 04 settles what "DPLM" refers to before it repeats RELATED.md's sentence (4), and 02b and 02c get real URLs per row so the loop's own gate can pass (5). Concerns 6 and 7 are worth doing in the same pass and block nothing.

Counts: Critical 2, High 3, Medium 2.
