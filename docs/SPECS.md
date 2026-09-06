# Destinations known to cumple 0.1.0

Generated 2026-09-06 from `src/cumple/specs/profiles/*.yaml`. Every number is traceable to the sources listed under each destination, and the grade says how good that trace is:

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
| `abc-commercial` | ABC commercial file delivery HD (Disney Advertising) | broadcast | -26 to -23 integrated | -6 dBTP | 48 kHz, 24-bit | READ |
| `arib-tr-b32` | ARIB TR-B32 (Japan television) | broadcast | -24 ±1 integrated | -1 dBTP | 48 kHz, 16/24-bit | SECONDARY |
| `atsc-a85-2026` | ATSC A/85:2026 television (US) | broadcast | -24 ±2 dialogue-gated or -24 ±2 integrated (speech < 15 %) | -2 dBTP | 48 kHz, 16/24-bit | READ |
| `cbs-commercial` | CBS Television Network commercial (Paramount) | broadcast | -24 ±2 integrated | -2 dBTP | 48 kHz, 16/20/24-bit | READ |
| `dpp-as11` | UK DPP / AS-11 programme delivery | broadcast | -23 ±0.5 integrated | -1 dBTP | 48 kHz, 24-bit, mono fold | READ |
| `ebu-r128` | EBU R 128 broadcast programme | broadcast | -23 ±1 integrated | -1 dBTP | 48 kHz, 16/24-bit, bext truth | READ* |
| `ebu-r128-s1-short` | EBU R 128 s1 short-form (adverts, promos) | broadcast | -23 ±0.2 integrated | -1 dBTP | max S ≤ -18, 48 kHz, 16/24-bit, bext truth | READ |
| `fox-commercial-2024` | Fox Networks commercial material (2024) | broadcast | -24 ±2 integrated | -6 dBFS sample | 48 kHz, 16/24-bit | READ* |
| `fox-program-2018` | Fox Networks broadcast program material (2018) | broadcast | -24 ±2 integrated | -2 dBTP | 48 kHz, 16/24-bit | READ* |
| `nbcu-commercial` | NBCUniversal linear commercial | broadcast | -24 ±2 integrated | -2 dBTP | 48 kHz, 16/24-bit | READ |
| `op-59` | Free TV Australia OP-59 | broadcast | -24 ±1 integrated | -2 dBTP | 48 kHz, 16/24-bit | READ |
| `dcp-5.1` | DCP 5.1 audio (ISDCF channel order) | cinema | no loudness target | none stated | 48/96 kHz, 24-bit | READ |
| `sawa-ad` | Cinema advertising (SAWA) | cinema | ≤ 82 dB Leq(m) | none stated | 48/96 kHz, 24-bit | READ |
| `tasa-trailer` | Cinema trailer (TASA) | cinema | ≤ 85 dB Leq(m) | none stated | 48/96 kHz, 24-bit | READ |
| `aes-td1008-music` | AES TD1008 streaming, music | music | -16 ±0.2 integrated | -1 dBTP |  | READ |
| `apple-digital-masters` | Apple Digital Masters | music | no loudness target | -1 dBTP | 44.1/48/88.2/96/176.4/192 kHz, 24-bit | READ* |
| `apple-immersive` | Apple Music immersive audio (Dolby Atmos, 5.1, 7.1) | music | ≤ -18 integrated | -1 dBTP | 48 kHz, 24-bit, LFE band | READ* |
| `soundcloud` | SoundCloud master | music | -14 ±1 integrated | -1 dBTP | 44.1/48/88.2/96 kHz, 16/24-bit | READ* |
| `spotify` | Spotify music master | music | -14 ±1 integrated | -1 dBTP | 44.1/48/88.2/96 kHz, 16/24-bit | READ* |
| `youtube` | YouTube (community-measured) | music | -14 ±1 integrated | -1 dBTP |  | COMMUNITY |
| `apple-podcasts` | Apple Podcasts | podcast | -16 ±1 integrated | -1 dBTP | 44.1/48/88.2/96/176.4/192 kHz | READ |
| `aes-td1008-speech` | AES TD1008 streaming, speech-anchored | streaming | -19 to -17 dialogue-gated | -1 dBTP |  | READ |
| `amazon-2.0-package` | Amazon MGM Studios 2.0 (discrete mono files) | streaming | -27 ±2 dialogue-gated | -2 dBTP | 48 kHz, 24-bit, discrete, padding, stems sum | READ* |
| `amazon-5.1-package` | Amazon MGM Studios 5.1 (discrete mono files) | streaming | -27 ±2 dialogue-gated | -2 dBTP | 48 kHz, 24-bit, discrete, padding, stems sum, LFE band | READ* |
| `amazon-pvd` | Prime Video Direct mezzanine audio | streaming | -24 ±2 integrated | -2 dBTP | 48 kHz, 16/24-bit | READ |
| `apple-tv` | Apple TV+ / Apple TV app | streaming | -31 to -10 dialogue-gated; -31 to -5 integrated (speech < 15 %) | -1 dBTP | 48 kHz, 24-bit, LFE band | READ* |
| `atsc-a85-streaming` | ATSC A/85:2026 Annex L streaming range | streaming | -27 to -23 dialogue-gated or -27 to -23 integrated (speech < 15 %) | -2 dBTP | 48 kHz, 16/24-bit | READ |
| `disney-a85` | Disney A85, General Entertainment (Hulu originals, ABC, FX) | streaming | -24 ±2 dialogue-gated or -24 ±2 integrated | -2 dBTP | 48 kHz, 24-bit | READ |
| `disney-plus-2.0` | Disney+ near-field 2.0 stereo | streaming | -24 ±0.4 integrated | -2 dBTP | 48 kHz, 24-bit | READ |
| `disney-plus-5.1` | Disney+ near-field 5.1, 7.1 and Atmos | streaming | -27 ±0.4 dialogue-gated; -24 ±0.4 integrated (speech < 15 %); ≤ -20 integrated | -2 dBTP | 48 kHz, 24-bit | READ |
| `disney-r128` | Disney R128 (dubs and territories on R 128) | streaming | -23 ±0.5 integrated | -3 dBTP | LRA ≤ 20 LU, max S ≤ -15 | READ |
| `disney-trailer` | Disney in-home trailer (Digital Supply Chain) | streaming | -24 ±2 integrated | -2 dBTP | 48 kHz, padding | READ |
| `hulu-2018` | Hulu content partner guidebook (2018, stale) | streaming | -24 ±2 integrated | -2 dBFS sample | 48 kHz, 16/24-bit, interleaved | READ |
| `max-wbd` | Warner Bros. Discovery / Max component audio | streaming | -24 ±2 dialogue-gated or -24 ±2 integrated | -2 dBTP | LRA ≤ 20 LU, 48 kHz, 24-bit, padding | READ |
| `netflix-2.0` | Netflix stereo (2.0) printmaster | streaming | -27 ±2 dialogue-gated or -24 ±2 integrated (speech < 15 %) | -2 dBTP | 48 kHz, 24-bit, discrete, stems sum, mono fold | READ* |
| `netflix-5.1` | Netflix 5.1 near-field printmaster | streaming | -27 ±2 dialogue-gated or -24 ±2 integrated (speech < 15 %) | -2 dBTP | 48 kHz, 24-bit, discrete, stems sum, LFE band | READ* |
| `paramount-pluto` | Paramount Global content delivery (Pluto TV ingest) | streaming | -24 ±2 integrated | -2 dBFS sample | 48/96 kHz, 16/24-bit | READ* |
| `peacock` | Peacock (NBCUniversal, community-reported) | streaming | -27 ±2 dialogue-gated | none stated |  | COMMUNITY* |

## ACX / Audible audiobook (`acx`)

