# Roadmap

What cumple does not do yet, ranked by the gap the competitive landscape found, and the rule by which this list advances. The evidence is [RELATED.md](RELATED.md) (what 21 documented tools list, and what three more open-source meters read when run here) and the run folder `docs/graph-runs/2026-09-12-competitive-landscape/`. Status moves in one direction: queued, proposed, building, merged, accepted; "out of scope" is the one status outside that ladder. The loop moves a row as far as merged; accepted is Victor's word.

## Items

| Id | Item | Gap, from RELATED.md | Status | PR | Receipt |
|---|---|---|---|---|---|
| R1 | Dialogue gate of the Dolby Dialogue Intelligence class: Silero VAD as an optional `cumple[vad]` backend, the heuristic stays the default | 3 of 21 tools list one (LM-Correct 2, Vantage, Pulsar); 6 profiles name the algorithm (netflix x2, amazon x2, disney-plus-5.1, apple-tv) | merged | #28 | `docs/graph-runs/2026-09-13-silero-vad/05-receipt.md` |
| R2 | Delivery codec and container conformance (AAC, AC-3, MP3, MXF) through an optional local ffmpeg, so a lossy file fails the clause instead of refusing to open | 3 of 9 QC platforms list it (Vidchecker, Pulsar, Netflix), 4 with Baton's codec list | merged | #27 | `docs/graph-runs/2026-09-12-ffmpeg-codec-conformance/05-receipt.md` |
| R3 | Dolby E detection (presence only; decoding is licensed) | 4 of 9 QC platforms handle it (eFF reads and writes it, Aurora checks its guard band, Vantage Pro detects it, Baton lists it as a codec) | queued | | |
| R4 | ADM and Atmos checks: chna track map, bed and object labels, per-track true peak; no rendering | 2 of 9 QC platforms (Baton, Vantage Pro), 0 of 12 meters; 3 profiles accept `adm-bwf` (apple-tv, apple-immersive, disney-plus-5.1); netflix-5.1 admits an ADM container only as a muxed-source exception | queued | | |
| R5 | Silence, dual mono, test tones, channel placement, mosquito tone | 3, 2, 2, 2 and 1 of 9 QC platforms | queued | | |
| R6 | 2-pop, leader and slate detection from the audio alone | 1 of 9 (Baton, container side); Amazon's two profiles forbid a leader without a number | queued | | |
| R7 | Audio-to-video duration and sync | 1 of 9 (Baton); needs the picture | out of scope until cumple reads picture | | |
| R8 | PyPI publishing through a trusted-publisher workflow | distribution, not a capability | queued; the last step needs Victor's PyPI account | | |
| R9 | Merge the mono tracks of a multi-stream MXF or MOV by their channel labels into one measurement; today such a file is refused with the stream count named | dpp-as11 and max-wbd list mxf; Apple immersive names LPCM in .mov with channel assignments | queued | | |
| R10 | Repair foundation: a Rust core `crates/cumple-dsp` seeded from cathar (MIT OR Apache-2.0) behind `cumple[repair]`, a streaming STFT, the module contract, De-click and De-clip, `cumple repair` with copy-only writes and a receipt, and the RX harness (`docs/REPAIR.md`, baselines RX 8 Standard, ffmpeg adeclick and adeclip, cathar) | iZotope RX is the benchmark since 2026-10-08; see the run folder below | proposed | | `docs/graph-runs/2026-10-08-rx-parity-landscape/05-receipt.md` |
| R11 | De-click v2: AR-residual detection, Interpolate up to RX's 4,000-sample rule, gap-wise Janssen interpolation | RX De-click and Interpolate | queued | | |
| R12 | Spectral editor v1 in the desktop app: WebGL2 spectrogram, time and time-frequency selection, Gain, De-click and Attenuate on a selection, a non-destructive edit list for undo and A/B | RX Spectral Repair and the interactive tools | queued | | |
| R13 | Spectral De-noise and Voice De-noise from cathar, brush and lasso selection; the harness gains SI-SDR and DNSMOS | RX Spectral De-noise, Voice De-noise | queued | | |
| R14 | Plugin shell: C++ CLAP over the core's C ABI, clap-wrapper for VST3 and AU, inserts with latency reporting, the editor through choc's WebView, signing and notarisation; ARA after | RX Connect and the RX ARA editor | queued | | |
| R15 | Move `app-qt` from PyQt6 (GPL-3.0-only) to PySide6 (LGPL-3.0); the Linux release bundles it | licence, not a capability | queued | | |

