# 02c: file-based QC platforms and services

## 1. Inputs read

- `docs/graph-runs/2026-09-12-competitive-landscape/01-frame.md`
- `docs/RELATED.md` (whole file)
- `README.md` lines 427-497 (Honest limits, Related work)
- `~/.claude/skills/ecc/upstream/skills/market-research/SKILL.md`
- `~/.claude/skills/ecc/upstream/skills/competitive-platform-analysis/SKILL.md`
- Vendor pages, read 2026-09-12 (list under Src, section 2).
- Not readable: two Netflix partner-help articles redirect to a JS app, per README:449. telestream.com's Qualify-for-Vantage PDF 404s; those claims instead come from vantage-analysis.htm (found on a closer scan).

## 2. Findings

"n/s": page checked, says nothing, never a guess.

| Product (vendor) | Kind/sold/platforms | Audio checks it lists (quoted) | Presets | Verdicts/report/ops | Src | cumple lacks vs it | it lacks vs cumple |
|---|---|---|---|---|---|---|---|
| eFF / Engine (Emotion Systems) | Desktop app; price n/s; Windows/Mac/Linux | "True Peak, LRA, short term and momentary loudness, and legacy PPM"; "EBU R128, ATSC A85 and TR-B32"; reads/writes "Dolby E encoded channels" | count n/s | Watch-folder auto-correct; "XML and PDF" reports | [1][2] | Dolby E read/write; watch-folder correction | clause+grade; stem-null diff; offline n/s |
| Vidchecker / Vantage (Telestream) | On-prem server; Vantage: Analysis/Analysis Pro tiers, price n/s; Windows Server/10/11 | "audio codec...phase coherence between channels...DialNorm...BS-1770, BLITS, GLITS"; Vantage: "ITU 1770-3...Dolby Dialog Intelligence"; Pro tier: "Dolby E Detection", "Dolby Atmos Loudness Measurement" | count n/s | report format n/s | [3][4] | DialNorm, dialogue-intelligence gating, BLITS/GLITS, Pro-tier Atmos/Dolby E | clause+grade; stem-null diff; price/offline n/s |
| Baton (Interra Systems) | Cloud+on-prem; subscription; Windows; datasheet is SDVI-hosted, not Interra's | "Dialnorm...Loudness compliance (ITU, EBU, CALM Act, OP59, ARIB)...Misplaced channels, Phase detection...Teletrax watermark, speech-caption alignment"; Container Checks: "Audio/Video duration mismatch", "Synchronization"; current page: "Dolby Atmos, BW64, 24-bit LPCM" | DPP, iTunes, Netflix, CableLabs, ARD_ZDF | severity-graded; HTML/XML/PDF/Excel/JSON; SOAP/XML-RPC/REST | [5][6] | watermarks, Misplaced-channel check, A/V duration/sync, Atmos support | clause+grade; stem-null diff; offline no-account |
| Pulsar (Venera) | On-prem/VM, 4 editions incl. pay-per-use; Windows/VM | "Audio Codec, Sampling Frequency...Dialnorm, True Peak, Dual Mono...EAS tone, Phase Mismatch, Language ID, Mosquito Tone" | Netflix, DPP, Amazon Prime, ARD-ZDF, iTunes, CableLabs (6) | format n/s; watch folders; SOAP/Web Service API | [7] | codec check, dual-mono flag, mosquito/EAS tone, 6 templates | clause+grade; stem-null diff; free/offline tier |
| Aurora (Digimetrics, now Telestream) | End of sale 1 May 2025, support to 1 May 2030; migrate to Qualify | "Silence, Drop-outs, Peaks, Average Levels (R128/ATSC/ARIB), Clipping, Snaps/Clicks/Pops, Phase Swaps, Hiss/Hum"; optional "Dolby E Guard Band Alignment" | CableLabs, iTunes, Netflix, ATSC, DVB, AS-02/10/11 (11) | web or PDF report; SOAP + legacy CeriTalk API | [8][9] | guard-band alignment, 11 presets, hiss/hum | winding down; stem-null diff; offline n/s |
| AudioTools Server (Minnetonka, Telos) | On-prem/cloud, "floating licenses"; Windows Server/VMware/AWS | "channel assignment detection, silence detection, phase analysis and correlation checks"; standard names n/s | "1000+ Pre-Configured Templates" | format n/s; live watch folder; "a modern REST API" | [10] | correlation checks; 1000+ presets | standard names n/s; clause+grade; stem-null diff; offline n/s |
| Auphonic | Cloud+API/CLI; free 2 hrs/month, paid beyond | "target loudness, true peak limit, MaxLRA"; noise/reverb reduction; clipping repair | "EBU R128" (-23 LUFS), "ATSC A/85", Netflix LRA 4-18 LU | corrects, no verdict; watch folders/API/CLI/Zapier; account required | [11][12] | auto-correction; noise/reverb/de-ess repair | clause+grade; offline; stem-null diff |
| Loudness Penalty | Free browser tool; no upload; no account | per-platform dB penalty (e.g. "-2.4 on YouTube") | YouTube, Spotify, TIDAL, Apple, Apple Legacy, Amazon, Pandora, Deezer (8) | dB number only; export/batch/API n/s | [13] | 8-platform penalty comparison in one pass | clause+grade; true peak/silence/clipping/phase/2-pop; report file; batch; diff |
| Netflix NP3 / NPFP QC vendor conditions | Certification program, not software; portal-bound | "detect silence, audio labelling and dual mono"; 5-point spot check (first/last 2 min, 25/50/75%); WAV-conformance; correct channel identifiers | n/a, destination is Netflix | vendor reports via Asset QC; format n/s | [14][15] | channel-identifier check; WAV-conformance check; 5-point protocol | human process; true peak/LRA/2-pop n/s here; not offline |