ACX Audio Submission Requirements, the one major spec that uses RMS instead of BS.1770. RMS between -23 and -18 dBFS, peaks at or below -3 dBFS, noise floor at or below -60 dBFS RMS, 44.1 kHz, 192 kbps CBR MP3, room tone at head and tail, at most 120 minutes per file.

In the source's words (paraphrased; verbatim quotes pending):

- `rms.level`: Measure between -23 dB and -18 dB RMS. (paraphrase of ACX Audio Submission Requirements)
- `peak.sample`: Peak values no higher than -3 dB. (paraphrase of ACX Audio Submission Requirements)
- `rms.noise_floor`: Noise floor no higher than -60 dB RMS. (paraphrase of ACX Audio Submission Requirements)
- `duration.max`: Each file is a single chapter or section and no longer than 120 minutes; 0.5 to 1 second of room tone at the head and 1 to 5 seconds at the tail. (paraphrase of ACX Audio Submission Requirements)

Sources:

- **READ** (primary) ACX Audio Submission Requirements · ACX (Audible) · <https://www.acx.com/help/acx-audio-submission-requirements/200013520> · retrieved 2026-09-03. The live page redirected during research; values are from the ACX document text.

## ABC commercial file delivery HD (Disney Advertising) (`abc-commercial`)

ABC Commercial File Delivery HD Technical Specifications (cover dated April 28, 2022; the media-kit file is dated 2024-08-13). -24 LKFS ±2 for the length of the spot with a BS.1770-3 meter on all channels but the LFE, and ABC rejects or normalizes anything louder than -23 LKFS, so the window is -26 to -23; true peak never above -6 dBFS; stereo or 5.1, 48 kHz, 24-bit (an earlier section prefers 20-bit); fixed dialnorm; a mono mix on track 7 when no audio description or SAP is delivered.

Loudness rules:

- -26 to -23 LUFS integrated, BS.1770-3 · The nominal window is -24 ±2; clause 5.2.5.2 caps it at -23 LKFS, so the upper bound here is -23, not -22.

In the source's words:

- `loudness.integrated`: In accordance with the ATSC recommended practice and the CALM act, ABC will adopt the current recommendation for audio loudness of -24LKFS (+/- 2 dB) measured for the length of the delivered spot. A loudness meter based on ITU-R BS.1770-3 incorporating all channels except the LFE channel should be used for this measurement. [...] 5.2.5.2 The target reference level for audio loudness is -24 LKFS, plus or minus 2 dB. ABC reserves the right to reject and/or normalize the content, on an entire spot basis, on anything louder than -23 dB LKFS. [...] 5.2.5.4 All audio channels of the 5.1, with the exception of the LFE, shall be measured. 5.2.5.5 For stereo material, both audio channels shall be measured.
- `peak.true`: The absolute maximum peak audio levels of brief and only occasional instances are not to exceed -6 dBFS. ABC reserves the right to either reject or correct audio levels that are not consistent with this specification. [...] 5.2.5.3 Maximum true peak levels are not to exceed -6 dBFS, per BS.1770.
- `format.sample_rate`: 5.2.3 Digital audio shall be linear PCM with a sample rate of 48 kHz.
- `format.bit_depth`: 5.2.3 Bit depth shall be 24 bits. [2.5.7.2 elsewhere in the document: at a sampling rate of 48KHz and at a preferred bit depth of 20 bits.]
- `format.layout`: Either 2-channel stereo or 5.1 channel audio will be accepted. [...] A mono-mix is now required on audio track 7 if Audio Description or SAP is not delivered. [...] 5.2.1 Spots may be delivered with either 5.1 channel audio or 2-channel stereo audio.
- `metadata.dialnorm`: ABC will be operating under a fixed dialnorm paradigm.

Sources:

- **READ** (primary) ABC Commercial File Delivery HD Technical Specifications, April 28, 2022 (cover dated April 28, 2022; file dated 2024-08-13) · Disney Advertising (ABC) · <https://files.disneyadvertising.com/MediaKit/ABC-Brands/HD-Tech-Specs.pdf> · retrieved 2026-09-06. Read from the PDF's text layer. Clause 5.2.3 says 24 bits and clause 2.5.7.2 says a preferred bit depth of 20 bits; the profile takes 24 as the requirement and records both. The -6 dBFS peak is stated once as an absolute maximum peak and once as a true peak per BS.1770; cumple applies it as a true peak. The document is an advertising delivery spec, not ABC's programme delivery spec, which is not public.

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

## CBS Television Network commercial (Paramount) (`cbs-commercial`)

CBS Television Network Commercial Integration Manual 2025 to 2026 (Paramount), Appendix A. -24 LKFS ±2 per ATSC A/85 Annex J, measured with the BS.1770-2 technique over the length of the commercial with all channels; the Lt/Rt downmix of a 5.1 mix is measured too and its true peak never exceeds -2 dBFS; stereo, Lt/Rt or 5.1 on channels 1 to 6 in SMPTE order, 16, 20 or 24-bit at 48 kHz, SMPTE RP-155 reference level -20 dBFS. Paramount+ programme deliverables are not public; this is the public Paramount commercial document.

Loudness rules:

- -24 ±2 LUFS integrated, BS.1770-2

In the source's words:

- `loudness.integrated`: For all of the above audio formats, the ITU-R BS-1770-2 loudness measurement technique shall be used to confirm the measured loudness does not exceed the ATSC Recommended Practice A/85 Annex-J target of -24 LKFS ± 2 dB with all channels measured for the length of the commercial. [...] If the commercial content fails to meet this loudness target, then CBS will process the material per the ITU-R BS.1770-2 loudness measurement technique to meet the ASTC Recommended Practice A/85 Annex-J target of -24 LKFS ± 2 dB. This delivery requirement ensures the commercial will be in compliance with the CALM Act and Federal Communications Commission’s Regulations.
- `peak.true`: In addition to measuring the 5.1 surround sound mix for loudness, the Lt/Rt downmix should also be measured with the downmix parameters listed in the Appendix. The maximum true peak stereo audio level shall never exceed -2 dBFS and a loudness of -24 LKFS ± 2 dB when down mixed from 5.1.
- `loudness.downmix`: In addition to measuring the 5.1 surround sound mix for loudness, the Lt/Rt downmix should also be measured with the downmix parameters listed in the Appendix.
- `format.sample_rate`: Digital audio must conform to the AES3 Specification. The digital audio sampling depth may be at 16, 20 or 24 bit with a sampling frequency of 48 kHz and conform to SMPTE RP-155 for -20 dBFS reference level.
- `format.bit_depth`: The digital audio sampling depth may be at 16, 20 or 24 bit with a sampling frequency of 48 kHz and conform to SMPTE RP-155 for -20 dBFS reference level.
- `format.layout`: The program supplier has the option of providing one of three formats: Discrete Two Channel Stereo, Matrixed Surround Sound (Lt, Rt), or 5.1 Surround Sound. [...] The six discrete channels that comprise the 5.1 Surround Sound signal shall be recorded on the following channels: CH-1 Left (music & effects), CH-2 Right (music & effects), CH-3 Center (dialogue), CH-4 Low Frequency Effects (LFE), CH-5 LS - Left Surround (music & effects), CH-6 RS - Right Surround (music & effects). At the option of the program supplier, Channel 7 may contain Secondary Audio Program- SAP (Spanish or Video Description).
- `reference.tone`: A 400 or 1KHz Hz audio tone at a reference level of -20dBFS shall be recorded on all channels containing program audio, with the exception of channel 4 (LFE) for 5.1 Surround Sound content shall contain 100 Hz audio tone at a reference level of -20 dBFS.

Sources:

