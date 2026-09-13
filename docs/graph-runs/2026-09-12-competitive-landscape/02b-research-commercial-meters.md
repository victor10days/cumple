# 02b Research: commercial loudness meters and plugins

## 1. Inputs read

`01-frame.md`, `docs/RELATED.md`, `README.md` lines 427-497, ecc
`market-research`/`competitive-platform-analysis` SKILL.md, plus a direct
`grep -rn "Nugen\|Dolby\|VisLM\|DPLM\|Media Meter" src/cumple/specs/profiles/`. Vendor URLs below
read 2026-09-12.

cumple's specs quote: `src/cumple/specs/profiles/amazon-2.0-package.yaml:52` and
`amazon-5.1-package.yaml:55` both read "Names Nugen Audio VisLM2 as the reference meter."
`netflix-2.0.yaml:13`, `netflix-5.1.yaml:13`, `amazon-2.0-package.yaml:12` and
`amazon-5.1-package.yaml:12` each read "measures with Dolby Dialogue Intelligence." Disney
(`disney-plus-5.1.yaml:34`) reads "Dolby's Dialogue Intelligence Algorithm."

`n/s` = page does not say (never guessed).

## 2. Findings

| Product (vendor, kind, platforms) | Price/licence | Measures | Presets | Verdict/report | Batch/account | cumple lacks | it lacks | URL |
|---|---|---|---|---|---|---|---|---|
| VisLM2 (Nugen, plugin+standalone, Win/Mac) | "$449/£314/€384" | BS.1770 "revisions 1, 2, 3 and 4"; true-peak; Leq(m)/Leq(a); LRA/dialogue/Atmos n/s | 8 standards named, no-count | "flags & alerts," not-verdict; report n/s | n/s | named-brand-studios-cite | no clause/report/diff | https://nugenaudio.com/vislm/ |
| LM-Correct 2 (Nugen, plugin+standalone, Win/Mac) | "$399/£279/€339" | BS.1770, no-rev; TP look-ahead-limiter; LRA DynApt-option; "dialog-gated measure" optional; Leq(m) TASA | n/s | corrects, not-verdict; report n/s | n/s | auto-gain+TP-fix | no named-destinations/diff | https://nugenaudio.com/lm-correct/ |
| AMB (Nugen, standalone-batch, Windows-only) | modules, no-list-price | BS.1770 1-4; Leq(m) TASA/SAWA; TP/LRA n/s | n/s | warnings, text/graphic-logs, not-verdict | "automatically watching output folders," "up to a total of 16" queues; account n/s | 16-watch-queues | no Mac/Linux/clause | https://nugenaudio.com/amb/ |
| Dolby Atmos Renderer / Album Assembler (Dolby) | Renderer: free trial; Assembler: "Requires iLok account" | Renderer BS.1770 K-weighted; CSV/TXT-export; Assembler n/s | n/s | Renderer exports data, no-verdict; Assembler n/s | Renderer n/s; Assembler iLok-bound | real-Atmos-rendering | no clause; needs host DAW | https://professional.dolby.com/product/dolby-atmos-content-creation/dolby-atmos-renderer/ and .../dolby-atmos-album-assembler/ |
| RX Loudness Control (iZotope, plugin+standalone) | Discontinued 2022-09-07 (article title; via search index, page not fetched) | Archived listing cites BS.1770-2/3, EBU R128, ATSC A/85, OP-59, TR-B32, AGCOM | "extensive presets," no-count | n/s | n/s | nothing, withdrawn | folded into RX Advanced | https://support.izotope.com/hc/en-us/articles/47669776557581-RX-Loudness-Control-Has-Been-Discontinued |
| Youlean Loudness Meter (Youlean, plugin, Win/Mac) | Free; Pro "$29+tax, one-time" | "BS.1770-4"; true-peak; LRA; dialogue/Leq(m) n/s | 19+ named platforms/standards | "only doing the analysis"; PDF/PNG/SVG-export, Pro-only | account n/s; multi-computer-personal-use | preset-breadth | no clause/watch-folder | https://youlean.co/youlean-loudness-meter/ |
| WLM Plus (Waves, plugin) | MSRP "$149," sale "$29.99" | "true peak limiter"; rev/LRA/dialogue/Leq(m)/Atmos n/s (thin-fetch) | YouTube/Spotify: via search index, page not fetched | n/s | n/s | nothing-confirmed | too-thin-to-say | https://www.waves.com/plugins/wlm-loudness-meter |
| DRMeter MkII (MAAT, plugin+standalone, Mac/Win) | "$129" perpetual, "$149 bundle" | BS.1770/R128; TP "disable (SPPM)"; LRA; "R/128 / A/85 Gate" (relative, not dialogue); Leq(m) n/s | 6 named (Spotify, iTunes/MfiT, YouTube, TIDAL, R128/A85, Pandora) | "difference in LU needed to match user defined target loudness"; no report | standalone-only; account n/s | nothing-extra | no report/batch/clause | https://www.maat.digital/drm2/ |
| Clarity M (TC Electronic, hardware+plugin) | "$319" (reseller, no official price) | "ITU BS.1770-4"; TP "True-Peak Technology"; LRA/dialogue/Leq(m)/Atmos n/s | 9 libraries: via search index, page not fetched | n/s | hardware-standalone | dedicated-hardware-display | no report/batch/MIT | https://www.tcelectronic.com/en/products/0842-AAA |
| Premiere/Audition (Adobe, DAW/NLE-feature, CC-subscription) | Audition "US$22.99/mo Annual" | Match Loudness: BS.1770-3, ATSC A/85, EBU R128: via search index, page not fetched; Radar "licensed from TC Electronic," third-party | n/s | corrects-to-target, no-verdict | account-bound, CC-login | nothing-extra | no offline-use/MIT-cost | https://www.adobe.com/products/audition.html |
| Pro Tools/Pro Limiter (Avid, DAW+AAX-plugin, Win/Mac) | avid.com 403 twice; guide: no price | "complies with the ITU-R BS.1770-3 loudness metering standard" (true peak, integrated loudness, loudness range); dialogue/Leq(m)/Atmos n/s | n/s | numeric-displays-only; no-report | n/s; subscription-bound | nothing-extra | no named-destinations/clause/report | https://resources.avid.com/SupportFiles/PT/Audio_Plug-Ins_Guide_2018.1.pdf |
| WaveLab, Loudness Meta Normalizer (Steinberg, DAW-batch-feature) | steinberg.net: no body text; unverified | "Top of Loudness Range," "Maximum Short-Term Loudness," Digital/True Peaks; rev/dialogue/Leq(m)/Atmos n/s | n/s | normalizes, not-verdict | "exclusively...Batch Processor window"; account n/s | nothing-extra | no clause/cross-file-watch | https://www.steinberg.help/r/wavelab-pro/wavelabplugref/12.0/en/_shared/topics/plug_ref/loudness_meta_normalizer_r.html |

