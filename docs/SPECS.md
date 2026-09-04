# Destinations known to cumple 0.1.0

Generated 2026-09-04 from `src/cumple/specs/profiles/*.yaml`. Every number is traceable to the sources listed under each destination, and the grade says how good that trace is:

- **READ**: primary document read directly
- **SE**: primary page exists (JavaScript app); values recovered via search extraction
- **GATED**: partner portal or NDA; values from secondary summaries
- **SECONDARY**: taken from another standards body's summary table
- **COMMUNITY**: platform publishes nothing; third-party measurement
- **TOOL_DEFAULT**: source is silent; the tool's own default

An asterisk after a grade means some value is the tool's own default where the source is silent.

## Matrix

| id | destination | family | loudness | peak | other rules | grade |
|---|---|---|---|---|---|---|
| `acx` | ACX / Audible audiobook | audiobook | -23 to -18 dBFS RMS | -3 dBFS sample | 44.1 kHz, RMS + noise floor | READ |
| `arib-tr-b32` | ARIB TR-B32 (Japan television) | broadcast | -24 ±1 integrated | -1 dBTP | 48 kHz, 16/24-bit | SECONDARY |
| `atsc-a85-2026` | ATSC A/85:2026 television (US) | broadcast | -24 ±2 dialogue-gated or -24 ±2 integrated (speech < 15 %) | -2 dBTP | 48 kHz, 16/24-bit | READ |
| `dpp-as11` | UK DPP / AS-11 programme delivery | broadcast | -23 ±0.5 integrated | -1 dBTP | 48 kHz, 24-bit, mono fold | READ |
| `ebu-r128` | EBU R 128 broadcast programme | broadcast | -23 ±1 integrated | -1 dBTP | 48 kHz, 16/24-bit, bext truth | READ* |
| `ebu-r128-s1-short` | EBU R 128 s1 short-form (adverts, promos) | broadcast | -23 ±0.2 integrated | -1 dBTP | max S ≤ -18, 48 kHz, 16/24-bit, bext truth | READ |
| `nbcu-commercial` | NBCUniversal linear commercial | broadcast | -24 ±2 integrated | -2 dBTP | 48 kHz, 16/24-bit | READ |
| `op-59` | Free TV Australia OP-59 | broadcast | -24 ±1 integrated | -2 dBTP | 48 kHz, 16/24-bit | READ |
| `dcp-5.1` | DCP 5.1 audio (ISDCF channel order) | cinema | no loudness target | none stated | 48/96 kHz, 24-bit | READ |
| `sawa-ad` | Cinema advertising (SAWA) | cinema | ≤ 82 dB Leq(m) | none stated | 48/96 kHz, 24-bit | READ |
| `tasa-trailer` | Cinema trailer (TASA) | cinema | ≤ 85 dB Leq(m) | none stated | 48/96 kHz, 24-bit | READ |
| `aes-td1008-music` | AES TD1008 streaming, music | music | -16 ±0.2 integrated | -1 dBTP |  | READ |
| `apple-digital-masters` | Apple Digital Masters | music | no loudness target | -1 dBTP | 44.1/48/88.2/96/176.4/192 kHz, 24-bit | READ* |
| `soundcloud` | SoundCloud master | music | -14 ±1 integrated | -1 dBTP | 44.1/48/88.2/96 kHz, 16/24-bit | READ* |
| `spotify` | Spotify music master | music | -14 ±1 integrated | -1 dBTP | 44.1/48/88.2/96 kHz, 16/24-bit | READ* |
| `youtube` | YouTube (community-measured) | music | -14 ±1 integrated | -1 dBTP |  | COMMUNITY |
| `apple-podcasts` | Apple Podcasts | podcast | -16 ±1 integrated | -1 dBTP | 44.1/48/88.2/96/176.4/192 kHz | READ |
| `aes-td1008-speech` | AES TD1008 streaming, speech-anchored | streaming | -19 to -17 dialogue-gated | -1 dBTP |  | READ |
| `amazon-5.1-package` | Amazon MGM Studios 5.1 (discrete mono files) | streaming | -27 ±2 dialogue-gated | -2 dBTP | 48 kHz, 24-bit, discrete, stems sum | GATED* |
| `amazon-pvd` | Prime Video Direct mezzanine audio | streaming | -24 ±2 integrated | -2 dBTP | 48 kHz, 16/24-bit | READ |
| `apple-tv` | Apple TV+ / Apple TV app | streaming | -31 to -10 dialogue-gated; -31 to -5 integrated (speech < 15 %) | -1 dBTP | 48 kHz, 24-bit, LFE band | READ* |
| `atsc-a85-streaming` | ATSC A/85:2026 Annex L streaming range | streaming | -27 to -23 dialogue-gated or -27 to -23 integrated (speech < 15 %) | -2 dBTP | 48 kHz, 16/24-bit | READ |
| `disney-plus` | Disney+ near-field mix | streaming | -27 ±2 dialogue-gated or -24 ±2 integrated (speech < 15 %) | -2 dBTP | 48 kHz, 24-bit | SE* |
| `hulu-2018` | Hulu content partner guidebook (2018, stale) | streaming | -24 ±2 integrated | -2 dBFS sample | 48 kHz, 16/24-bit, interleaved | READ |
| `max-wbd` | Warner Bros. Discovery / Max component audio | streaming | -24 ±2 dialogue-gated or -24 ±2 integrated | -2 dBTP | LRA ≤ 20 LU, 48 kHz, 24-bit, padding | READ |
| `netflix-2.0` | Netflix stereo (2.0) printmaster | streaming | -27 ±2 dialogue-gated or -24 ±2 integrated (speech < 15 %) | -2 dBTP | 48 kHz, 24-bit, stems sum | SE* |
| `netflix-5.1` | Netflix 5.1 near-field printmaster | streaming | -27 ±2 dialogue-gated or -24 ±2 integrated (speech < 15 %) | -2 dBTP | 48 kHz, 24-bit, stems sum, LFE band | SE* |
| `paramount-pluto` | Paramount Global content delivery (Pluto TV ingest) | streaming | -24 ±2 integrated | -2 dBFS sample | 48/96 kHz, 16/24-bit | READ* |

## ACX / Audible audiobook (`acx`)