- **READ** (primary) CBS Television Network Commercial Integration Manual, 2025 to 2026 Network Integration Manual, Appendix A: Broadcast Materials Technical Specification, 2025 to 2026 (PDF dated 2025-09-23) · Paramount (CBS Television Network) · <https://www.paramount.com/files/documents/CBS%20Commercial%20Integration%20Manual.pdf> · retrieved 2026-09-06. Read from the PDF's text layer. The manual covers commercial material; the Lt/Rt downmix measurement is recorded as a clause and is not run by cumple on the 5.1 file. A 20-bit file reads as 24-bit in most tools; cumple reports the container's stated depth.

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

## Fox Networks commercial material (2024) (`fox-commercial-2024`)

Fox Network Operations Delivery Requirements and Technical Specifications, February 2024, Technical Specifications for Commercial Material. Each commercial segment averages -24 LKFS per ATSC A/85 across all channels except the LFE; instantaneous peaks never above -6 dBFS and average peaks never above -10 dBFS; 5.1 on channels 1 to 6 with DVS, SAP or mono on 7 and mono on 8; 16 or 24-bit PCM at 48 kHz; stereo and mono deliveries need prior authorization. Fox states no tolerance; the ±2 window is the tool's default from A/85.

Loudness rules:

- -24 ±2 LUFS integrated, BS.1770-3 · Fox states the target and no tolerance; ±2 is the tool's default, the A/85 window.

In the source's words:

- `loudness.integrated`: The loudness shall be measured across all channels, except LFE (Low-Frequency Enhancement) in units of LKFS per ATSC RP/A85. Each commercial segment shall have an average loudness of -24LKFS. [...] If the material’s loudness measures higher or lower than our loudness specification, the material will be subject to rejection. SAP and DVS are subject to the above loudness and dynamic range requirements.
- `peak.sample`: Instantaneous audio peaks shall not exceed -6dBFS.
- `peak.average`: Average peak audio levels shall not exceed -10dBFS.
- `format.sample_rate`: MXF files shall have 8 audio PCM 16 (16 bits @ 48 kHz PCM) or 8 audio PCM 24 (24 bits @ 48 kHz PCM) channels per SMPTE 382M-2007. Audio Layout shall be included in MXF wrapper or XML data.
- `format.bit_depth`: MXF files shall have 8 audio PCM 16 (16 bits @ 48 kHz PCM) or 8 audio PCM 24 (24 bits @ 48 kHz PCM) channels per SMPTE 382M-2007.
- `format.layout`: All files shall be delivered per SMPTE 296M- 2001 with 5.1 digital sound per ATSC RP A/85. Videotape, SD, DVS, SAP, Stereo and Mono deliveries require prior authorization. [...] 5.1 digital surround sound shall be in phase. Dolby E is not accepted. [...] Channel 1: Left, 2: Right, 3: Center, 4: LFE Low Frequency Enhancement, 5: Left surround, 6: Right surround, 7: DVS, SAP, Mono, 8: Mono, 9 to 12: (n/a or not used). Programming shall be created such that any down mix from 5.1 to stereo or mono represents the original mix.

Sources:

- **READ** (primary) Network Operations Delivery Requirements and Technical Specifications, Technical Specifications for Commercial Material, February 2024 (February 2024) · Fox Networks · <https://www.fox.com/pdf/Network-Operations-Delivery-Requirements-and-Technical-Specifications-Final.pdf> · retrieved 2026-09-06. Read from the PDF's text layer. The -6 dBFS figure is an instantaneous peak, applied as a sample peak; the -10 dBFS average peak is recorded as a clause and not measured. Fox delivers as MXF, which cumple does not read; check the PCM printmaster before wrapping.
- **TOOL_DEFAULT** (default) Loudness tolerance · cumple · retrieved 2026-09-06. Fox states -24 LKFS with no tolerance; ±2 is the A/85 window applied as the tool's default.

## Fox Networks broadcast program material (2018) (`fox-program-2018`)

Fox Technical Specifications for Broadcast Program Material, August 2018, the public Fox programme delivery document. Average loudness of -24 LKFS for the duration of the program per ATSC A/85 (2013), measured across all channels except the LFE; true peaks never above -2 dBFS; 5.1 per ITU-R BS.775-3 on channels 1 to 6 with DVS, SAP or mono on 7 and mono on 8; 16 or 24-bit PCM at 48 kHz; any downmix must represent the original mix; Dolby E refused. Fox states no tolerance; the ±2 window is the tool's default from A/85.

Loudness rules:

- -24 ±2 LUFS integrated, BS.1770-3 · Fox states the target and no tolerance; ±2 is the tool's default, the A/85 window. Fox cites A/85 (12 March 2013), which measures per BS.1770-3; the gated result equals BS.1770-4 for 5.1 and stereo.

In the source's words:

- `loudness.integrated`: The loudness shall be measured across all channels, except LFE (Low-Frequency Enhancement) in units of LKFS per ATSC RP/A85 (Doc. A/85 12 March 2013). The Program must have an average loudness of -24lkfs, measured for the duration of the program, although if the material’s loudness measures out of specification at any point, the material is subject to rejection. [...] If the material’s loudness measures higher or lower than our loudness specification, the material will be subject to rejection. SAP and DVS are subject to the above loudness and dynamic range requirements.
- `peak.true`: Audio true peaks shall not exceed -2dBFS
- `format.sample_rate`: MXF files shall have 8 audio PCM 16 (16 bits @ 48 kHz PCM) or 8 audio PCM 24 (24 bits @ 48 kHz PCM) channels per SMPTE ST 377-4:2012. Dolby E is not accepted.
- `format.bit_depth`: MXF files shall have 8 audio PCM 16 (16 bits @ 48 kHz PCM) or 8 audio PCM 24 (24 bits @ 48 kHz PCM) channels per SMPTE ST 377-4:2012.
- `format.layout`: All material shall be delivered per SMPTE ST 296:2012 with 5.1 digital sound per ITU-R BS 775-3 (08/2012). [...] 5.1 digital surround shall be in phase. Channel 1: Left, 2: Right, 3: Center, 4: LFE Low Frequency Enhancement, 5: Left surround, 6: Right surround, 7: DVS, SAP or Mono, 8: Mono, 9 to 12: (n/a or not used). [...] Programming shall be created such that any down mix from 5.1 to stereo or mono represents the original mix. [...] Stereo, 2-channel and monophonic deliveries require prior authorization.
- `reference.tone`: At the head of the material, a 30-second test signal of color bars per SMPTE RP 219:2002 and an audio test tone of 1kHz. at -20dBFS shall reflect the recorded material

Sources:

- **READ** (primary) Technical Specifications for Broadcast Program Material, August 2018 (August 2018) · Fox Networks · <https://assets.foxdcg.com/dpp-uploaded/images/articles/59bc1012fdcf74001fb5d07f/Broadcast_AUG_2018_TechnicalSpecs.pdf> · retrieved 2026-09-06. Read from the PDF's text layer. The document dates from 2018 and cites A/85:2013; no newer public programme specification was found on 2026-09-06 (Fox's February 2024 document covers commercial material, see fox-commercial-2024). Fox delivers as MXF, which cumple does not read; check the PCM printmaster before wrapping. The 8-track layout with mono on 7 and 8 is accepted as 5.1+lt-rt when those tracks fold down from the bed.
- **TOOL_DEFAULT** (default) Loudness tolerance · cumple · retrieved 2026-09-06. Fox states -24 LKFS with no tolerance; ±2 is the A/85 window applied as the tool's default.

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

## Apple Music immersive audio (Dolby Atmos, 5.1, 7.1) (`apple-immersive`)

Apple Video and Audio Asset Guide, Immersive Audio Source Profile, the delivery rules for Dolby Atmos, 5.1 and 7.1 music on Apple Music. Integrated loudness never above -18 LKFS and true peak never above -1 dBTP, both per BS.1770-4; Dolby Atmos as a BWF ADM file at 24-bit 48 kHz, 5.1 and 7.1 as LPCM; the immersive source within 50 ms of the stereo master's length; no full-frequency content in the LFE; no Atmos generated from a stereo mix. cumple measures the bed or re-render it can read (a 5.1, 7.1 or 7.1.4 WAV), not rendered objects.

