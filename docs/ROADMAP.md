# Roadmap

What cumple does not do yet, ranked by the gap the competitive landscape found, and the rule by which this list advances. The evidence is [RELATED.md](RELATED.md) (what 21 documented tools list, and what three more open-source meters read when run here) and the run folder `docs/graph-runs/2026-09-12-competitive-landscape/`. Status moves in one direction: queued, proposed, building, merged, accepted; "out of scope" is the one status outside that ladder. The loop moves a row as far as merged; accepted is Victor's word.

Decided 8 October 2026: cumple stops being a read-only QC tool and becomes a full open-source audio DSP tool with every iZotope RX module, benchmarked against RX (RX 8.5.1 Standard now, the latest RX when a trial is available), with a spectral editor for Victor's own use first and a plugin (CLAP, VST3, AU, ARA later). This reverses the 12 September ruling below that automatic repair is outside the tool. Reverse engineering is black-box only: run RX on signals with a held clean reference, measure, build from the literature and permissively licensed code. The architecture is path C of `docs/graph-runs/2026-10-08-rx-parity-landscape/04-recommendation.md`: a Rust core seeded from cathar (MIT OR Apache-2.0) behind `cumple[repair]`, the Python meters, CLI and app unchanged, a C++ plugin shell over the core later. Items R10 onward are that work, in build order.

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
| R10 | Repair foundation (build 1): `crates/cumple-dsp` (streaming STFT, module contract, De-click with Interpolate and De-clip ported from cathar), PyO3 wheel behind `cumple[repair]`, `cumple repair` with YAML chains and a sidecar receipt, the RX harness (`scripts/benchmark_repair.py`, `docs/REPAIR.md`, the RX 8 recipe) with ffmpeg and cathar baselines | RX parity run: De-click and De-clip are Victor's first family; nothing in cumple resynthesises audio today | proposed; spec `docs/superpowers/specs/2026-10-08-repair-foundation-design.md`, plan `docs/superpowers/plans/2026-10-08-repair-foundation.md`, plan skeptic pending | | |
| R11 | De-click v2: AR-residual detection (Godsill and Rayner), Interpolate up to RX's 4,000 samples, gap-wise Janssen (Mokrý and Rajmic 2025); ships only if it beats ffmpeg and cathar on ΔSDR at every damage level | `04-recommendation.md` section 10 | queued | | |
| R12 | Spectral editor v1 in the pywebview app: WebGL2 spectrogram from tiles the core computes, Gain, De-click and Attenuate on time, time-frequency and frequency selections, a non-destructive edit list that is both undo and A/B | `04-recommendation.md` section 6 | queued | | |
| R13 | Spectral De-noise and Voice De-noise from cathar, brush and lasso selection; the harness adds SI-SDR and DNSMOS | `04-recommendation.md` section 10 | queued | | |
| R14 | Plugin shell: C++ CLAP over the core's C ABI, clap-wrapper for VST3 and AU, inserts with latency reporting, the editor through choc's WebView, signing and notarisation; ARA after | `04-recommendation.md` section 10; 2 to 3 cycles, estimate | queued | | |
| R15 | `app-qt` from PyQt6 (GPL-3.0-only) to PySide6 (LGPL-3.0): the Linux release bundles it, so this precedes the next release | `03-skeptic.md` Concern 4; the frame's GPL rule is kept | queued | | |

Victor's own list, not the loop's:

- The `EBU_TEST_SET_URL` secret so CI runs the 29 EBU cases.
- The manual rows in [QA.md](QA.md) (a DAW bounce, real mix versions, a real Windows and Linux machine).
- A custom domain, GitHub pins, a Frame.io action.
- The ffmpeg question below.
- Whether apple-immersive's containers list gains `mov` (its quoted clause permits LPCM in .mov containers; a PCM MOV now fails the clause it quotes).
- A Finder-launched cumple.app has a minimal PATH and will not see Homebrew's ffmpeg; the app needs a way to set CUMPLE_FFMPEG or a bundled decoder before compressed deliveries work from the desktop.
- Between one 32 ms window and 1.28 s, `--vad silero` reports a speech share where the heuristic reports unknown; the engine may then pick a different loudness rule for the same short file (R1, a known difference).

Decided against on 12 September, and why: new landing-page columns for ffmpeg-normalize, r128gain or rsgain (each re-measures an engine already in the table: loudnorm, ffmpeg's ebur128, libebur128 1.2.6); watermark detection and automatic repair (outside a read-only QC tool); more presets (39 destinations is a strength, not a gap). Automatic repair was reversed on 8 October (R10 onward); watermark detection and more presets stand.

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
- `docs/graph-runs/2026-09-13-silero-vad/`: R1, PR #28. The loop's budget (research plus two builds) is spent; the next item needs Victor's word.
- `docs/graph-runs/2026-10-08-rx-parity-landscape/`: the RX parity landscape (five branches, skeptic, recommendation), Victor's reversal, path C, and items R10 to R15; PR #29.
