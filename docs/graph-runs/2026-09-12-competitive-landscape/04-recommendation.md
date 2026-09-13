# 04 Recommendation: competitive landscape for cumple

## 1. Recommendation

Build the Silero VAD optional backend (`cumple[vad]`) as a second dialogue-gate option, and add an optional local ffmpeg pass for delivery codec and container conformance (AAC, AC-3, MP3, MXF); both are buildable without Victor's accounts or hardware and close gaps the branches found widest. Change RELATED.md's and README's "Nugen VisLM and Dolby's DPLM are the commercial meters the studios name" to the section 5 replacement, since no live Dolby product named DPLM exists and the studios name an algorithm, not a meter.

## 2. Ranked roadmap

Profile counts are established only for row 1, from the one grep this run was scoped to; "n/e" below means no branch counted profile mentions for that row, so rank rests on comparable count and judgement, as the frame allows when a factor is zero.

| Rank | Item | Score | Comparables with it | Profiles | Buildable, no account/hardware |
|---|---|---|---|---|---|
| 1 | Dialogue gate, Dolby-Dialogue-Intelligence class (Silero VAD, `cumple[vad]`) | 18 (3x6) | 3/21: LM-Correct 2 "dialog-gated measure" (02b); Vantage "Dolby Dialog Intelligence", Pulsar "Speech Gated" (02c) | 6 (section 5): netflix x2, amazon x2, disney name "Dolby Dialogue Intelligence"; apple-tv same thing, no Dolby attribution | Yes, pip, offline |
| 2 | Codec/container conformance (AAC, AC-3, MP3, MXF, optional local ffmpeg) | n/c | 3/9 (Vidchecker, Pulsar, Netflix); 4/9 counting Baton | n/e | Yes, subprocess to local ffmpeg |
| 3 | Dolby E detection (presence, not decode) | n/c | 3/9 (eFF, Aurora, Vantage Pro) | n/e | Yes, presence only; decode is licensed |
| 4 | ADM/Atmos checks (chna, bed/object labels, per-track true peak; metadata only) | n/c | 2/9 (Baton, Vantage Pro); 0/12 in 02b | n/e | Yes, BWF/ADM XML parsing; rendering stays out of scope |
| 5 | Silence, dual mono, test tones, channel-identifier-vs-filename, mosquito tone | n/c | 3/9, 2/9, 2/9, 1/9, 1/9 respectively (all 02c) | n/e | Yes, read-only checks, small each |
| 6 | 2-pop, leader, slate detection (audio-only) | n/c | 1/9 (Baton "Slates," likely picture-adjacent, N3) | n/e | Partly, unproven audio-only value |
| 7 | A/V duration and sync | n/c | 1/9 (Baton) | n/e | No, needs the picture, out of scope |
| n/a | PyPI publishing | not a capability | n/a | n/a | No, needs Victor's PyPI account |

## 3. What cumple has that the comparables lack

A clause quoted with a grade behind every verdict: 0 of 21 comparables (02b's 12 "it lacks" cells; 02c's own line, "none of the 15 pages quote a clause with a grade"). A stem-null diff in words: 0 of 21, same sources. Offline, no account, MIT: 0 of 21 claim all three; several are account-bound (Baton, Auphonic, Adobe, Dolby Album Assembler's iLok). This is the honest count behind README's "cumple combines what none of them do together": 0 of 21, not "none."

## 4. Which 02a tools would earn a landing-page column later

None. 02a section 3 and the skeptic's N2 agree: ffmpeg-normalize measures through loudnorm (loudcheck's column), r128gain through ffmpeg's ebur128 filter (already that column), rsgain through libebur128 1.2.6 (already that column). All three landed in tolerance, showing the wrappers agree with engines already shown, not a new one. What would change this: bs1770gain running here with its own implementation (its macOS binary fails on a swresample mismatch today), loudness-scanner building against a patched input_ffmpeg.c, or a new CLI meter with its own BS.1770 code.

## 5. The Dolby DPLM sentence