Loudness rules:

- ≤ -18 LUFS integrated, BS.1770-4 · A ceiling, not a target: Apple states no lower bound for immersive music.

In the source's words:

- `loudness.integrated`: Integrated loudness should not exceed -18 LKFS measured as per ITU-R BS. 1770-4
- `peak.true`: True-peak level should not exceed -1 dB TP measured as per ITU-R BS. 1770-4
- `format.container`: Broadcast Wave Format Audio Definition Model (BWF ADM) file [for Dolby Atmos]; LPCM in .mov containers with channel assignments [for 5.1 and 7.1]
- `format.sample_rate`: 24-bit linear pulse code modulation (LPCM) audio at 48kHz
- `format.bit_depth`: 24-bit linear pulse code modulation (LPCM) audio at 48kHz [Dolby Atmos]; 48 kHz with 16-bit or 24-bit resolution [5.1 and 7.1]
- `format.lfe_band`: Full-frequency content should not be present in the Low-Frequency Effects (LFE) channel
- `sync.stereo_offset`: Duration difference between stereo and immersive sources: less than or equal to 50 milliseconds
- `gapless.boundary`: Track boundaries must align no more than half a frame (1,000 samples @ 48 kHz) earlier or later with stereo versions [gapless albums]
- `source.no_upmix`: Dolby Atmos audio files generated from stereo mixes are not allowed.

Sources:

- **READ** (primary) Apple Video and Audio Asset Guide, Immersive Audio Source Profile, 5.3.18 (October 13, 2025) · Apple · <https://help.apple.com/itc/videoaudioassetguide/en.lproj/itcf946aaace.html> · retrieved 2026-09-06. cumple reads a BWF ADM as a plain multichannel WAV and does not render beds and objects; measure the 5.1, 7.1 or 7.1.4 bed or the re-render the mastering tool exports, and read the sheet as that render's loudness. The 5.1 and 7.1 .mov container is not in cumple's container list, so check the PCM before wrapping.
- **READ** (supporting) Apple Music Provider Support: Delivering Dolby Atmos audio · Apple · <https://itunespartner.apple.com/music/support/5216-delivering-dolby-atmos-audio> · retrieved 2026-09-06. States that Dolby Atmos can only be delivered through Transporter and that Atmos generated from stereo mixes, upmixed or de-mixed, is not allowed.
- **TOOL_DEFAULT** (default) LFE corner frequency · cumple · retrieved 2026-09-06. Apple forbids full-frequency content in the LFE without naming a corner; cumple checks one octave above 120 Hz, the usual LFE low-pass.

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

## Amazon MGM Studios 2.0 (discrete mono files) (`amazon-2.0-package`)

Amazon MGM Studios near-field 2.0 printmaster. True stereo Lo/Ro only; -27 LKFS ±2 LU on the BS.1770-1 scale with Dolby Dialogue Intelligence, -2 dBTP, 48 kHz / 24-bit PCM, one flattened mono .wav per channel, no leader, slate or 2-pop; true D/M/E stems must reproduce the printmaster.

Loudness rules:

- -27 ±2 LKFS dialogue-gated, BS.1770-1 · Amazon measures with Dolby Dialogue Intelligence on Nugen VisLM2. cumple approximates that gate with an open speech detector and says so on every sheet. Amazon states no speech-share switch: a mix with no dialogue is measured as full programme, and the sheet says so.

In the source's words:

- `loudness.dialogue_gated`: Follow the Loudness guidelines noted below for Near Field 5.1/2.0 mixes only. [...] Loudness Target: -27 LKFS ± 2 LU. Loudness Scale: 1770-1 with Dialogue Gating exclusion algorithm/Dolby Dialogue Intelligence. [QC Guidelines for Loudness:] If the 1770-1 loudness scale with dialogue gating exclusion algorithm/Dolby Dialogue Intelligence is not within -27 +/- 2 LU range, please flag as a rejection on the QC report.
- `peak.true`: Maximum True Peak: -2dbTP
- `format.sample_rate`: Audio Codec: PCM. Audio Sample Rate: 48kHz. Audio Bit Depth: 24-bit. Audio Bit Rate: Uncompressed.
- `format.bit_depth`: Audio Codec: PCM. Audio Sample Rate: 48kHz. Audio Bit Depth: 24-bit. Audio Bit Rate: Uncompressed.
- `format.packaging`: Each .wav file must be flattened. Discrete .wav files required per channel. Interleaved audio is not acceptable.
- `format.layout`: 2.0 mixes must be provided as true stereo Left Only/Right Only (Lo/Ro) audio. [Track Layouts:] 2.0: Lo, Ro. [...] Mono and 2.0 audio assets do not require LFE Channel Filtering, as they do not include an LFE channel.
- `padding.head`: Do not include leader, slate, 2-pop, or post roll. [...] Start of File: 00:00:00:00. First Frame of Program: 00:00:00:00.
- `stems.sum`: All Dialogue, Music, and Effects stems must be delivered as “True D/M/E” files. When played back together a True D/M/E will result in an OV Printmaster experience with matching mix levels.
- `stems.me_speech`: Elements Not to Be Included in the M&E: Discernible dialogue of any kind. This includes foreign language and discernible dialogue in groups or walla.

Sources:

- **READ** (primary) Asset Technical Specifications: Audio (Nearfield WAV, Audio Asset Specs, Track Layouts) · Amazon MGM Studios · <https://portal.amazonstudios.com/hc/en-us/articles/15986845319323-Asset-Technical-Specifications> · retrieved 2026-09-04. Public article on the Amazon Studios partner portal, read directly in a browser (command-line fetches get a 403).
- **READ** (supporting) Delivery & QC: Near Field Loudness Levels, QC Guidelines for Loudness, M&E · Amazon MGM Studios · <https://portal.amazonstudios.com/hc/en-us/articles/15986851525147-Delivery-QC> · retrieved 2026-09-04. Names Nugen Audio VisLM2 as the reference meter and states that Dolby Atmos audio has no loudness requirement.
- **TOOL_DEFAULT** (default) Stem residual and leader threshold · cumple · retrieved 2026-09-04. Amazon publishes no null-test tolerance; -60 dBFS residual after alignment is the tool's choice. Leader, slate and 2-pop are forbidden without a number; cumple flags more than 2 s of leading silence.

## Amazon MGM Studios 5.1 (discrete mono files) (`amazon-5.1-package`)

Amazon MGM Studios near-field 5.1 printmaster. -27 LKFS ±2 LU on the BS.1770-1 scale with Dolby Dialogue Intelligence, -2 dBTP, 48 kHz / 24-bit PCM, one flattened mono .wav per channel in L R C LFE Ls Rs order, LFE low-passed at 120 Hz, no leader, slate or 2-pop; true D/M/E stems must reproduce the printmaster. Nugen VisLM2 is Amazon's reference meter and a QC vendor rejects anything outside the window.

Loudness rules:

- -27 ±2 LKFS dialogue-gated, BS.1770-1 · Amazon measures with Dolby Dialogue Intelligence on Nugen VisLM2. cumple approximates that gate with an open speech detector and says so on every sheet. Amazon states no speech-share switch: a mix with no dialogue is measured as full programme, and the sheet says so.

In the source's words:

