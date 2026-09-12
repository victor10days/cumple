# 02b Research: commercial loudness meters and plugins

## 1. Inputs read

`01-frame.md`, `docs/RELATED.md`, `README.md` lines 427-497, ecc `market-research` and
`competitive-platform-analysis` SKILL.md files, and a direct
`grep -rn "Nugen\|Dolby\|VisLM\|DPLM\|Media Meter" src/cumple/specs/profiles/`. Vendor URLs below
read 2026-09-12.

cumple's specs: Amazon 2.0/5.1 name "Nugen Audio VisLM2" as reference meter outright. Netflix,
Amazon, Disney+, Apple TV name "Dolby Dialogue Intelligence" for gating, no SKU given. No profile
names LM-Correct, AMB, Youlean, Waves, MAAT, TC, Adobe, Avid or Steinberg.

`n/s` below means the fetched page does not say (never guessed).

## 2. Findings

| Product (vendor, kind, platforms) | Price/licence | Measures | Presets | Verdict/report | Batch/account | cumple lacks | it lacks | URL |
|---|---|---|---|---|---|---|---|---|
| VisLM2 (Nugen, plugin+standalone, Win/Mac) | "$449/£314/€384" | BS.1770 "rev 1-4"; true peak; Leq(m)/Leq(a); LRA/dialogue/Atmos n/s | 8 standards named, no count | "flags & alerts," not verdict; report n/s | n/s | named brand studios cite | no clause, no report, no diff | nugenaudio.com |
| LM-Correct 2 (Nugen, plugin+standalone, Win/Mac) | "$399/£279/€339" | BS.1770, no rev; TP via look-ahead limiter; LRA via DynApt; dialogue-gated optional; Leq(m) TASA | n/s | corrects, not verdict; report n/s | n/s | auto gain+TP fix | no named destinations, no diff | nugenaudio.com |
| AMB (Nugen, standalone batch, Windows only) | modules, no list price | BS.1770 1-4; Leq(m) TASA/SAWA; TP/LRA n/s | n/s | warnings, text/graphic logs, not verdict | "watched folders," up to 16 queues; account n/s | 16 watch queues | no Mac/Linux, no clause | nugenaudio.com |
| Dolby Atmos Renderer/Album Assembler (Dolby, standalone+mastering app) | Renderer: free trial; Assembler: "Requires iLok account" | Renderer BS.1770 K-weighted; v3.4 CSV/TXT export; Assembler n/s | n/s | Renderer exports measurements, no verdict; Assembler n/s | Renderer n/s; Assembler iLok-bound | real Atmos rendering | no clause; needs a host DAW | professional.dolby.com |
| RX Loudness Control (iZotope, was plugin+standalone) | Discontinued 2022-09-07 (own article title; 403'd, via index) | Archived listing cites BS.1770-2/3, EBU R128, ATSC A/85, OP-59, TR-B32, AGCOM | "extensive presets," no count live | n/s | n/s | nothing, withdrawn | ceased to exist; folded into RX Advanced | support.izotope.com |
| Youlean Loudness Meter (Youlean, plugin, Win/Mac) | Free; Pro "$29+tax, one-time" | "BS.1770-4"; true peak; LRA; dialogue/Leq(m) n/s | 19+ named platforms/standards | "only doing the analysis" (meter only); PDF/PNG/SVG, Pro only | account n/s; multi-computer personal use | preset breadth | no clause, no watch folder | youlean.co |
| WLM Plus (Waves, plugin) | MSRP "$149," sale "$29.99" | "true peak limiter"; rev/LRA/dialogue/Leq(m)/Atmos n/s (thin fetch) | YouTube/Spotify per search only, unconfirmed | n/s | n/s | nothing confirmed | page too thin to say | waves.com |
| DRMeter MkII (MAAT, plugin+standalone, Mac/Win) | "$129" perpetual, "$149 bundle" | BS.1770/R128 compliant; TP "disable (SPPM)"; LRA defined; gate R128/A85; Leq(m) n/s | 6 named (Spotify, iTunes/MfiT, YouTube, TIDAL, R128/A85, Pandora) | advisory only (e.g. "2dB too loud"), not verdict; no report | standalone only, no watcher; account n/s | nothing extra | no report, no batch, no clause | maat.digital |
| Clarity M (TC Electronic, hardware+plugin) | "$319" (reseller, no official price) | "ITU BS.1770-4"; TP "True-Peak Technology"; LRA/dialogue/Leq(m)/Atmos n/s | 9 libraries per reseller, not on official excerpt | n/s | hardware standalone | dedicated hardware display | no report, no batch, no MIT | tcelectronic.com |
| Premiere/Audition (Adobe, DAW/NLE feature, CC subscription) | Audition "US$22.99/mo Annual" | Match Loudness: BS.1770-3, ATSC A/85, EBU R128 (helpx 403'd, via search); Radar "licensed from TC Electronic," unconfirmed | n/s | corrects to target, no verdict | account-bound, CC login | nothing extra | no offline use, no MIT cost | adobe.com |
| Pro Tools/Pro Limiter (Avid, DAW+plugin) | avid.com 403 twice; unverified | No native LUFS meter in Pro Tools; Pro Limiter's BS.1770-3/TP/LRA claims unchecked (403) | n/s | n/s | subscription-bound | nothing confirmable | ships no loudness meter at all | avid.com |
| WaveLab, Loudness Meta Normalizer (Steinberg, DAW batch feature) | steinberg.net loaded no body text; unverified | "Top of Loudness Range," "Max Short-Term Loudness," Digital/True Peaks; rev/dialogue/Leq(m)/Atmos n/s | n/s | normalizes, not verdict | "exclusively...Batch Processor window"; account n/s | nothing extra | no clause, no cross-file watch | steinberg.help |

Waves and Avid thinned or blocked a direct read; those cells rest on a search index, marked above.
Two are dead: Dolby Media Meter 2 (discontinued 2018-08-23 per production-expert.com's report of
Nugen's own discount offer, a news report, not a vendor page or table source) and iZotope RX
Loudness Control (2022, per iZotope's own article title). No page names a live "Dolby Professional
Loudness Meter (DPLM)."

## 3. Options, ranked by how many of the twelve have it

1. Named presets (10 of 12); cumple's 39 graded, sourced destinations beat every one.
2. BS.1770 revision stated (7 of 12); true peak stated (7 of 12).
3. Dialogue gating named (VisLM, LM-Correct, DRMeter, plus four cumple profiles naming Dolby's own
   algorithm); cumple's heuristic gate is the weakest meter README admits.
4. A written report file (Youlean, AMB, Dolby Renderer; eight silent); cumple's HTML/PDF/JSON/CSV
   report beats most of this set.
5. Batch or watch-folder (AMB, WaveLab yes; DRMeter no; rest silent); cumple's watch folder is a
   real differentiator.
6. Atmos/ADM handling as a checked item, not a renderable format: none of the twelve states this,
   the one gap this table leaves open for cumple to close or decline.

## 4. Unknowns

- Whether "Dolby Professional Loudness Meter (DPLM)" is a live, separately named product.
- WLM Plus's DIAL mode, preset list, platforms (thin fetch; its PDF manual returned binary).
- Avid's pricing and Pro Limiter's claims (avid.com blocked WebFetch, 403 twice).
- Steinberg's WaveLab price and edition (steinberg.net returned a page shell, no body text).
- iZotope's exact discontinuation wording (support.izotope.com 403'd; read via search index).
- Whether DRMeter MkII is iLok or account bound; its page does not say.

## 5. Recommendation from this angle

Nugen VisLM2 is the one meter cumple's own spec grep found named by a studio (Amazon); page copy
claiming a competitive position should name VisLM2, not the wider commercial-meter category. This
angle's top roadmap item is closing or declining the Atmos/ADM QC gap: no vendor page here shows
cumple ahead there, and README already admits it.