Victor's own list, not the loop's:

- The `EBU_TEST_SET_URL` secret so CI runs the 29 EBU cases.
- The manual rows in [QA.md](QA.md) (a DAW bounce, real mix versions, a real Windows and Linux machine).
- A custom domain, GitHub pins, a Frame.io action.
- The ffmpeg question below.
- Whether apple-immersive's containers list gains `mov` (its quoted clause permits LPCM in .mov containers; a PCM MOV now fails the clause it quotes).
- A Finder-launched cumple.app has a minimal PATH and will not see Homebrew's ffmpeg; the app needs a way to set CUMPLE_FFMPEG or a bundled decoder before compressed deliveries work from the desktop.
- Between one 32 ms window and 1.28 s, `--vad silero` reports a speech share where the heuristic reports unknown; the engine may then pick a different loudness rule for the same short file (R1, a known difference).

Decided against, and why: new landing-page columns for ffmpeg-normalize, r128gain or rsgain (each re-measures an engine already in the table: loudnorm, ffmpeg's ebur128, libebur128 1.2.6); watermark detection (outside a QC tool); more presets (39 destinations is a strength, not a gap).

Reversed on 2026-10-08: automatic repair had been decided against on 2026-09-12 as "outside a read-only QC tool". Victor decided that cumple becomes a full open-source DSP tool with every iZotope RX feature, benchmarked black-box against RX (never decompiled), with a spectral editor delivered as a plugin. The stack, the licence rules, the harness and the build order are in `docs/graph-runs/2026-10-08-rx-parity-landscape/04-recommendation.md`; `check`, `diff`, `watch` and the QC sheet keep working unchanged, and `repair` only ever writes a copy.

## How this roadmap advances

Each iteration is one graph run under `docs/graph-runs/` and one pull request: frame, work, a skeptic that has no history with the work, a recommendation, Victor's decision, a receipt. The loop is a servo with a retry cap, written the way `ecc:loop-design-check` asks: a decidable goal, boundaries beside it, damping, and judgment kept with a person.

Done, per iteration, all machine-judged:

1. `uv run ruff check src tests scripts` and `uv run ruff format --check src tests scripts` exit 0.
2. `uv run pytest` exits 0, run alone, never piped through another command.
3. The collected count, from `uv run pytest --collect-only | grep 'tests collected'`, is at least the previous iteration's, and the five pinned copies (README, CONTRIBUTING, QA.md, AI_USAGE.md, site/index.html) are re-pinned from that line.
4. `git diff main -- tests | grep '^-.*assert'` is empty, or the receipt names every removed assertion.
5. No em or en dash in README, ROADMAP, RELATED, the run folder, the page or AI_USAGE.
6. The CI run for the pull request concludes `success` (the release job skipping on a pull request is fine).
7. Research rows carry a URL and a read date, and the skeptic re-fetched at least five cited cells.

Boundaries: pinned figures change only through `scripts/conformance_report.py`, `scripts/benchmark_meters.py` and `scripts/perf.py`; no profile number changes; no new runtime dependency without a named reason in the receipt; no claim in README, the page or RELATED.md without a source or a run; the phrase "not checked" stays forbidden; no push to main; no Homebrew install that upgrades a tool the published comparison is pinned to (ffmpeg, learned on 12 September); the context that produced work never grades it.

Damping and stop: three CI fix rounds, one skeptic fix round, then stop and report; the loop also stops at any step only Victor can take. Victor delegated the merge of this loop's pull requests on 12 September 2026, after green checks and a clean fresh review; a version bump or a release still waits for him.

## Open for Victor

Closed 12 September: Victor chose to accept the machine's ffmpeg 9.0.1 (exact 8.0 was not restorable; its libraries had been upgraded) and the benchmark was re-run and re-pinned in PR #27.

## Runs

- `docs/graph-runs/2026-09-12-competitive-landscape/`: the landscape, this ranking, and the loop's first receipt.
- `docs/graph-runs/2026-09-12-ffmpeg-codec-conformance/`: R2, PR #27.
- `docs/graph-runs/2026-09-13-silero-vad/`: R1, PR #28. The loop's budget (research plus two builds) was spent there.
- `docs/graph-runs/2026-10-08-rx-parity-landscape/`: the RX parity research (five branches, skeptic, recommendation) that set R10 to R15 and the architecture.
