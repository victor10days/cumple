# 02c: file-based QC platforms and services

## 1. Inputs read

- `docs/graph-runs/2026-09-12-competitive-landscape/01-frame.md`
- `docs/RELATED.md` (whole file)
- `README.md` lines 427-497 (Honest limits, Related work)
- `~/.claude/skills/ecc/upstream/skills/market-research/SKILL.md`
- `~/.claude/skills/ecc/upstream/skills/competitive-platform-analysis/SKILL.md`
- Vendor pages, all read 2026-09-12 (full list under Src, section 2 below).
- Not readable: two Netflix partner-help articles redirect to a JS app (studiopartner.netflix.net) returning only a "Knowledge Hub" shell, per README:449.

## 2. Findings

"n/s" means the page was checked and says nothing, never a guess.

| Product (vendor) | Kind/sold/platforms | Audio checks it lists (quoted) | Presets | Verdicts/report/ops | Src | cumple lacks vs it | it lacks vs cumple |
|---|---|---|---|---|---|---|---|
| eFF / Engine (Emotion Systems) | Desktop app; price n/s; Windows/Mac/Linux | "True Peak, LRA, short term and momentary loudness, and legacy PPM"; "EBU R128, ATSC A85 and TR-B32"; Dolby E read/write | count n/s | Watch-folder auto-correct; "XML and PDF" reports | [1][2] | Dolby E read/write; watch-folder correction | clause+grade; stem-null diff; offline n/s |
| Vidchecker / Vantage (Telestream) | On-prem server; price n/s; Windows Server/10/11 | "channel mapping, tones, phase coherence...DialNorm...BS-1770, BLITS, GLITS"; Vantage: "ITU 1770-3, Dolby Dialog Intelligence, gated/dialog loudness" | count n/s | report format n/s | [3][4] | DialNorm, dialogue-intelligence gating, BLITS/GLITS | clause+grade; stem-null diff; price/offline n/s |
| Baton (Interra Systems) | Cloud+on-prem; subscription; Windows | "Kantar BVS Watermark...Dialnorm...Loudness compliance (ITU, EBU, CALM Act, OP59, ARIB)(BS.1770)...Phase detection...EAS tones...Nielsen & Cinavia...Teletrax watermark, speech-caption alignment" | DPP, iTunes, Netflix, CableLabs, ARD_ZDF | severity-graded; HTML/XML/PDF/Excel/JSON; SOAP/XML-RPC/REST | [5] | watermarks, language ID, Dolby-E guard-band, caption alignment | clause+grade; stem-null diff; offline no-account |
| Pulsar (Venera) | On-prem/VM, 4 editions incl. pay-per-use; Windows/VM | "Loudness (R128, CALM, OP-59, ARIB, Speech Gated)...Dialnorm, True Peak, Dual Mono...EAS tone, Phase Mismatch, Language ID, Mosquito Tone" | Netflix, DPP, Amazon Prime, ARD-ZDF, iTunes, CableLabs (6) | format n/s; watch folders; SOAP/Web Service API | [6] | speech-gated variant, dual-mono flag, mosquito/EAS tone, 6 templates | clause+grade; stem-null diff; free/offline tier |
| Aurora (Digimetrics, now Telestream) | Discontinued 1 May 2025; migrate to Qualify | "Silence, Drop-outs, Peaks, Average Levels (R128/ATSC/ARIB), Clipping, Snaps/Clicks/Pops, Phase Swaps, Hiss/Hum"; optional "Dolby E Guard Band Alignment" | CableLabs, iTunes, Netflix, ATSC, DVB, AS-02/10/11 (11) | web or PDF report; SOAP + legacy CeriTalk API | [7][8] | guard-band alignment, 11 presets, hiss/hum | no longer sold; stem-null diff; offline n/s |
| AudioTools Server (Minnetonka, Telos) | On-prem/cloud, floating licenses; Windows Server/VMware/AWS | "channel assignment detection, silence detection, phase analysis and correlation checks"; standard names n/s | 1000+ templates | format n/s; live watch folder; REST API | [9] | correlation checks; 1000+ presets | standard names n/s; clause+grade; stem-null diff; offline n/s |
| Auphonic | Cloud+API/CLI; free 2 hrs/month, paid beyond | "target loudness, true peak limit, MaxLRA"; noise/reverb reduction; clipping repair | Spotify, YouTube, Apple Podcast, EBU R128 | corrects, no verdict; watch folders/API/CLI/Zapier; account required | [10] | auto-correction; noise/reverb/de-ess repair | clause+grade; offline; stem-null diff |
| Loudness Penalty | Free browser tool; no upload; no account | per-platform dB penalty (e.g. "-2.4 on YouTube") | YouTube, Spotify, TIDAL, Apple Music, Amazon, Pandora, Deezer (7) | dB number only; export/batch/API n/s | [11] | 7-platform penalty comparison in one pass | clause+grade; true peak/silence/clipping/phase/2-pop; report file; batch; diff |
| Netflix NP3 / NPFP QC vendor conditions | Certification program, not software; portal-bound | "detect silence, audio labelling and dual mono"; 5-point spot check (first/last 2 min, 25/50/75%); WAV-conformance to spec; correct channel identifiers | n/a, destination is Netflix | vendor reports via Asset QC; format n/s | [12][13] | channel-identifier check; WAV-conformance check; 5-point protocol | human process; true peak/LRA/2-pop n/s here; not offline |

