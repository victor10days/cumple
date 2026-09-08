# Related tools: what was checked, and how

The comparison table on the landing page is this table. `tests/test_site_numbers.py` holds the two equal cell for cell and checks every "N of M readings in our run" cell against the summary lines of [BENCHMARK.md](BENCHMARK.md). Every cell comes from the tool's own documentation or source, read on 8 September 2026 at the addresses below, or from that run, which happened on one machine with the tools installed as listed. Nothing here is copied from a third party's description of a tool.

| Capability | cumple | libebur128 | pyloudnorm | ffmpeg ebur128 | loudcheck | DeltaWave |
|---|---|---|---|---|---|---|
| BS.1770 loudness and true peak | yes | yes | integrated and range, no true peak | yes | yes, measured by ffmpeg loudnorm | R 128 loudness, true peak and LRA per its release notes |
| Passes the EBU test set | 24 of 24 readings in our run; 29 of 29 cases in the conformance report | 24 of 24 readings in our run; its own tests open the EBU files | 15 of 15 readings in our run, loudness and range only | 24 of 24 readings in our run, no published report of its own | 23 of 24 readings in our run, through ffmpeg loudnorm | no published report; Windows only |
| Named destinations with graded sources | 39 | no | no | no | EBU R 128 and ATSC A/85; no platform presets, by design | no |
| The clause behind each verdict | yes | no verdicts | no verdicts | no verdicts | a one-line citation per gated metric, paraphrased | no verdicts |
| A report that travels with the delivery | HTML, PDF, JSON, CSV log | no, library only | no, library only | no, log output only | JSON on stdout, no file written | HTML report, batch via Report Cruncher |
| Diff in words, stems null test | yes | no | no | no | no | null test with level, offset and clock drift matched |
| Watch folder and desktop app | yes, three platforms | no | no | no | no; batch over a folder and an MCP server | desktop app, Windows only |
| Runs offline, no account | yes | yes | yes | yes | yes, with ffmpeg installed | no account mentioned; offline not stated |
| Licence | MIT | MIT | MIT | LGPL 2.1 or later | MIT | free of charge, all rights reserved, no program source published |

## cumple

Version 0.2.1, this repository. The run is [BENCHMARK.md](BENCHMARK.md) (22 files, 24 readings with an expectation); the full 29-case report is [CONFORMANCE.md](CONFORMANCE.md). Destinations, clauses and grades are in [SPECS.md](SPECS.md); the sheets, the watch folder, the diff and the app are described in the README.

## libebur128

Version checked: 1.2.6, the latest tag (14 February 2021), as built by Homebrew. Read on 8 September 2026: the README at https://github.com/jiixyj/libebur128, whose feature list says "Implements M, S and I modes", "Implements loudness range measurement (EBU - TECH 3342)" and "True peak scanning", whose licence line says "All source code is licensed under the MIT license", and which makes no claim of passing the EBU test set; `ebur128/ebur128.h`, where the true-peak function "Uses an implementation defined algorithm to calculate the true peak"; `test/tests.c`, which opens the seq-3341 and seq-3342 files by name against the expected values, with no test registered in the build and no instructions in the README. Steinmetz and Reiss, "pyloudnorm: A simple yet flexible loudness meter in Python" (AES 150th Convention, 2021), Table 1, show it within tolerance on every ITU-R BS.2217 compliance file. It is a library: no command line of its own (loudness-scanner is a separate project), no report, no verdicts, no network code. Run here: 22 files through ctypes, 24 of 24 readings inside tolerance, integrated loudness identical to cumple's to the hundredth on every file.

## pyloudnorm

Version checked: 0.2.0 on PyPI, MIT by its licence expression. Read on 8 September 2026: the README at https://github.com/csteinmetz1/pyloudnorm ("Implementation of ITU-R BS.1770-4"); `pyloudnorm/meter.py`, whose `Meter` has `integrated_loudness` and `loudness_range` and nothing for true peak; `tests/test_loudness.py` and `tests/data`, which hold the ITU-R BS.2217 compliance files (`1770-2_Comp_*`, `1770-2_Conf_*`) and no EBU file; the paper above, which calls it fully compliant on that material. A library with two dependencies (NumPy, SciPy), no network code, no report, no verdicts. Run here: 15 of 15 readings (9 integrated, 6 loudness range) inside tolerance; it takes at most five channels, so the six-channel file went in without its LFE.