## 3. Options, ranked by how many of the twelve table rows support it

1. BS.1770 revision named: 7/12 (VisLM2, AMB, RX Loudness, Youlean, Clarity M, Adobe, Avid); true
   peak: 8/12.
2. Named presets from a vendor's own page: 3/12 (VisLM2, Youlean, DRMeter); six n/s, one archived,
   two search-index-only.
3. Dialogue gating on a vendor's own page: 1/12, LM-Correct 2's "dialog-gated measure." VisLM2
   says dialogue n/s; DRMeter's gate is BS.1770's relative gate, not dialogue: both excluded.
4. A written report file: 3/12 (AMB logs, Dolby Renderer CSV/TXT, Youlean PDF/PNG/SVG).
5. Batch or watch-folder: 2/12 (AMB, WaveLab); DRMeter states it lacks one.
6. Atmos/ADM as a checked QC item: 0/12, the one gap this table leaves open for cumple.

## 4. Unknowns

- Live Dolby pages: Atmos Renderer, Album Assembler (fetched, above). Dolby Media Meter 2
  discontinued 2018-08-23 (production-expert.com, third-party). No live "Dolby Professional
  Loudness Meter (DPLM)" page found. iZotope RX Loudness Control discontinued 2022 (own article
  title, search index).
- WLM Plus's DIAL mode, preset list, platforms (thin fetch; PDF manual returned binary).
- Steinberg's WaveLab price/edition (steinberg.net: page shell, no body text).
- Whether DRMeter MkII is iLok/account-bound; page silent.
- Whether Pro Tools has a loudness meter without Pro Limiter.

## 5. Recommendation from this angle

Nugen VisLM2 is the one meter cumple's own spec grep found named by a studio (Amazon); page copy
claiming a competitive position should name VisLM2, not the wider category. This angle's top
roadmap item: close or decline the Atmos/ADM QC gap, since no page here shows cumple ahead, and
README already admits it.