ACX Audio Submission Requirements, the one major spec that uses RMS instead of BS.1770. RMS between -23 and -18 dBFS, peaks at or below -3 dBFS, noise floor at or below -60 dBFS RMS, 44.1 kHz, 192 kbps CBR MP3, room tone at head and tail, at most 120 minutes per file.

In the source's words (paraphrased; verbatim quotes pending):

- `rms.level`: Measure between -23 dB and -18 dB RMS. (paraphrase of ACX Audio Submission Requirements)
- `peak.sample`: Peak values no higher than -3 dB. (paraphrase of ACX Audio Submission Requirements)
- `rms.noise_floor`: Noise floor no higher than -60 dB RMS. (paraphrase of ACX Audio Submission Requirements)
- `duration.max`: Each file is a single chapter or section and no longer than 120 minutes; 0.5 to 1 second of room tone at the head and 1 to 5 seconds at the tail. (paraphrase of ACX Audio Submission Requirements)

Sources:

- **READ** (primary) ACX Audio Submission Requirements · ACX (Audible) · <https://www.acx.com/help/acx-audio-submission-requirements/200013520> · retrieved 2026-09-03. The live page redirected during research; values are from the ACX document text.

## ARIB TR-B32 (Japan television) (`arib-tr-b32`)

Japanese television loudness. -24 LKFS ±1 LU, -1 dBTP, BS.1770-2 gating. The ARIB text is paid and in Japanese; the numbers here come from the AES TD1006 regional table.

Loudness rules:

- -24 ±1 LUFS integrated, BS.1770-4

In the source's words (paraphrased; verbatim quotes pending):

- `loudness.integrated`: Target -24 LKFS, tolerance ±1 LU, measured with BS.1770-2 gating. (from the AES TD1006 regional table, not the ARIB text)
- `peak.true`: Maximum true peak -1 dBTP. (from the AES TD1006 regional table)

Sources:

- **SECONDARY** (primary) ARIB TR-B32: Operational Guidelines for Loudness of Digital Television Programmes · ARIB · <https://www.arib.or.jp/english/std_tr/broadcasting/desc/tr-b32.html> · retrieved 2026-09-03. Values taken from AES TD1006 (Oct 2017) Table 1, not read from the ARIB document.
- **READ** (supporting) AES TD1006: Recommendations for loudness of audio for OTT and OVD, AESTD1006.1.17-10 (October 2017) · AES · <https://aes2.org/wp-content/uploads/2024/01/AESTD1006_1_17_10.pdf> · retrieved 2026-09-03

## ATSC A/85:2026 television (US) (`atsc-a85-2026`)

US television loudness under the CALM Act. -24 LKFS with about ±2 dB tolerance; long-form content is measured as dialogue level with BS.1770-1 and a dialogue gate, short-form as the full mix with BS.1770-3 or later; true peak below -2 dBTP.

Loudness rules (any one applicable rule may pass):

- -24 ±2 LKFS dialogue-gated, BS.1770-1, if speech ≥ 15 % · Long-form content: dialogue level, BS.1770-1 without the relative gate, plus a dialogue-gating algorithm, over the entire duration.
- -24 ±2 LUFS integrated, BS.1770-4, if speech < 15 % · Full-program mix only when the content contains no dialogue whatsoever (A/85 §5.2.4); short-form content uses this method too.

In the source's words:

- `loudness.dialogue_gated`: It is vital that the average Dialogue Level be measured and reported as the Loudness for Long-form Content. This should be performed using BS.1770-1 (i.e., without the relative-level gate added in subsequent versions), along with a Dialogue-Gating algorithm, and measured over the entire duration (not act by act) of the Content's composite mix.
- `loudness.integrated`: For delivery or exchange of Content without metadata (and where there is no prior arrangement by the parties regarding Loudness), the Target Loudness value should be –24 LKFS. Measurement tolerance of up to approximately ±2 dB around this value is anticipated, due to measurement variations. Content Loudness should not be targeted to the high or low side of this tolerance.
- `peak.true`: The True Peak level should be kept below –2 dBTP in order to provide headroom to avoid potential clipping due to downstream processing (such as audio coding used in delivery). Minor measurement tolerance of up to approximately ±0.5 dBTP around this value is anticipated, due to meter variations, and is acceptable.

Sources:

- **READ** (primary) ATSC A/85: Techniques for Establishing and Maintaining Audio Loudness for Digital Television, A/85:2026-07 (8 July 2026) · ATSC · <https://www.atsc.org/wp-content/uploads/2026/07/A85-2026-07.pdf> · retrieved 2026-09-03

## UK DPP / AS-11 programme delivery (`dpp-as11`)