## ffmpeg ebur128

Version checked: ffmpeg 8.0. Read on 8 September 2026: `libavfilter/f_ebur128.c` in the FFmpeg repository (licence header "GNU Lesser General Public License ... version 2.1 of the License, or (at your option) any later version"; options `integrated`, `range`, `sample_peak`, `true_peak`, `peak=true` for the oversampled peak, momentary and short-term gauges; a file comment citing EBU R 128 and claiming no conformance); `tests/fate/filter-video.mak`, where the one ebur128 test feeds `seq-3341-7_seq-3342-5-24bit.flac` and compares against a stored reference, a regression test rather than a conformance one; https://ffmpeg.org/legal.html. The paper above reports it 0.4 LU high on the BS.2217 relative-gate file and exactly 0.1 LU high on many tones. It prints a log, and `metadata=1` attaches values to frames; no report file, no verdicts. Run here: 24 of 24 readings inside tolerance; on the case 6 files it reports a true peak of −28 dBFS where the centre channel sits at −24, noted in BENCHMARK.md.

## loudcheck

Version checked: 0.3.2 on PyPI (6 July 2026), MIT, no dependencies, ffmpeg 5.0 or later on PATH. Read on 8 September 2026: the README at https://github.com/chaoz23/loudcheck: standards EBU R 128, ATSC A/85 and BS.1770 measure-only; "Only formal, stable standards live in this repo; per-platform delivery templates (Netflix, DPP, Apple TV+, Amazon, broadcaster specs) never do"; exit codes 0, 1 and 2; an MCP server; "GUIs" and "real-time monitoring" out of scope; batch over a directory. `loudcheck/analyze.py`: one ffmpeg pass with `loudnorm=print_format=json`, a second with `ebur128=peak=true` for `--detailed`. `loudcheck/standards.py` and `verdict.py`: a `citation` string per metric, for example "R 128: Target Level -23.0 LUFS, deviation shall not exceed ±0.5 LU", seen in its JSON here. `loudcheck/cli.py`: every result is printed to stdout, nothing is written to a file. `tests/`: generated tones, loudnorm cross-checked against ebur128 within 1 LU, no EBU or ITU file. Run here: 23 of 24 readings inside tolerance; case 5 reads −23.14 LUFS, 0.04 LU outside.

## DeltaWave

Version checked: 2.0.25; the site names no release date and was generated on 25 September 2025. Read on 8 September 2026: https://deltaw.org/ and its pages (Get started, Features, Quick start, Comparator, Reports, Release notes), and the documentation source at https://github.com/pkane2001/DeltaWave. "DeltaWave is provided to you free of charge, and contains no advertisements or in-program purchases"; every page's footer says "All rights reserved"; the repository carries a GPL-3.0 licence file, the documentation site and the installer, and no program source. "DeltaWave runs on Microsoft Windows and required .NET 4.6 framework to be installed." Release notes: 2.0.12 "Added: loudness analysis and comparison feature according to EBU R 128 specification with delta, true peak and LRA calculations included"; 2.0.25 "Change: adjusted LUFS calculation filter profile to better match specification"; neither says which loudness values are shown or how the true peak is computed. Reports: "DeltaWave can generate a detailed report in HTML format from the results of any two file comparison", from File, Generate Report; "To create multiple reports from a list of files, please use File->Report Cruncher". The comparison: "detailed comparison of two different captures of the same audio signal", with level and offset matched, and the feature list's "Determines and corrects for clock drift between two files". No page mentions an account, a key or an internet connection either way. Not run here: it does not run on this machine.

## Not compared

Nugen VisLM and Dolby's DPLM are the commercial meters the studios name in their specifications; neither was bought for this table. bbc/audio-offset-finder finds offsets only and leqm-nrt measures Leq(m) only; both are named in the README's Related work.