The grep confirms six profiles name a dialogue-gating algorithm: netflix-2.0/5.1.yaml, amazon-2.0/5.1-package.yaml name "Dolby Dialogue Intelligence"; disney-plus-5.1.yaml names "Dolby's Dialogue Intelligence Algorithm"; apple-tv.yaml names "Dialogue Intelligence (or other speech-gating algorithm)" with no Dolby attribution. The two Amazon files separately name "Nugen Audio VisLM2" as the reference meter. No branch found a live Dolby page named DPLM. Interra Baton's datasheet lists "DPLM" once, unexpanded, among other audio checks.

Replacement sentence for RELATED.md's "Not compared" and README's "Related work," ready to paste:

"Nugen VisLM2 is the reference meter Amazon's own delivery specs name, and Dolby Dialogue Intelligence, the dialogue-gating algorithm Netflix, Amazon, Apple TV and Disney name in their loudness clauses, is licensed inside other vendors' tools such as Telestream Vantage and Venera Pulsar rather than sold as a Dolby meter; one QC vendor's datasheet (Interra Baton) prints DPLM as a check without defining it, and no live Dolby product by that name was found."

## 6. Rejected options and why

Every frame candidate is ranked in section 2. Other items branches surfaced, not ranked: watermark detection (Baton only, needs an account); auto-correction or repair (Auphonic only, outside cumple's diff-and-gain-only scope); preset breadth (cumple ships 39 named destinations, a strength not a gap); phase mismatch, correlation checks, hiss/hum, clipping, EAS tone (one vendor each, low signal, deferred); report and batch/watch-folder breadth (cumple already has both, section 3). bs1770gain and loudness-scanner are rejected as landing-page candidates per section 4, not for lacking value but because neither runs here today.

## 7. Skeptic findings and disposition

1. r128gain false "no read-only flag": addressed, `-d` confirmed with shasum proof.
2. Ranking counts not traceable to cells: addressed, section 3 counts now match the cells.
3. Avid row's unsourced negatives: addressed, row quotes the Pro Limiter guide verbatim.
4. Dolby DPLM premise: addressed by section 5's rewrite; the fact (no live DPLM product) is sourced, not asserted.
5. Rows without fetchable URLs: addressed, both branches carry a resolvable URL per row.
6. 02a's self-imposed limits: addressed, rsgain and bs1770gain both tried, results or failures recorded.
7. Word cap and paraphrase-in-quotes: addressed, 02b under 900 words, quotes match cited pages.
N1 (ffmpeg 8.0 to 9.0.1 relink): Victor's decision. Options: (a) restore the pin by relinking libvpx 1.15.2 and ffmpeg 8.0 by hand, or (b) accept 9.0.1 and let the report scripts re-pin RELATED.md and BENCHMARK.md. Recommend (a): pinned figures should change only through the report scripts, and restoring the default is smaller than re-pinning published numbers over a dependency bump. No action taken; named here for Victor to choose.
N2 (r128gain's independent-engine claim): critical, addressed, matching the fix the skeptic asked for.
N3 (Baton's "Slates" and "DPLM" missing): addressed, both now quoted, "SADM" restored.
N4 (small residues): mostly addressed; one accepted as low risk, bs1770gain's licence cell still cites an unreachable site, harmless since it does not run here.

## 8. Open risks

The score formula (comparables x profiles) is computable only for row 1; every other row rests on comparable count and judgement, since no branch counted profile mentions for Atmos, codec, Dolby E, 2-pop or A/V duration. Several 02b/02c cells rest on reseller pages, search indexes, or thin fetches (Clarity M price, WLM Plus presets, WaveLab, RX Loudness Control's date) and could be stale. Dolby E presence detection has no licensing review yet. N1's ffmpeg state is unresolved and could affect any CI run touching ffmpeg until Victor picks an option.

## 9. Next action for Victor

Confirm the two build items (Silero VAD dialogue-gate backend, optional-ffmpeg codec and container check) and choose between restoring ffmpeg to 8.0 or accepting 9.0.1 and re-pinning the benchmark, before either build touches CI.