Src: [1] emotion-systems.com/products/eff [2] emotion-systems.com/engine-loudness-solutions [3] telestream.net/vidchecker/specs.htm [4] telestream.net/vantage/vantage-analysis.htm [5] sdvi.com/wp-content/uploads/2021/11/Baton_Datasheet-2021.pdf [6] interrasystems.com/file-based-qc.php [7] veneratech.com/pulsar-automated-file-qc/ [8] telestream.net/pdfs/datasheets/Aurora-...-2NW6005410.pdf [9] telestream.net/pdfs/support/Telestream_Aurora_EOS-Announcement.pdf [10] telosalliance.com/file-based-audio-processing/audio-automation-for-enterprise/minnetonka-audiotools-server [11] auphonic.com/ [12] auphonic.com/help/web/preset.html [13] loudnesspenalty.com/ [14] npfp.netflixstudios.com/program-conditions [15] partnerhelp.netflixstudios.com/hc/en-us/articles/360057627193-Welcome-to-Asset-QC

Some, not most, check cumple's gaps: Dolby E (3/9: eFF, Aurora, Vantage Pro); Atmos/ADM (2/9: Vantage Pro, Baton); codec/container (3/9: Vidchecker, Pulsar, Netflix); A/V duration/sync (1/9: Baton). Auphonic and Loudness Penalty have none of these four.

**cumple has, none list:** none of the 15 pages quote a clause with a grade (RELATED.md:9-10); none describe a stem-null test or word-diff (RELATED.md:12); none claim offline, no-account, MIT (RELATED.md:14-15); Baton, Auphonic are account-bound.

## 3. Options, ranked by how many of the 9 rows check it

1. Codec/container conformance: 3 of 9.
2. Dolby E metadata: 3 of 9.
3. Atmos/ADM metadata: 2 of 9.
4. Channel-identifier-vs-filename: 2 of 9 (Netflix, Baton).
5. A/V duration/sync: 1 of 9 (Baton).
6. 2-pop/leader/slate: 0 of 9.

## 4. Unknowns

- Whether Vidchecker, Pulsar, Aurora or AudioTools check 2-pop/leader/slate; unfound, undenied.
- Pricing for Vidchecker, Vantage tiers, AudioTools; withheld everywhere.
- Whether the two unreadable Netflix pages name true peak, LRA or 2-pop.
- Whether Baton's 2021 SDVI datasheet still matches checks on its current page.

## 5. Recommendation

Codec/container and Dolby E metadata are cumple's widest gaps (3 of 9 each); Atmos/ADM is next (2 of 9). A read-only Dolby E/MXF/AC-3 check closes the most ground; nothing matches cumple's clause-with-grade or stem-null diff, so keep it.