UK broadcaster file delivery (DPP, restated in Channel 4's v5.2 spec). -23.0 LUFS ±0.5 LU for non-live programmes (±1.0 live), true peak recommended below -3 dBTP and failed above -1 dBTP, LRA guide 18 LU, stereo must fold to mono, 48 kHz / 24-bit PCM.

Loudness rules:

- -23 ±0.5 LUFS integrated, BS.1770-4 · ±1.0 LU applies to live programmes.

In the source's words (paraphrased; verbatim quotes pending):

- `loudness.integrated`: Programme loudness -23.0 LUFS, tolerance ±0.5 LU for non-live and ±1.0 LU for live programmes, EBU I mode over the whole programme, LFE excluded. (paraphrase of the Channel 4 restatement of the DPP spec)
- `peak.true`: Maximum true peak recommended -3 dBTP; a programme with true peaks above -1 dBTP fails. (paraphrase)
- `dynamics.lra`: Loudness range guide of 18 LU, and no more than 6 LU for speech in factual programmes. (paraphrase)
- `mono.compat`: Stereo audio must be mono compatible; phase must fold down. (paraphrase)
- `format.sample_rate`: PCM at 48 kHz, 24-bit, one channel per MXF audio track. (paraphrase)

Sources:

- **READ** (primary) Programme Delivery Specification File: DPP / Channel 4, v5.2 (2022) · Channel 4 (DPP member) · <https://assets-corporate.channel4.com/_flysystem/s3/documents/2023-03/ProgrammeDeliverySpecificationFile_DPP-Channel4_v5.2.pdf> · retrieved 2026-09-03. thedpp.com is login-gated; Channel 4 publishes the DPP figures.
- **READ** (supporting) AMWA AS-11 UK DPP HD · AMWA · <https://amwa-tv.github.io/AS-11_UK_DPP_HD/AMWA_AS_11_UK_DPP_HD.html> · retrieved 2026-09-03

## EBU R 128 broadcast programme (`ebu-r128`)

European broadcast loudness. -23.0 LUFS integrated, -1 dBTP. The reference most other specs are compared against.

Loudness rules:

- -23 ±1 LUFS integrated, BS.1770-4 · R 128 permits ±1.0 LU where the target is not practically attainable (live); for QC workflows it allows ±0.2 LU for measurement error. cumple passes at ±1.0 and reports the ±0.2 window in the note.

In the source's words:

- `loudness.integrated`: that the Programme Loudness Level shall be normalised to a Target Level of −23.0 LUFS. Where attaining the Target Level is not achievable practically (for example, live programmes), a tolerance of ±1.0 LU is permitted. A broadcaster should ensure that a deviation from the Target Level towards the limits of the tolerance does not become standard practice; [...] that for the implementation of Loudness workflows (for example, in Quality Control environments) a tolerance of ±0.2 LU is allowed in order to take account of measurement errors
- `loudness.method`: that the measurement shall be made with a loudness meter compliant with ITU-R BS.1770 (including the level-gating method described in equation (7)) and EBU Tech 3341
- `peak.true`: that the True Peak Level of a programme shall not exceed −1 dBTP (dB True Peak) during production (linear audio), measured with a meter compliant with ITU-R BS.1770 and EBU Tech 3341. The measurement tolerance is ±0.3 dB (for signals with a bandwidth limited to 20 kHz).
- `metadata.bext_loudness`: LoudnessValue: A 16-bit signed integer, equal to round(100x the Integrated Loudness Value of the file in LUFS). [...] If any of the loudness parameters are not being used then their 16-bit integer values shall be set to 7FFFh, which is a value outside the range of the parameter values.

Sources:

- **READ** (primary) EBU R 128: Loudness normalisation and permitted maximum level of audio signals, v5.0 (November 2023) · EBU · <https://tech.ebu.ch/docs/r/r128.pdf> · retrieved 2026-09-03
- **READ** (primary) EBU Tech 3285: Specification of the Broadcast Wave Format (BWF), v2 (May 2011) · EBU · <https://tech.ebu.ch/docs/tech/tech3285.pdf> · retrieved 2026-09-03
- **TOOL_DEFAULT** (default) Metadata match tolerance · cumple · retrieved 2026-09-03. R 128 says loudness metadata must reflect the measured values but gives no tolerance; cumple flags a mismatch above 0.5 LU.

## EBU R 128 s1 short-form (adverts, promos) (`ebu-r128-s1-short`)

R 128 for commercials and promos. -23.0 LUFS integrated at QC tolerance ±0.2 LU, maximum short-term loudness -18.0 LUFS, -1 dBTP.

Loudness rules:

- -23 ±0.2 LUFS integrated, BS.1770-4

In the source's words:

- `loudness.integrated`: that the Programme Loudness Level shall be normalised to a Target Level of −23.0 LUFS [...] for the implementation of loudness workflows (for example, in Quality Control environments) a tolerance of ±0.2 LU is allowed in order to take account of measurement errors
- `dynamics.short_term_max`: that the Short-term Loudness Level (measured in compliance with EBU Tech 3341) shall not exceed −18.0 LUFS (+5.0 LU on the relative scale). For the implementation of loudness workflows (for example, in Quality Control environments) a tolerance of +0.2 LU is allowed in order to take account of measurement errors
- `peak.true`: that the True Peak Level of the programme shall not exceed −1 dBTP (dB True Peak) for linear audio, measured with a meter compliant with ITU-R BS.1770 and EBU Tech 3341. The measurement tolerance is ±0.3 dB (for signals with a bandwidth limited to 20 kHz).

Sources:

- **READ** (primary) EBU R 128 s1: Loudness parameters for short-form content (adverts, promos, etc.), v3 (August 2020) · EBU · <https://tech.ebu.ch/docs/r/r128s1.pdf> · retrieved 2026-09-03

## NBCUniversal linear commercial (`nbcu-commercial`)

NBCU Linear Commercial Guidelines (short-form). Measured average of -24 LKFS ±2 dB of the full program mix, not dialogue only, with a BS.1770-based meter; matches ATSC A/85 and the AC-3 dialnorm.

Loudness rules:

- -24 ±2 LUFS integrated, BS.1770-4

In the source's words (paraphrased; verbatim quotes pending):

- `loudness.integrated`: Provide a measured AVERAGE of -24 LKFS (+/-2 dB) of the full program mix (not only dialog). Use an ITU-R BS.1770 based broadcast loudness meter. (as quoted from the guidelines)
- `peak.true`: The guidelines reference ATSC A/85, whose true peak recommendation is below -2 dBTP. (paraphrase)

Sources:

- **READ** (primary) Linear NBCU Commercial Guidelines (February 2024) · NBCUniversal · <https://together.nbcuni.com/wp-content/uploads/sites/3/2024/01/Linear-NBCU-Commercial-Guidelines-Feb-24.pdf> · retrieved 2026-09-03. Short-form commercial guidelines; NBCU's long-form delivery spec is not public.

## Free TV Australia OP-59 (`op-59`)

Australian television loudness. -24 LKFS ±1 dB, -2 dBTP, BS.1770-3. A recommendation, not a regulation.

Loudness rules:

- -24 ±1 LUFS integrated, BS.1770-4

In the source's words (paraphrased; verbatim quotes pending):

- `loudness.integrated`: Target loudness -24 LKFS with a tolerance of ±1 dB, measured per ITU-R BS.1770-3. (paraphrase of OP-59 Issue 4)
- `peak.true`: Maximum true peak -2 dBTP. (paraphrase of OP-59 Issue 4)

Sources:

- **READ** (primary) OP-59: Measurement and Management of Loudness for TV Broadcasting, Issue 4 (October 2018) · Free TV Australia · <https://www.freetv.com.au/wp-content/uploads/2019/08/OP-59-Measurement-and-Managemnt-of-Loudness-for-TV-Broadcasting-Issue-4-October-2018.pdf> · retrieved 2026-09-03

## DCP 5.1 audio (ISDCF channel order) (`dcp-5.1`)

Digital cinema package audio per the ISDCF channel recommendation. 48 or 96 kHz, 24-bit, channels in the order L R C LFE Ls Rs (then HI and VI-N on 7 and 8), always an even channel count. No loudness target, since cinema mixes are calibrated to the room; trailers use the TASA profile.

In the source's words (paraphrased; verbatim quotes pending):

- `format.layout`: Channel 1 L, 2 R, 3 C, 4 LFE, 5 Ls, 6 Rs, 7 HI, 8 VI-N, 9 Lc, 10 Rc, 11 Lrs, 12 Rrs, 13 motion data, 14 sync signal, 15 sign language video, 16 unused; an even number of channels is required. (paraphrase of ISDCF Doc 4)
- `format.sample_rate`: 48 or 96 kHz at 24-bit is the practice stated by SMPTE ST 428-2, which is paywalled and not verified here.

Sources:

- **READ** (primary) ISDCF Doc 4: Audio channel recommendations for DCPs (29 June 2017) · ISDCF · <https://files.isdcf.com/papers/ISDCF-Doc4-Audio-channel-recommendations.pdf> · retrieved 2026-09-03
- **GATED** (supporting) SMPTE ST 428-2 (sample rate and bit depth) · SMPTE · retrieved 2026-09-03

## Cinema advertising (SAWA) (`sawa-ad`)

Screen Advertising World Association limit for cinema commercials. 82 dB Leq(m), 3 dB below the TASA trailer limit, measured the same way.

In the source's words (paraphrased; verbatim quotes pending):

- `leqm.level`: Cinema advertisements shall not exceed 82 dB Leq(m). (paraphrase of the SAWA Screen Advertising Guide to Sound)

Sources:

- **READ** (primary) Screen Advertising Guide to Sound in Cinema · SAWA · <https://www.sawa.com/wp-content/uploads/2010/10/sound_in_cinema.pdf> · retrieved 2026-09-03
- **READ** (supporting) TASA Standard for Trailer Loudness · Trailer Audio Standards Association · <https://www.tasatrailers.org/TASAStandard.pdf> · retrieved 2026-09-03

## Cinema trailer (TASA) (`tasa-trailer`)

Trailer Audio Standards Association limit for theatrical trailers. 85 dB Leq(m) over the whole trailer, M-weighted, calibrated so -20 dBFS is 85 dBC per screen channel with surrounds 3 dB lower.

In the source's words:

- `leqm.level`: The TASA Standard defines the measurement and calls the limit 'a flexible number' set by its Ad Hoc Committee; the PDF does not print it. The figure of 85 dB Leq(m), in force since 2001 after starting at 87 in 1999, is documented in ISDCF Doc 11 (Ioan Allen, 2016).
- `leqm.calibration`: For example, using SMPTE Standards, −20 dBFS on a digital medium represents the reference level. A DFSS may produce +4 dBu at −20 dBFS, and may be designed so that such an electrical reference level produces 85 dBC Sound Pressure Level re: 20 μPa for each channel. [...] if the surround level is calibrated at 82 dBC for each channel (as practiced with 5.1, 6.1, 6.1(EX) and 7.1 formats) rather than 85 dB given in the example above, the contribution of each surround channel to the sum shall be 3 dB less than a screen channel.
- `leqm.detectors`: To prevent differences between electrical addition (vector) and acoustical addition in the reverberant field of a room (scalar), each of the channels shall employ a separate detector circuit, and the output of each of the detector circuits shall be added.
- `leqm.weighting`: The frequency weighting equalizer is based on an International Telecommunications Union recommended filter for the assessment of background noise in audio programs. [...] Note that for the purposes of insertion gain, the frequency 2.0 kHz is used for the 0 dB reference level. (The response table in §1.4.2 runs from -35.5 dB at 31 Hz through 0.0 dB at 2 kHz and +6.6 dB at 6.3 kHz to -27.8 dB at 20 kHz, each with a tolerance.)

Sources:

- **READ** (primary) ISDCF Doc 11: Trailer loudness history and the TASA standard (Ioan Allen) (15 March 2016) · ISDCF · retrieved 2026-09-03. Source of the numeric limit: 87 dB Leq(m) in 1999, lowered to 85 dB in 2001 and unchanged since.
- **READ** (primary) TASA Standard for Trailer Loudness (annex dated 15 January 2015) · Trailer Audio Standards Association · <https://www.tasatrailers.org/TASAStandard.pdf> · retrieved 2026-09-03
- **GATED** (supporting) ISO 21727:2016 Cinematography: Method of measurement of perceived loudness of short duration motion-picture audio material, 2016 · ISO · <https://www.iso.org/standard/69744.html> · retrieved 2026-09-03. Paywalled. The measurement method used here follows the freely published TASA description.

## AES TD1008 streaming, music (`aes-td1008-music`)

AES recommendation for streamed music. Track-normalized to -16 LUFS integrated with ±0.2 LU tolerance, -1 dBTP at the codec input; album mode normalizes the loudest track to -14 LUFS.

Loudness rules:

- -16 ±0.2 LUFS integrated, BS.1770-4

In the source's words (paraphrased; verbatim quotes pending):

- `loudness.integrated`: Music, track-normalized: -16 LUFS integrated, tolerance ±0.2 LU; in album mode the loudest track is normalized to -14 LUFS. (paraphrase of AES TD1008)
- `peak.true`: Maximum true peak -1 dBTP at the input to the codec. (paraphrase of AES TD1008)

Sources:

- **READ** (primary) AES TD1008: Recommendations for Loudness of Internet Audio Streaming and On-Demand Distribution, AESTD1008.1.21-9 (24 September 2021) · AES · <https://aes2.org/wp-content/uploads/2024/01/20210924_TD1008_v3.13.pdf> · retrieved 2026-09-03

## Apple Digital Masters (`apple-digital-masters`)

Apple Music's mastered-for-Apple programme. No loudness target and no numeric peak, but audible clipping at the encoder disqualifies a track. 24-bit PCM at 44.1 to 192 kHz; never upsample or pad 44.1/16 sources.

In the source's words (paraphrased; verbatim quotes pending):

- `peak.true`: Apple gives no numeric peak limit; it says audible clipping caused by excessive levels to the encoder may be reason for tracks not to be badged. -1 dBTP is cumple's default headroom for AAC encoding.
- `format.bit_depth`: Deliver 24-bit PCM at the native sample rate (44.1 to 192 kHz); do not upsample or bit-pad 44.1 kHz / 16-bit sources. (paraphrase of the Apple Digital Masters guide)

Sources:

- **READ** (primary) Apple Digital Masters: Technology Overview · Apple · <https://www.apple.com/apple-music/apple-digital-masters/docs/apple-digital-masters.pdf> · retrieved 2026-09-03
- **TOOL_DEFAULT** (default) Peak headroom default · cumple · retrieved 2026-09-03

## SoundCloud master (`soundcloud`)

SoundCloud normalizes to -14 LUFS integrated. Keep true peaks at or below -1 dBTP, or -2 dBTP if the master is louder than -14 LUFS.

Loudness rules:

- -14 ±1 LUFS integrated, BS.1770-4 · ±1 LU is cumple's window around the published normalization level.

In the source's words (paraphrased; verbatim quotes pending):

- `loudness.integrated`: Tracks are normalized to -14 LUFS integrated (ITU-R BS.1770). (paraphrase of SoundCloud help)
- `peak.true`: True peak at or below -1 dBTP, or -2 dBTP if louder than -14 LUFS. (paraphrase of SoundCloud help)

Sources:

- **READ** (primary) Will SoundCloud play my track at the level it's mastered? · SoundCloud · <https://help.soundcloud.com/hc/en-us/articles/360053660014> · retrieved 2026-09-03
- **TOOL_DEFAULT** (default) Tolerance window · cumple · retrieved 2026-09-03

## Spotify music master (`spotify`)

Spotify normalizes playback to -14 LUFS (Loud -11, Quiet -19). Masters at -14 LUFS integrated with true peaks at or below -1 dBTP arrive unchanged; anything louder is turned down and should keep peaks at or below -2 dBTP.

Loudness rules:

- -14 ±1 LUFS integrated, BS.1770-4 · Spotify publishes the normalization level, not a delivery tolerance; ±1 LU is cumple's window. A quieter master is fine and is simply turned up (limited to available headroom); a louder one is turned down.

In the source's words (paraphrased; verbatim quotes pending):

- `loudness.integrated`: Playback is normalized to -14 dB LUFS by default (ITU 1770); Loud is -11 and Quiet is -19. (paraphrase of Spotify's loudness normalization page)
- `peak.true`: Master with true peaks at or below -1 dBTP; if the master is louder than -14 LUFS, keep true peaks at or below -2 dBTP so that turning it down does not add distortion. (paraphrase of Spotify's loudness normalization page)

Sources:

- **READ** (primary) Loudness normalization · Spotify for Artists · <https://support.spotify.com/us/artists/article/loudness-normalization/> · retrieved 2026-09-03
- **TOOL_DEFAULT** (default) Tolerance window · cumple · retrieved 2026-09-03

## YouTube (community-measured) (`youtube`)

YouTube publishes no loudness specification. Third-party measurements put its playback normalization near -14 LUFS with true peaks kept at or below -1 dBTP. Use with that caveat.

Loudness rules:

- -14 ±1 LUFS integrated, BS.1770-4

In the source's words (paraphrased; verbatim quotes pending):

- `loudness.integrated`: About -14 LUFS, measured by third parties from YouTube's playback normalization; YouTube publishes nothing. (community measurement)
- `peak.true`: -1 dBTP is common advice for lossy delivery; YouTube publishes nothing. (community practice)

Sources:

- **COMMUNITY** (primary) Community measurements of YouTube playback normalization · various · retrieved 2026-09-03. No primary document exists. Treat a PASS here as 'consistent with what people have measured', not as compliance.

## Apple Podcasts (`apple-podcasts`)

Apple Podcasts audio requirements. -16 LKFS ±1, true peak at or below -1 dBFS; RSS episodes as MP3 or AAC (mono 64 to 128 kbps, stereo 128 to 256 kbps) at 44.1 or 48 kHz; subscriber audio as 24-bit stereo WAV or FLAC.

Loudness rules:

- -16 ±1 LUFS integrated, BS.1770-4

In the source's words (paraphrased; verbatim quotes pending):

- `loudness.integrated`: Loudness -16 dB LKFS with a ±1 dB tolerance. (paraphrase of Apple Podcasts audio requirements)
- `peak.true`: True peak no higher than -1 dBFS. (paraphrase of Apple Podcasts audio requirements)
- `format.sample_rate`: 44.1 or 48 kHz for RSS MP3/AAC; 44.1 to 192 kHz, 24-bit, stereo for Apple Podcasts Connect WAV or FLAC. (paraphrase)

Sources:

- **READ** (primary) Audio requirements, Apple Podcasts for Creators · Apple · <https://podcasters.apple.com/support/893-audio-requirements> · retrieved 2026-09-03

## AES TD1008 streaming, speech-anchored (`aes-td1008-speech`)

AES recommendation for internet streaming and on-demand distribution, speech content (news, talk, drama, podcasts). Speech-anchored -18 LUFS, +1 LU tolerance, -1 dBTP at the codec input. Written for distributors, not mastering engineers.

Loudness rules:

- -19 to -17 LKFS dialogue-gated, BS.1770-4 · Dialog Integrated Loudness preferred; TD1008 states +1 LU as the tolerance. cumple uses a symmetric ±1 window.

In the source's words (paraphrased; verbatim quotes pending):

- `loudness.dialogue_gated`: Speech-anchored content: -18 LUFS with +1 LU tolerance; measure Dialog Integrated Loudness where possible, otherwise Integrated Loudness. (paraphrase of AES TD1008)
- `peak.true`: Maximum true peak -1 dBTP at the input to the codec. (paraphrase of AES TD1008)

Sources:

- **READ** (primary) AES TD1008: Recommendations for Loudness of Internet Audio Streaming and On-Demand Distribution, AESTD1008.1.21-9 (24 September 2021) · AES · <https://aes2.org/wp-content/uploads/2024/01/20210924_TD1008_v3.13.pdf> · retrieved 2026-09-03

## Amazon MGM Studios 5.1 (discrete mono files) (`amazon-5.1-package`)

Amazon Studios near-field 5.1 delivery. -27 LKFS ±2 dialogue-gated (BS.1770-1 with Dialogue Intelligence, Nugen VisLM2 as the reference meter), -2 dBTP, 48 kHz / 24-bit, one mono .wav per channel; interleaved files are not accepted.

Loudness rules:

- -27 ±2 LKFS dialogue-gated, BS.1770-1

In the source's words (paraphrased; verbatim quotes pending):

- `loudness.dialogue_gated`: -27 ±2 LU, ITU-R BS.1770-1 with dialogue gating (Dolby Dialogue Intelligence); reference meter Nugen VisLM2. (paraphrase of the Amazon Studios asset technical specifications)
- `peak.true`: -2 dBTP maximum. (paraphrase)
- `format.packaging`: Each .wav file must be flattened. Discrete .wav files required per channel. Interleaved audio is not acceptable. (as quoted in search extraction of the gated portal)
- `stems.sum`: True D/M/E: dialogue, music and effects stems played together must reproduce the original-version printmaster at matching levels. (paraphrase)

Sources:

- **GATED** (primary) Amazon Studios Asset Technical Specifications · Amazon MGM Studios · <https://portal.amazonstudios.com/hc/en-us/articles/15986845319323-Asset-Technical-Specifications> · retrieved 2026-09-03. Partner portal returns 403 without a login; values come from search extraction.
- **TOOL_DEFAULT** (default) Stem residual default · cumple · retrieved 2026-09-03

## Prime Video Direct mezzanine audio (`amazon-pvd`)

Public Prime Video Direct (Video Central) audio rules. -24 LKFS ±2 integrated, -2 dBTP, 48 kHz, fully mixed program track only, 8-channel layout L R C LFE Ls Rs Lt Rt, audio and video durations within 2.0 s.

Loudness rules:

- -24 ±2 LUFS integrated, BS.1770-4

In the source's words (paraphrased; verbatim quotes pending):

- `loudness.integrated`: -24 LKFS ±2 dB integrated program loudness per ITU-R BS.1770. (paraphrase of Prime Video Direct content specifications)
- `peak.true`: True peak not above -2 dBTP. (paraphrase)
- `format.layout`: 8-channel layout L, R, C, LFE, Ls, Rs, Lt, Rt; M&E, silent, MOS and commentary tracks must be removed from the mezzanine. (paraphrase of Video Central audio page)
- `duration.av`: Audio and video durations must match within 2.0 seconds. (paraphrase of Video Central audio page)

Sources:

- **READ** (primary) Prime Video Central: Delivery experience, Audio · Amazon · <https://videocentral.amazon.com/support/delivery-experience/audio> · retrieved 2026-09-03

## Apple TV+ / Apple TV app (`apple-tv`)

Apple Video and Audio Asset Guide. A permitted range rather than a target. Dialogue-anchored -31 to -10 LKFS (ideally -30 to -18), non-dialogue -31 to -5 LKFS, true peak at most -1 dB TP, 24-bit LPCM at 48 kHz, no full-frequency content in the LFE.

Loudness rules:

- -31 to -10 LKFS dialogue-gated, BS.1770-4, if speech ≥ 15 % · Apple measures BS.1770 with Dialogue Intelligence, integrated over the full duration. The ideal window -30 to -18 LKFS is reported, not enforced.
- -31 to -5 LUFS integrated, BS.1770-4, if speech < 15 %

In the source's words:

- `loudness.dialogue_gated`: The average loudness of dialogue or speech in the Dolby Atmos file must be within the range of -31 LKFS to -10 LKFS, and should ideally be between -30 LKFS and -18 LKFS. [...] 1770 + Dialogue Intelligence (or other speech-gating algorithm) to measure the dialogue-gated loudness, integrated over the full duration of the asset, to verify it falls within the specified range indicated above.
- `loudness.integrated`: For Dolby Atmos files where dialogue is not the anchor element (for example, music assets), the average audio loudness of the Dolby Atmos file must be within the range of -31 LKFS to -5 LKFS.
- `peak.true`: True-peak level should not exceed -1 dB TP measured as per ITU-R BS.1770-4.
- `format.sample_rate`: All audio must be 24-bit linear pulse code modulation (LPCM) audio at 48kHz.
- `format.bit_depth`: All audio tracks in the file must be 24-bit LPCM audio at 48kHz.
- `format.lfe_band`: Full-frequency content should not be present in the Low-Frequency Effects (LFE) channel of the BWF ADM.
- `format.layout`: Expected channels: L, R, C, LFE, Ls, Rs [...] Expected channels: L, R, C, LFE, Ls, Rs, Rls (or Lrs), Rrs [...] Expected Dolby Pro Logic channels: Lt, Rt or expected stereo channels: L, R

Sources:

- **READ** (primary) Apple Video and Audio Asset Guide, 5.3.18 (October 13, 2025) · Apple · <https://help.apple.com/itc/videoaudioassetguide/en.lproj/static.html> · retrieved 2026-09-03
- **TOOL_DEFAULT** (default) LFE corner frequency · cumple · retrieved 2026-09-03. Apple gives no corner frequency for 'full-frequency content'; 120 Hz is the tool's choice, matching common bass-management practice.

## ATSC A/85:2026 Annex L streaming range (`atsc-a85-streaming`)

The new Annex L guidance for internet delivery. One consistent target between -23 and -27 LKFS, measured like television (dialogue level for long-form), true peak below -2 dBTP.

Loudness rules (any one applicable rule may pass):

- -27 to -23 LKFS dialogue-gated, BS.1770-1, if speech ≥ 15 %
- -27 to -23 LUFS integrated, BS.1770-4, if speech < 15 %

In the source's words:

- `loudness.dialogue_gated`: For Streaming delivery services only, a single Target Loudness between –23 to –27 LKFS is recommended, unless there are other prior arrangements between Content-exchange or delivery parties.
- `loudness.integrated`: It is strongly recommended that all Content be presented to the audience at only one specific and consistent Target Loudness. Long-form and Short-form Loudness measurements should be performed per Table M.1, regardless of the source of the Content.
- `peak.true`: The True Peak level should be kept below –2 dBTP in order to provide headroom to avoid potential clipping due to downstream processing (such as audio coding used in delivery).

Sources:

- **READ** (primary) ATSC A/85:2026-07, Annex L: Guidelines for Establishing and Maintaining Audio Loudness of Internet-delivered Content, A/85:2026-07 (8 July 2026) · ATSC · <https://www.atsc.org/wp-content/uploads/2026/07/A85-2026-07.pdf> · retrieved 2026-09-03

## Disney+ near-field mix (`disney-plus`)

Disney media tech specs for home audio. -27 LKFS dialogue anchor; -24 LKFS program loudness when speech is under 15 %; BS.1770-3/-4 relative gating over the full composite program; every bed and object at or below -2 dBTP; monitoring at 79 dBC.

Loudness rules (any one applicable rule may pass):

- -27 ±2 LKFS dialogue-gated, BS.1770-4, if speech ≥ 15 % · Disney states the -27 LKFS dialogue anchor; the ±2 tolerance is cumple's assumption pending a direct read of the page.
- -24 ±2 LUFS integrated, BS.1770-4, if speech < 15 % · A ±0.4 tolerance was reported by search extraction; it is unusually tight and unverified, so ±2 is used until the page is read directly.

In the source's words (paraphrased; verbatim quotes pending):

- `loudness.dialogue_gated`: -27 LKFS dialogue anchor, measured on the full composite program with the relative-level (G10) gating of BS.1770-3 or -4. (paraphrase of mediatechspecs.disney.com)
- `loudness.integrated`: -24 LKFS program loudness when the speech or dialogue percentage is below 15 %. (paraphrase of mediatechspecs.disney.com)
- `peak.true`: Limit all beds and objects individually to -2 dBTP or lower; the Atmos printmaster may exceed -2 dBTP when measured via the 5.1 re-render. (paraphrase of mediatechspecs.disney.com)

Sources:

- **SE** (primary) Disney Media Tech Specs: Production Audio · Disney · <https://mediatechspecs.disney.com/production/audio/production-audio> · retrieved 2026-09-03. The site is a JavaScript app; values were recovered via search extraction.
- **TOOL_DEFAULT** (default) Tolerance assumption · cumple · retrieved 2026-09-03

## Hulu content partner guidebook (2018, stale) (`hulu-2018`)

Hulu's public Content Partner Guidebook v5.0 from 2018. -24 LKFS per BS.1770-4, sample peak -2 dBFS, 48 kHz LPCM 16 or 24-bit interleaved, 8-channel L R C LFE Ls Rs Lt Rt. Kept for reference; Hulu now delivers through Disney.

Loudness rules:

- -24 ±2 LUFS integrated, BS.1770-4

In the source's words (paraphrased; verbatim quotes pending):

- `loudness.integrated`: -24 LKFS/LUFS measured per ITU-R BS.1770-4. (paraphrase of the guidebook)
- `peak.sample`: Peak -2 dBFS (sample peak). (paraphrase of the guidebook)

Sources:

- **READ** (primary) Hulu Content Partner Guidebook, v5.0 (2018) · Hulu · <http://assets.hulu.com/portaldocuments/ContentPartnerGuidebook_v5.0.pdf> · retrieved 2026-09-03. Stale: the newest public version is from 2018.

## Warner Bros. Discovery / Max component audio (`max-wbd`)

WBD Content Partner Hub audio ingest. -24 LKFS ±2 (dialog-gated or overall, both accepted), -2 dBTP, LRA max 20 LU, 48 kHz / 24-bit, head padding at most 5 s, no tail padding.

Loudness rules (any one applicable rule may pass):

- -24 ±2 LKFS dialogue-gated, BS.1770-4
- -24 ±2 LUFS integrated, BS.1770-4

In the source's words (paraphrased; verbatim quotes pending):

- `loudness.integrated`: -24 LKFS/LUFS (plus or minus 2 dB) via ITU-R BS.1770-3 and BS.1770-4; either dialog-gated or overall target average loudness is accepted; 5.1 measured minus LFE. (paraphrase of Content Partner Hub Audio v1.3)
- `loudness.dialogue_gated`: Dialog-gated target average loudness of -24 LKFS ±2 dB is accepted as an alternative to the overall measurement. (paraphrase of Content Partner Hub Audio v1.3)
- `peak.true`: Maximum true peak -2 dBTP. (paraphrase of Content Partner Hub Audio v1.3)
- `dynamics.lra`: Loudness range maximum 20 LU. (paraphrase of Content Partner Hub Audio v1.3)
- `format.sample_rate`: 48 kHz, 24-bit linear PCM, MBWF/RF64 or MXF. (paraphrase of Content Partner Hub Audio v1.3)
- `format.layout`: 2.0 as L, R or Lt, Rt, M1, M2; 5.1 as L, R, C, LFE, Ls, Rs; one soundfield group per file; 5.1 must be accompanied by a separate 2.0. (paraphrase of Content Partner Hub Audio v1.3)
- `padding.head`: Head padding at most 5 seconds. (paraphrase of Content Partner Hub Audio v1.3)
- `padding.tail`: Tail padding not permitted; timecode aligned to the OV master. (paraphrase of Content Partner Hub Audio v1.3)

Sources:

- **READ** (primary) Content Partner Hub, Ingest Specifications, Component Delivery: Audio, v1.3 (2 December 2025) · Warner Bros. Discovery · <https://partnerhub.warnermediagroup.com/ingest-specifications/component-delivery/audio> · retrieved 2026-09-03

## Netflix stereo (2.0) printmaster (`netflix-2.0`)

Netflix near-field stereo mix. -27 LKFS ±2 dialogue-gated (BS.1770-1 with Dialogue Intelligence), -24 ±2 full program if speech is under 15 %, -2 dBTP, 48 kHz / 24-bit.

Loudness rules (any one applicable rule may pass):

- -27 ±2 LKFS dialogue-gated, BS.1770-1, if speech ≥ 15 % · Netflix measures with Dolby Dialogue Intelligence. cumple approximates that gate with an open speech detector and says so on every sheet.
- -24 ±2 LUFS integrated, BS.1770-4, if speech < 15 % · Content measuring under 15 % dialogue switches to a full-program target.
- -27 ±2 LUFS integrated, BS.1770-4 (fallback) · Netflix QC rule: if the dialogue-gated measurement fails, re-measure BS.1770-4 full program and do not flag if that passes. The fallback window is taken as the same -27 ±2; to be verified against the live page.

In the source's words (paraphrased; verbatim quotes pending):

- `loudness.dialogue_gated`: -27 LKFS ±2 LU, dialogue-gated, measured over the entire program per ITU-R BS.1770-1 with Dolby Dialogue Intelligence. (paraphrase of Sound Mix Specifications v1.6)
- `loudness.integrated`: Near-field mixes with less than 15 % dialogue: -24 LKFS ±2 LU, BS.1770-3 or -4, full program. (paraphrase of Sound Mix Specifications v1.6)
- `peak.true`: True peak shall not exceed -2 dBTP; a limiter at -2.3 dBFS is recommended. (paraphrase of Sound Mix Specifications v1.6)
- `stems.sum`: The DX, MX and FX stems must equal the printmaster when combined. No numeric tolerance is published; -60 dBFS residual is cumple's default. (paraphrase of Originals Delivery Specifications OC-3-3)
- `stems.me_speech`: The M&E must be fully filled and contain no dialogue. (paraphrase of M&E Creation and Delivery Guidelines)

Sources:

- **SE** (primary) Netflix Sound Mix Specifications & Best Practices, v1.6 · Netflix · <https://partnerhelp.netflixstudios.com/hc/en-us/articles/360001794307> · retrieved 2026-09-03. The Partner Help Center moved behind studiopartner.netflix.net, a JavaScript app; values were recovered via search extraction of the live page and must be re-read directly.
- **READ** (primary) Netflix Originals Delivery Specifications OC-3-3, OC-3-3 (July 2019) · Netflix · retrieved 2026-09-03. Historical: read from a re-hosted copy. Used only for stems, M&E and channel-order clauses.
- **SE** (primary) Loudness and True Peaks: How to Measure and When to Flag · Netflix · <https://partnerhelp.netflixstudios.com/hc/en-us/articles/360050414014> · retrieved 2026-09-03
- **TOOL_DEFAULT** (default) Stem residual default · cumple · retrieved 2026-09-03. Netflix publishes no null-test tolerance; -60 dBFS residual after alignment is the tool's choice.

## Netflix 5.1 near-field printmaster (`netflix-5.1`)

Netflix near-field 5.1 mix. -27 LKFS ±2 dialogue-gated (BS.1770-1 with Dialogue Intelligence), -24 ±2 full program if speech is under 15 %, -2 dBTP, 48 kHz / 24-bit, L R C LFE Ls Rs; stems must sum to the printmaster.

Loudness rules (any one applicable rule may pass):

- -27 ±2 LKFS dialogue-gated, BS.1770-1, if speech ≥ 15 %
- -24 ±2 LUFS integrated, BS.1770-4, if speech < 15 %
- -27 ±2 LUFS integrated, BS.1770-4 (fallback) · Netflix QC rule: if the dialogue-gated measurement fails, re-measure BS.1770-4 full program and do not flag if that passes. The fallback window is taken as -27 ±2; to be verified against the live page.

In the source's words (paraphrased; verbatim quotes pending):

- `loudness.dialogue_gated`: -27 LKFS ±2 LU, dialogue-gated, measured over the entire program per ITU-R BS.1770-1 with Dolby Dialogue Intelligence. (paraphrase of Sound Mix Specifications v1.6)
- `loudness.integrated`: Near-field mixes with less than 15 % dialogue: -24 LKFS ±2 LU, BS.1770-3 or -4, full program. (paraphrase of Sound Mix Specifications v1.6)
- `peak.true`: True peak shall not exceed -2 dBTP; a limiter at -2.3 dBFS is recommended. (paraphrase of Sound Mix Specifications v1.6)
- `format.layout`: 5.1 channel order L, R, C, LFE, Ls, Rs. (paraphrase of Originals Delivery Specifications OC-3-3)
- `stems.sum`: The DX, MX and FX stems must equal the 5.1 mix when combined. No numeric tolerance is published; -60 dBFS residual is cumple's default. (paraphrase of Originals Delivery Specifications OC-3-3)
- `stems.me_speech`: The M&E must be fully filled and contain no dialogue. (paraphrase of M&E Creation and Delivery Guidelines)

Sources:

- **SE** (primary) Netflix Sound Mix Specifications & Best Practices, v1.6 · Netflix · <https://partnerhelp.netflixstudios.com/hc/en-us/articles/360001794307> · retrieved 2026-09-03. The Partner Help Center moved behind studiopartner.netflix.net, a JavaScript app; values were recovered via search extraction and must be re-read directly.
- **READ** (primary) Netflix Originals Delivery Specifications OC-3-3, OC-3-3 (July 2019) · Netflix · retrieved 2026-09-03. Historical, read from a re-hosted copy; used for stems, M&E and channel order only.
- **TOOL_DEFAULT** (default) Stem residual and LFE corner defaults · cumple · retrieved 2026-09-03

## Paramount Global content delivery (Pluto TV ingest) (`paramount-pluto`)

Paramount's public Global Content Delivery Guide v2.2, which covers Pluto TV ingest rather than Paramount+ post deliverables. About -24 LKFS per BS.1770-4, sample peak -2 dBFS, 48 kHz minimum, 16 or 24-bit LPCM.

Loudness rules:

- -24 ±2 LUFS integrated, BS.1770-4 · The guide says loudness should approximate -24 LKFS; the ±2 window is cumple's reading of 'approximate'.

In the source's words (paraphrased; verbatim quotes pending):

- `loudness.integrated`: All audio loudness levels should approximate -24 LKFS/LUFS (based on ITU-R BS.1770-4 loudness measurement methods). (as quoted from the guide)
- `peak.sample`: Audio peak level of -2 dBFS. (as quoted from the guide; a sample peak, not a true peak)
- `format.layout`: ProRes 8-channel: 1 L, 2 R, 3 C, 4 LFE, 5 Ls, 6 Rs, 7 Lt, 8 Rt, all discrete. (paraphrase of the guide)

Sources:

- **READ** (primary) Paramount Global Content Delivery Guide, V2.2 · Paramount · <https://www.paramount.com/sites/g/files/dxjhpe356/files/2024-07/Global_Content_Delivery_Guide_V2.2.pdf> · retrieved 2026-09-03. Body text is Pluto TV FAST-channel ingest; no public Paramount+ post-production audio spec was found.
- **TOOL_DEFAULT** (default) Tolerance reading · cumple · retrieved 2026-09-03