- `loudness.dialogue_gated`: Loudness Target: -27 LKFS ± 2 LU. Loudness Scale: 1770-1 with Dialogue Gating exclusion algorithm/Dolby Dialogue Intelligence. [QC Guidelines for Loudness:] If the 1770-1 loudness scale with dialogue gating exclusion algorithm/Dolby Dialogue Intelligence is not within -27 +/- 2 LU range, please flag as a rejection on the QC report.
- `peak.true`: Maximum True Peak: -2dbTP
- `format.sample_rate`: Audio Codec: PCM. Audio Sample Rate: 48kHz. Audio Bit Depth: 24-bit. Audio Bit Rate: Uncompressed.
- `format.bit_depth`: Audio Codec: PCM. Audio Sample Rate: 48kHz. Audio Bit Depth: 24-bit. Audio Bit Rate: Uncompressed.
- `format.packaging`: Each .wav file must be flattened. Discrete .wav files required per channel. Interleaved audio is not acceptable.
- `format.layout`: Track Layouts: 5.1: L, R, C, LFE, Ls, Rs. [...] If Surround Sound does not include an LFE channel then provide a 5.0 track layout.
- `format.lfe_band`: LFE Channel Filter: Low-Pass filter @ 120Hz 24 dB/octave
- `padding.head`: Do not include leader, slate, 2-pop, or post roll. [...] Start of File: 00:00:00:00. First Frame of Program: 00:00:00:00.
- `stems.sum`: All Dialogue, Music, and Effects stems must be delivered as “True D/M/E” files. When played back together a True D/M/E will result in an OV Printmaster experience with matching mix levels.
- `stems.me_speech`: Elements Not to Be Included in the M&E: Discernible dialogue of any kind. This includes foreign language and discernible dialogue in groups or walla.

Sources:

- **READ** (primary) Asset Technical Specifications: Audio (Nearfield WAV, Audio Asset Specs, Track Layouts) · Amazon MGM Studios · <https://portal.amazonstudios.com/hc/en-us/articles/15986845319323-Asset-Technical-Specifications> · retrieved 2026-09-04. Public article on the Amazon Studios partner portal, read directly in a browser (command-line fetches get a 403).
- **READ** (supporting) Delivery & QC: Near Field Loudness Levels, QC Guidelines for Loudness, M&E · Amazon MGM Studios · <https://portal.amazonstudios.com/hc/en-us/articles/15986851525147-Delivery-QC> · retrieved 2026-09-04. Names Nugen Audio VisLM2 as the reference meter and states that Dolby Atmos audio has no loudness requirement.
- **TOOL_DEFAULT** (default) Stem residual, leader threshold and LFE check corner · cumple · retrieved 2026-09-04. Amazon publishes no null-test tolerance; -60 dBFS residual after alignment is the tool's choice. Leader, slate and 2-pop are forbidden without a number; cumple flags more than 2 s of leading silence. The LFE check looks one octave above the 120 Hz corner, where Amazon's 24 dB/octave filter leaves -24 dB.

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

## Disney A85, General Entertainment (Hulu originals, ABC, FX) (`disney-a85`)

Disney Media Tech Specs, Production Audio GE v1.7 (2024-01-24), the "Disney A85" standard for General Entertainment content delivered to Disney's mastering vendor (Hulu originals, ABC, FX, Freeform, National Geographic). -24 LKFS ±2 for 5.1 and 2.0 mixes, dialog as the anchor where the meter allows and the whole act otherwise, all channels but the LFE, G10 gating per BS.1770-3/-4; true peak never above -2 dBFS, with some linear workflows at -6 dBFS; 1 kHz tone at -20 dBFS. Dubs of an A85 mix are made to Disney R128 (see disney-r128).

Loudness rules (any one applicable rule may pass):

- -24 ±2 LKFS dialogue-gated, BS.1770-4 · Disney: 'Where metering allows, dialog should be used as the anchor element for this measurement.' cumple approximates the dialog anchor with an open speech detector and says so on every sheet.
- -24 ±2 LUFS integrated, BS.1770-4 · Disney: 'If dialog is not available (such as in a music segment), or the meter does not allow dialog intelligibility, a long-term integrated measurement should be used over the duration of the entire act.' Either reading inside the window passes.

In the source's words:

- `loudness.integrated`: Disney A85 Requirements. 5.1 Mix: Program Target (Tolerance) -24LKFS (± 2). 2.0 Mix: Program Target (Tolerance) -24LKFS (± 2). [...] The target reference level for audio loudness is -24 LKFS, plus or minus 2 dB. Special care should be taken to bring the audio loudness to -24LKFS at the beginning and end of acts to ensure smooth program to interstitial (commercials, promos, etc.) transitions. [...] All audio channels of the 5.1, with the exception of the LFE, shall be measured. For stereo material, both audio channels shall be measured. Measurement of Program: Program loudness should be measured using the relative level G10 gating provided for in BS 1770-3 or -4.
- `loudness.dialogue_gated`: Where metering allows, dialog should be used as the anchor element for this measurement. If dialog is not available (such as in a music segment), or the meter does not allow dialog intelligibility, a long-term integrated measurement should be used over the duration of the entire act.
- `peak.true`: True Peak: -2 dBFS* (see note below). [...] * Maximum true peak levels are not to exceed -2 dBFS, per BS.1770, some broadcast workflows require a True Peak of -6 dBFS, check with your Disney rep for your specific workflow.
- `format.layout`: Disney Digital Supply Chain Trailer Specifications: Embedded Audio Channel Layout - 8 Channel, 5.1 + 2.0. 5.1: L, R, C, Lfe, Ls, Rs. Stereo: Left, Right. One channel per audio track (Discrete, Mono).
- `reference.tone`: 1kHz Reference Tone: -20 dBFS

Sources:

- **READ** (primary) Disney Media Tech Specs: Production, Audio, Production Audio GE, Loudness Standards, ATSC A85, v1.7 (2024-01-24) · The Walt Disney Company · <https://mediatechspecs.disney.com/production/audio/production-audio-ge> · retrieved 2026-09-06. Read directly in a browser (the site is a JavaScript app). Disney measures from First Frame of Action to Last Frame of Action; cumple measures the whole delivered file, so trim leaders and tone before checking. The -6 dBFS variant for some linear workflows is not a rule here; ask the Disney representative and lower true_peak_max in a user profile if it applies.
- **READ** (supporting) Disney Digital Supply Chain Trailer Specifications, 2024 v1.2 (2025-03-03) · The Walt Disney Company · <https://disneymasteringspecs.s3.us-east-1.amazonaws.com/Disney_Digital_Supply_Chain_Trailer_Specs_2024_v1_2_2025_03_03_e2ee0710cc.pdf> · retrieved 2026-09-06. The eight-channel 5.1 + 2.0 track layout is quoted from the trailer specification; the GE page itself lists 5.1 and 2.0 mixes without a track table.
- **SE** (supporting) Disney Media Tech Specs: Production Audio (format values) · The Walt Disney Company · <https://mediatechspecs.disney.com/production/audio/production-audio> · retrieved 2026-09-03. The 48 kHz / 24-bit format values come from search extraction of this page and were not re-read on the site.

## Disney+ near-field 2.0 stereo (`disney-plus-2.0`)

Disney Media Tech Specs, Audio v1.7 (2024-01-24), near field 2.0 stereo. Program target -24 LKFS ±0.4 with BS.1770-3/-4 gating and no dialogue norm for stereo; loudness range 0 to 20 LU as a guideline; -2 dBTP.

Loudness rules:

- -24 ±0.4 LUFS integrated, BS.1770-4 · For 2.0 stereo Disney's table gives a Program Target only; Maximum Program and Dialogue Norm Target are N/A.

In the source's words:

- `loudness.integrated`: 2.0 Stereo: Program Target (Tolerance): -24 LKFS (± 0.4). Maximum Program: N/A. Dialogue Norm Target (Tolerance): N/A. [...] Measurement of Program: Program loudness should be measured using the relative level G10 gating provided for in BS 1770-3 or -4.
- `dynamics.lra`: Loudness Range: 0 - 20 LU (Guideline Only)
- `peak.true`: True Peak: -2dBTP. [...] Maximum True Peak, measured as dBTP, is the maximum peak level permitted within the soundtrack. There is no expectation that audio should always peak to this level. True Peak is measured on all configurations.