Src: [1] emotion-systems.com/products/eff [2] emotion-systems.com/engine-loudness-solutions [3] telestream.net/vidchecker/specs.htm [4] telestream.net/vantage/vantage-analysis.htm [5] sdvi.com/Baton_Datasheet-2021.pdf [6] veneratech.com/pulsar-automated-file-qc [7] telestream.net Aurora datasheet 2NW-60054-10 [8] telestream.net Aurora EOS-Announcement.pdf [9] telosalliance.com Minnetonka AudioTools Server [10] auphonic.com [11] loudnesspenalty.com [12] npfp.netflixstudios.com/program-conditions [13] partnerhelp.netflixstudios.com Welcome-to-Asset-QC

**Every platform here has, cumple does not:** codec/container conformance (eFF, Baton, Aurora, Netflix's WAV check) vs README:458-459; A/V duration/sync (Baton, Vidchecker, Aurora) vs README:460-461; Dolby E/dialogue metadata (eFF, Baton, Aurora, Vantage) vs README:456-457 ("no Dolby Atmos or ADM checks yet").

**cumple has, none list:** none of the 13 pages quote a destination's clause with a source grade (RELATED.md:9-10); none describe a stem-null test or diff in words (RELATED.md:12); none claim a fully offline, no-account, MIT run (RELATED.md:14-15); Baton and Auphonic are explicitly account-bound.

## 3. Options, ranked by how many of the 9 rows check it

1. Dolby E/Atmos/ADM metadata: 4 of 9 (eFF, Baton, Aurora, Vantage).
2. Codec/container conformance (AC-3, AAC, MXF): 4 of 9 (eFF, Baton, Aurora, Netflix).
3. A/V duration/sync: 3 of 9 (Baton, Vidchecker, Aurora).
4. Channel-identifier-vs-filename: 2 of 9 (Netflix; Baton's "Misplaced channels").
5. 2-pop/leader/slate: 0 of 9.

## 4. Unknowns

- Whether Vidchecker, Pulsar, Aurora or AudioTools Server check 2-pop/leader/slate; unfound, undenied.
- Pricing for Vidchecker, Vantage, AudioTools Server; withheld everywhere.
- Whether the two unreadable Netflix pages name true peak, LRA or 2-pop.
- Whether the 2021 Baton datasheet (hosted by SDVI, not Interra) still matches its current release.

## 5. Recommendation

Dolby E/Atmos metadata and codec/container conformance are cumple's widest gaps against these vendors, with A/V duration/sync next; a read-only Dolby E and MXF/AC-3 container check closes the most ground. Nothing here matches cumple's clause-with-grade or its stem-null diff, so keep that pairing rather than re-prove it.