Sources:

- **READ** (primary) Disney Media Tech Specs: Mastering, Audio Specifications, Loudness Standards, v1.7 (2024-01-24) · The Walt Disney Company · <https://mediatechspecs.disney.com/mastering/audio/audio-specifications> · retrieved 2026-09-04. Read directly in a browser (the site is a JavaScript app). Disney measures from First Frame of Action to Last Frame of Action; cumple measures the whole delivered file, so trim leaders before checking.
- **SE** (supporting) Disney Media Tech Specs: Production Audio (format values) · The Walt Disney Company · <https://mediatechspecs.disney.com/production/audio/production-audio> · retrieved 2026-09-03. The 48 kHz / 24-bit format values come from search extraction of this page and were not re-read on the site.

## Disney+ near-field 5.1, 7.1 and Atmos (`disney-plus-5.1`)

Disney Media Tech Specs, Audio v1.7 (2024-01-24), near field 5.1, 7.1 and Atmos. Dialogue norm -27 LKFS ±0.4 measured with Dolby Dialogue Intelligence on the full composite program; mixes with under 15 % speech use the program target -24 LKFS ±0.4 with BS.1770-3/-4 gating; program loudness never above -20 LKFS; loudness range 0 to 20 LU as a guideline; beds and objects at or below -2 dBTP.

Loudness rules:

- -27 ±0.4 LKFS dialogue-gated, BS.1770-1, if speech ≥ 15 % · Disney's Dialogue Norm is measured with Dolby's Dialogue Intelligence, 'the dialog gated setting', on the full composite program. cumple approximates that gate with an open speech detector and says so on every sheet. Disney names no BS.1770 revision for it; the dialog-gated setting of the meters it names has no relative gate, which is BS.1770-1.
- -24 ±0.4 LUFS integrated, BS.1770-4, if speech < 15 %
- ≤ -20 LUFS integrated, BS.1770-4 · Maximum Program: the BS.1770-3/-4 gated program loudness may never exceed -20 LKFS, whatever the speech share.

In the source's words:

- `loudness.dialogue_gated`: Dialogue Norm Target (Tolerance): -27 LKFS (± 0.4). [...] Measurement of Dialogue Norm: Dialogue Norm should be measured using Dolby’s Dialogue Intelligence Algorithm which may commonly be referred to as the “dialog gated” setting. Measurement should include the full composite program, not just the center channel or dialogue stem.
- `loudness.integrated`: Near-Field Atmos and 5.1 mixes that measure a Speech/Dialogue Percentage of less than the minimum 15% will use the Program Target standard of -24 LKFS ± 0.4 and not the Dialogue Norm Target. [...] Maximum Program: -20 LKFS. [...] Measurement of Program: Program loudness should be measured using the relative level G10 gating provided for in BS 1770-3 or -4.
- `dynamics.lra`: Loudness Range: 0 - 20 LU (Guideline Only)
- `peak.true`: True Peak: -2dBTP. [...] Maximum True Peak, measured as dBTP, is the maximum peak level permitted within the soundtrack. There is no expectation that audio should always peak to this level. True Peak is measured on all configurations. For Atmos printmasters, the requirement is to limit all beds and objects individually to -2dBTP or lower. This may yield an overall Atmos Printmaster True Peak level that exceeds -2dBTP when measured via the 5.1 re-render.

Sources:

- **READ** (primary) Disney Media Tech Specs: Mastering, Audio Specifications, Loudness Standards, v1.7 (2024-01-24) · The Walt Disney Company · <https://mediatechspecs.disney.com/mastering/audio/audio-specifications> · retrieved 2026-09-04. Read directly in a browser (the site is a JavaScript app). Disney measures from First Frame of Action to Last Frame of Action; cumple measures the whole delivered file, so trim leaders before checking.
- **READ** (supporting) Disney Media Tech Specs: Mastering, Audio Specifications, Master Deliverables, v1.7 · The Walt Disney Company · <https://mediatechspecs.disney.com/mastering/audio/audio-specifications?tab=master-deliverables> · retrieved 2026-09-04. Deliverables are Pro Tools sessions with flattened Broadcast WAV files per track.
- **SE** (supporting) Disney Media Tech Specs: Production Audio (format values) · The Walt Disney Company · <https://mediatechspecs.disney.com/production/audio/production-audio> · retrieved 2026-09-03. The 48 kHz / 24-bit format values come from search extraction of this page and were not re-read on the site.

## Disney R128 (dubs and territories on R 128) (`disney-r128`)

Disney Media Tech Specs, Localized Audio v1.5 (2022-02-28), the "Disney R128" standard used when a mix that originated in ATSC A85 is dubbed, and for territories on EBU R 128. -23 LUFS ±0.5, true peak never above -3 dBTP, short-term loudness never above -15, loudness range at most 20 LU, 1 kHz tone at -18 dBFS, measured from first to last frame of action. Disney also states a dialogue range of ±7 LU, which cumple does not measure.

Loudness rules:

- -23 ±0.5 LUFS integrated, BS.1770-4

In the source's words:

- `loudness.integrated`: Disney R128 Standard. Program Target (Tolerance): -23 LUFS (± 0.5) LU. [...] All measurements are based on the BS-1770 standard. All measurements are from First Frame of Action (FFOA) to Last Frame of Action (LFOA).
- `peak.true`: Maximum True Peak: -3 dBTP*. [...] *Please note: dBTP, this is the maximum peak level permitted - there is no expectation that audio should always peak to this level. True Peak is measured on all configurations (2.0, 5.1, Atmos,etc).
- `dynamics.short_term_max`: Maximum Short-Term Loudness: -15 LU
- `dynamics.lra`: Maximum Loudness Range: 20 LUFS
- `dialogue.range`: Dialogue Range: ±7 LU
- `reference.tone`: 1kHz Reference Tone: -18 dBFS

Sources:

- **READ** (primary) Disney Media Tech Specs: Localization, Audio, Localized Audio, Loudness Standards, Disney R128, v1.5 (2022-02-28) · The Walt Disney Company · <https://mediatechspecs.disney.com/localization/audio/localized-audio?tab=loudness-standards&spec=disney-r128> · retrieved 2026-09-06. Read directly in a browser (the site is a JavaScript app). Disney measures from First Frame of Action to Last Frame of Action; cumple measures the whole delivered file, so trim leaders and tone before checking. The dialogue range clause is recorded but not measured. The page names no BS.1770 revision; cumple applies BS.1770-4 gating, which is what R 128 specifies.

## Disney in-home trailer (Digital Supply Chain) (`disney-trailer`)

Disney Digital Supply Chain Trailer Specifications 2024 v1.2 (2025-03-03), in-home trailers. The composite mix follows ATSC A85 (-24 LKFS ±2, -2 dBTP), or the Disney Near Field standard when the trailer is exclusive to direct-to-consumer platforms; eight embedded channels as 5.1 plus 2.0, one channel per track; exactly one second of black and silence at head and tail; a partially filled M&E with no discernible words. Theatrical trailers are out of scope. For a direct-to-consumer trailer mixed to Near Field, check with disney-plus-5.1 or disney-plus-2.0 instead.

Loudness rules:

- -24 ±2 LUFS integrated, BS.1770-4 · The trailer specification delegates the numbers to ATSC A85 as stated on Disney's Production Audio GE page: -24 LKFS ±2, measured over the whole trailer with BS.1770-3/-4 gating, all channels but the LFE.

In the source's words:

- `loudness.integrated`: Audio Loudness Specification. Trailers for In-home distribution should generally follow the ATSC A85 guidelines. Trailers exclusive to “Direct to Consumer” streaming platforms will also be accepted in the Near Field loudness specification. Theatrical trailers for release in digital cinema may have different requirements, not covered in this document. [...] Audio Loudness analysis (for composite mix only): ATSC A85 or Near Field per guidelines.
- `peak.true`: Disney A85 Requirements (Production Audio GE): True Peak: -2 dBFS* (see note below). * Maximum true peak levels are not to exceed -2 dBFS, per BS.1770, some broadcast workflows require a True Peak of -6 dBFS, check with your Disney rep for your specific workflow.
- `format.layout`: Embedded Audio Channel Layout - 8 Channel, 5.1 + 2.0. 5.1: L, R, C, Lfe, Ls, Rs. Stereo: Left, Right. One channel per audio track (Discrete, Mono).
- `padding.head`: Program Layout & Conformance is DPO. One (1) second of black video, silent audio at head and tail. Video timecode start at 00:00:00:00. Audio program matches start, end and length of video.
- `padding.tail`: One (1) second of black video, silent audio at head and tail.
- `padding.head_min`: One (1) second of black video, silent audio at head and tail.
- `padding.tail_min`: One (1) second of black video, silent audio at head and tail.
- `duration.av`: Audio program matches start, end and length of video.
- `stems.me_speech`: Music & Effects Tracks (for dubbing facility QC): Follows Partially-Filled M&E Guideline. No discernable spoken words. Not missing any music or effects from the main program. Volume match to main program.

Sources:

- **READ** (primary) Disney Digital Supply Chain Trailer Specifications, 2024 v1.2 (2025-03-03) · The Walt Disney Company · <https://disneymasteringspecs.s3.us-east-1.amazonaws.com/Disney_Digital_Supply_Chain_Trailer_Specs_2024_v1_2_2025_03_03_e2ee0710cc.pdf> · retrieved 2026-09-06. PDF linked from mediatechspecs.disney.com, Production, Trailers. The document quotes no sample rate or bit depth of its own; 48 kHz is the Disney audio standard the trailer spec sits inside. The M&E rule is recorded; cumple checks an M&E for speech with cumple check on the M&E file itself, since the trailer package does not carry it in the same file.
- **READ** (primary) Disney Media Tech Specs: Production, Audio, Production Audio GE, Loudness Standards, ATSC A85, v1.7 (2024-01-24) · The Walt Disney Company · <https://mediatechspecs.disney.com/production/audio/production-audio-ge> · retrieved 2026-09-06. The loudness and peak numbers the trailer specification delegates to.

## Hulu content partner guidebook (2018, stale) (`hulu-2018`)

Hulu's public Content Partner Guidebook v5.0 from 2018. -24 LKFS per BS.1770-4, sample peak -2 dBFS, 48 kHz LPCM 16 or 24-bit interleaved, 8-channel L R C LFE Ls Rs Lt Rt. Kept for reference; Hulu originals now follow Disney's General Entertainment path, the disney-a85 profile.

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

Netflix branded near-field 2.0 original-language mix (Sound Mix Specifications & Best Practices, OC-1-6). Lo/Ro preferred, or Lt/Rt; -27 LKFS ±2 dialogue-gated per BS.1770-1 over the entire program; -2 dBTP; mono compatible; 48 kHz / 24-bit discrete LPCM .wav or .bwav. Netflix's QC partners flag loudness only after both the dialogue-gated and the full-program measurement fail their ±3 windows.

Loudness rules (any one applicable rule may pass):

- -27 ±2 LKFS dialogue-gated, BS.1770-1, if speech ≥ 15 % · Netflix measures with Dolby Dialogue Intelligence. cumple approximates that gate with an open speech detector and says so on every sheet. QC partners flag at ±3 LU to absorb meter differences; the delivery window is ±2.
- -24 ±2 LUFS integrated, BS.1770-4, if speech < 15 % · Netflix states the under-15 % dialogue switch for near field Atmos and 5.1 mixes in its Best Practices. cumple applies the same switch to 2.0, because a mix with no dialogue has no dialogue-gated value; that extension is the tool's choice.
- -24 ±3 LUFS integrated, BS.1770-4 (fallback) · Netflix's QC procedure: if the dialogue-gated analysis fails, measure full program per BS.1770-4; if that passes, do not flag. The QC windows are -27 ±3 and -24 ±3.

In the source's words:

- `loudness.dialogue_gated`: Provide a Lo/Ro or LT/RT mix with -27 LKFS (+/- 2 LU) dialogue loudness using ITU-R BS.1770-1 measured over entire program.
- `loudness.integrated`: When near field Atmos or 5.1 mixes measure at less than 15% dialogue, program target measurement will be used instead (-24 LKFS +/- 2 LU - ITU BS 1770-3 or -4).
- `loudness.fallback`: If the dialogue-gated analysis FAILS, proceed with measuring the mix against the ITU-R BS. 1770-4 full program algorithm. [...] If the full program analysis PASSES, do NOT flag in the QC Request. If the full program analysis FAILS, flag the Loudness LKFS Out of Spec as an ISSUE and include both the measurements for 1770-1 and 1770-4 or 1770-2/1770-3.
- `peak.true`: Do not exceed +18dBu (-2 dBFS) maximum level (true-peak) over reference of -20 dBFS, achieved by peak limiting and not lowering the mix level. [Best Practices:] Set a True Peak limiter at -2.3 dBFS for all audio deliverables.
- `dynamics.lra`: The following loudness range (LRA) values will play best on the service: [...] 2.0 program LRA between 4 and 18 LU. Dialog LRA of 10 LU or less. [Best Practices, which the page says are not technical specifications]
- `mono.compat`: Lo/Ro or LT/RT mix to be mono compatible.
- `format.sample_rate`: 48kHz/24-bit for Original Language Mix or M&E Mix - applies to Stems & Mix Masters.
- `format.bit_depth`: 48kHz/24-bit for Original Language Mix or M&E Mix - applies to Stems & Mix Masters.
- `format.channels`: Mono audio is acceptable if the program’s original source is mono and no stereo and/or 5.1 mix exists. Mono audio must be duplicated on channels 1 & 2 and delivered as 2-channel.
- `format.layout`: Provide a Lo/Ro or LT/RT mix [...] Lo/Ro mix is preferred.
- `format.container`: Lossy or lossless audio compression is never allowed. Audio must be standard or RF64 discrete LPCM .wav or .bwav files.
- `format.packaging`: Discrete audio is required, except in the following circumstances: When muxed audio is inherent to the source, such as audio in an IMF, Quicktime or Atmos® BWAV ADM container. Interleaved Secondary Audio .wav deliveries.
- `stems.sum`: For Original Version: Provide 5.1 Dialog, Music and Effects stems that equal the 5.1 mix when combined.
- `stems.me_speech`: Provide a fully filled 5.1 surround submix containing only Music & Effects (no dialog).

Sources:

- **READ** (primary) Netflix Sound Mix Specifications & Best Practices, OC-1-6 (2024-10-29) · Netflix · <https://studiopartner.netflix.net/studio/branded-sound-mix-spec-and-best-practices> · retrieved 2026-09-04. Read directly in a browser; the page is a JavaScript app that renders nothing for command-line fetchers. The LRA values and the under-15 % dialogue rule sit in its Best Practices section, which the page says are not technical specifications.
- **READ** (supporting) Loudness and True Peaks: How to Measure and When to Flag (2024-04-30) · Netflix · <https://studiopartner.netflix.net/studio/loudness-and-true-peaks-how-to-measure-and-when-to-flag> · retrieved 2026-09-04. QC-partner thresholds: -27 ±3 dialogue-gated (BS.1770-1), -24 ±3 full program (BS.1770-4), the fallback procedure, and the channel configuration (2.0 - Lt/Rt). Its true-peak flag threshold is -1 dBTP; the delivery specification stays at -2 dBTP.
- **TOOL_DEFAULT** (default) Speech switch on 2.0 and stem residual default · cumple · retrieved 2026-09-04. Netflix states the under-15 % dialogue switch for Atmos and 5.1 mixes; applying it to 2.0 is the tool's extension. Netflix publishes no null-test tolerance; -60 dBFS residual after alignment is the tool's choice.

## Netflix 5.1 near-field printmaster (`netflix-5.1`)

Netflix branded near-field 5.1 original-language mix (Sound Mix Specifications & Best Practices, OC-1-6). -27 LKFS ±2 dialogue-gated per BS.1770-1 over the entire program; -24 ±2 full program when the mix measures under 15 % dialogue; -2 dBTP; 48 kHz / 24-bit discrete LPCM .wav or .bwav in L R C LFE Ls Rs order; DX, MX and FX stems must equal the 5.1 mix when combined. Netflix's QC partners flag loudness only after both the dialogue-gated and the full-program measurement fail their ±3 windows.

Loudness rules (any one applicable rule may pass):

- -27 ±2 LKFS dialogue-gated, BS.1770-1, if speech ≥ 15 % · Netflix measures with Dolby Dialogue Intelligence. cumple approximates that gate with an open speech detector and says so on every sheet. QC partners flag at ±3 LU to absorb meter differences; the delivery window is ±2.
- -24 ±2 LUFS integrated, BS.1770-4, if speech < 15 % · From the Best Practices section: near field Atmos or 5.1 mixes that measure under 15 % dialogue use the program target instead.
- -24 ±3 LUFS integrated, BS.1770-4 (fallback) · Netflix's QC procedure: if the dialogue-gated analysis fails, measure full program per BS.1770-4; if that passes, do not flag. The QC windows are -27 ±3 and -24 ±3.

In the source's words:

- `loudness.dialogue_gated`: Meet a -27 LKFS (+/- 2 LU) dialogue loudness using ITU-R BS.1770-1 measured over entire program.
- `loudness.integrated`: When near field Atmos or 5.1 mixes measure at less than 15% dialogue, program target measurement will be used instead (-24 LKFS +/- 2 LU - ITU BS 1770-3 or -4).
- `loudness.fallback`: If the dialogue-gated analysis FAILS, proceed with measuring the mix against the ITU-R BS. 1770-4 full program algorithm. [...] If the full program analysis PASSES, do NOT flag in the QC Request. If the full program analysis FAILS, flag the Loudness LKFS Out of Spec as an ISSUE and include both the measurements for 1770-1 and 1770-4 or 1770-2/1770-3.
- `peak.true`: Do not exceed +18dBu (-2 dBFS) maximum level (true-peak) over reference of -20 dBFS, achieved by peak limiting and not lowering the mix level. [Best Practices:] Set a True Peak limiter at -2.3 dBFS for all audio deliverables.
- `dynamics.lra`: The following loudness range (LRA) values will play best on the service: 5.1 program LRA between 4 and 18 LU [...] Dialog LRA of 10 LU or less. [Best Practices, which the page says are not technical specifications]
- `format.sample_rate`: 48kHz/24-bit for Original Language Mix or M&E Mix - applies to Stems & Mix Masters.
- `format.bit_depth`: 48kHz/24-bit for Original Language Mix or M&E Mix - applies to Stems & Mix Masters.
- `format.container`: Lossy or lossless audio compression is never allowed. Audio must be standard or RF64 discrete LPCM .wav or .bwav files.
- `format.packaging`: Discrete audio is required, except in the following circumstances: When muxed audio is inherent to the source, such as audio in an IMF, Quicktime or Atmos® BWAV ADM container. Interleaved Secondary Audio .wav deliveries.
- `format.layout`: Channel Configuration: 5.1 - L,R,C,LFE,LS,RS
- `stems.sum`: For Original Version: Provide 5.1 Dialog, Music and Effects stems that equal the 5.1 mix when combined.
- `stems.me_speech`: Provide a fully filled 5.1 surround submix containing only Music & Effects (no dialog).

Sources:

- **READ** (primary) Netflix Sound Mix Specifications & Best Practices, OC-1-6 (2024-10-29) · Netflix · <https://studiopartner.netflix.net/studio/branded-sound-mix-spec-and-best-practices> · retrieved 2026-09-04. Read directly in a browser; the page is a JavaScript app that renders nothing for command-line fetchers. The LRA values and the under-15 % dialogue rule sit in its Best Practices section, which the page says are not technical specifications.
- **READ** (supporting) Loudness and True Peaks: How to Measure and When to Flag (2024-04-30) · Netflix · <https://studiopartner.netflix.net/studio/loudness-and-true-peaks-how-to-measure-and-when-to-flag> · retrieved 2026-09-04. QC-partner thresholds: -27 ±3 dialogue-gated (BS.1770-1), -24 ±3 full program (BS.1770-4), the fallback procedure, and the channel configuration. Its true-peak flag threshold is -1 dBTP; the delivery specification stays at -2 dBTP.
- **TOOL_DEFAULT** (default) Stem residual and LFE corner defaults · cumple · retrieved 2026-09-04. Netflix publishes no null-test tolerance; -60 dBFS residual after alignment is the tool's choice. Netflix states no LFE low-pass for the 5.1 master (200 Hz or lower is stated for the 2.0 fold-down); the 120 Hz corner is the tool's, and the check looks one octave above it.

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

## Peacock (NBCUniversal, community-reported) (`peacock`)

NBCUniversal publishes no Peacock audio delivery specification; the number here, -27 LKFS dialogue-gated, comes from a delivery vendor's guide that cites no source. Tolerance and the BS.1770 revision are the tool's defaults. Treat the grade as part of the result and confirm the target with NBCUniversal before delivering.

Loudness rules:

- -27 ±2 LKFS dialogue-gated, BS.1770-1 · The ±2 window and the BS.1770-1 gate follow the Netflix and Amazon convention for a dialogue-gated -27 target; neither is sourced from NBCUniversal.

In the source's words:

- `loudness.dialogue_gated`: Loudness Target: -27 LKFS dialogue-gated

Sources:

- **COMMUNITY** (primary) Peacock Delivery Guide: Avails and Specs · Molten Cloud · <https://moltencloud.com/blog-article/delivering-content-to-peacock-avails-specs-workflow> · retrieved 2026-09-06. A delivery vendor's summary that states the target without citing an NBCUniversal document. NBCUniversal's own creative-guidelines page for Peacock returned 404 on 2026-09-06, and no public Peacock programme specification was found; NBCU's public Linear Commercial Guidelines are the nbcu-commercial profile.
- **TOOL_DEFAULT** (default) Tolerance and gate revision · cumple · retrieved 2026-09-06. ±2 LU and the BS.1770-1 gate are the tool's defaults for a dialogue-gated -27 target.

## Looked for, not public (2026-09-06)

These companies were searched for on the date above and publish no delivery specification a tool can quote. A profile built from a rumour would carry a grade it does not deserve, so there is none.

- **Sony Pictures Entertainment and Sony Pictures Television**: no public delivery specification; SonyLIV's Indian spec is not a studio document
- **Lionsgate**: delivery schedules are per contract; third-party summaries only
- **Starz**: the affiliate page says only that advertisements follow ATSC A/85
- **Universal Pictures theatrical**: not public; NBCU's public document is the Linear Commercial Guidelines (nbcu-commercial)
- **Paramount+ originals**: not public; Paramount's public documents are the Pluto TV guide (paramount-pluto) and the CBS commercial manual (cbs-commercial)
- **HBO and Max brand A/V specs**: behind a login; the public WBD document is the Content Partner Hub audio spec (max-wbd)
- **Warner Bros. Pictures theatrical**: not public
- **NBCUniversal Peacock programme delivery**: no public primary; see peacock, graded COMMUNITY

