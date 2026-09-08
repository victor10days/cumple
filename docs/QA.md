# Manual QA log

Hands-on checks recorded here with a date and with who or what ran them.
The automated suite (`uv run pytest`, 185 tests) and the conformance report
cover the measurement; this log covers the surfaces an engineer actually
touches. An item without a dated entry has **not** been done. Rows that need
a DAW, real mix versions or a Windows or Linux machine stay pending until a
person runs them; the entries below say plainly when a check ran on the
synthetic demo set or was driven through the app's own bridge instead of a
mouse.

## Checklist for a release

| item | what to do | status |
|---|---|---|
| Drag-and-drop app, one file | Build `cumple QC.app` with `integrations/macos/build_app.sh`, drop a real bounce on it, pick a destination, confirm the sheet opens next to the file and its verdict matches `cumple check` in a terminal. | pending |
| Drag-and-drop app, folder | Drop a delivery folder of discrete mono files; confirm the roles are read from the filename suffixes and the sheet lands inside the folder. | pending |
| Watch folder during a bounce | Run `cumple watch <folder> --spec <id>` and bounce from a DAW into that folder. The file must not be measured while it is still growing, and the sheet plus a CSV line must appear after it settles. | pending |
| PDF sheet | Open a generated `.qc.pdf` in Preview and read it end to end: verdict, findings, fixes, timeline, clauses, sources. Nothing clipped, nothing wrong. | done 2026-09-08 on the demo set (entry 2) |
| Diff on real versions | `cumple diff v1.wav v2.wav` on two real mix versions; the offset, gain and spectral summary must match what was changed in the session. | done 2026-09-08 on the demo versions (entry 3); real versions pending |
| Diff sheet | `cumple diff v1.wav v2.wav --sheet --pdf` on two real versions; open the HTML and the PDF, read the stamp, the strip, the levels and the band chart; nothing clipped, the type is Barlow and Plex, not Helvetica. | done 2026-09-08 on the demo versions (entry 3) |
| Stems against the printmaster | `cumple diff DX MX FX --against PM` on a real stem set; the residual must reflect the real null. | done 2026-09-08 on the demo stems (entry 3); a real stem set pending |
| Desktop app, one file | Open `cumple.app` (or `cumple app`), drop a real bounce, pick a destination, press Check; the sheet appears in the window and lands next to the file, and its verdict matches `cumple check` in a terminal. | done 2026-09-07 and 2026-09-08 (entries 1 and 4) |
| Desktop app, a package and a folder | Drop a delivery folder of discrete mono files (one item, the sheet inside the folder) and a folder of bounces (one item per file). | done 2026-09-08 (entry 4) |
| Desktop app, Save PDF and Reveal | Save PDF writes `<name>.qc.pdf` next to the sheet through the local Chrome; Reveal selects it in Finder or Explorer; a clause link in the sheet opens in the browser. | done 2026-09-08 (entry 4); the clause link in the browser not exercised |
| Desktop app, watch during a bounce | The Watch tab on the bounce folder while a DAW bounces into it: the file is left alone until it settles, then the row, the sheet and the CSV line appear. | partly done 2026-09-08: a copied file that landed at once, not a growing DAW bounce (entry 4) |
| Desktop app, the diff | Two real versions in the Diff tab, then real stems against their printmaster; the prose and the diff sheet match the CLI. | done 2026-09-08 on the demo versions and stems (entry 4) |
| Windows build launches | The CI zip on a Windows 10 or 11 machine: SmartScreen's More info, Run anyway; the window opens, a WAV checks, Save PDF works with Edge or Chrome installed. | pending |
| Linux build launches | The CI tarball on an x86_64 desktop: the window opens (Qt), a WAV checks, the `.desktop` file works from the launcher. | pending |

## Entries

### 2026-09-07, the macOS build from a fresh download (desktop app, one file)
- Ran by: Claude Code, in the working session on Victor's Mac (Apple silicon, macOS 15).
- File(s): `hot.wav` from the synthetic demo set (`scripts/make_demo.py`).
- Action: downloaded `cumple-macos-arm64.zip` from the v0.2.0 release with the quarantine bit
  set, unzipped, `codesign --verify` passed on the ad-hoc signature, Gatekeeper refused the
  first launch as documented, `xattr -dr com.apple.quarantine cumple.app` cleared it, the app
  opened (`app.log`: "cumple 0.2.0 starting (frozen=True, platform=darwin)"), the file was
  checked against Netflix stereo (2.0) and the sheet landed next to it.
- Result: matches `cumple check` in a terminal (FAIL on integrated loudness, true peak and
  packaging).
- Finding: none.

### 2026-09-08, the QC sheet as a PDF (PDF sheet)
- Ran by: Claude Code, from the command line, on the demo set.
- Command: `cumple check ~/cumple-demo/hot.wav --spec netflix-2.0 --pdf`, then the pages
  rendered to PNG and read.
- Result: three A4 pages; verdict stamp, the six figures, twelve findings with their notes,
  the fixes, the timeline, the clauses and the sources all present, in Barlow Condensed and
  IBM Plex, nothing clipped. The JSON next to it carries the same verdict and twelve findings.
- Finding: none.

### 2026-09-08, diff, diff sheet and stems (three rows)
- Ran by: Claude Code, from the command line, on the demo set (synthetic; a real session's
  versions and stems are still pending).
- Commands: `cumple diff v12.wav v13.wav`, the same with `--sheet --pdf`, and
  `cumple diff DX.wav MX.wav FX.wav --against PM.wav`.
- Result: v13 reads as v12 at -1.3 dB, 23 samples late, residual -37 dBFS with the 2.5 kHz
  lift the demo applies, verdict SAME MATERIAL; the diff sheet's PDF shows the stamp, the
  strip, the levels and the band chart, nothing clipped; the stems sum to the printmaster with
  a -139 dBFS residual, verdict NULLS.
- Finding: none.

### 2026-09-08, the desktop app, all five rows, through the bridge
- Ran by: Claude Code, driving the real window (`cumple app`, pywebview, macOS 15) through
  its own JavaScript bridge on the demo set: the same functions the buttons call, no mouse.
- Actions and results:
  - `hot.wav` dropped, Netflix stereo (2.0) chosen, Check: the sheet appeared in the window
    with FAIL, and `hot.qc.html` landed next to the file.
  - Save PDF: "PDF saved next to the sheet: hot.qc.pdf", the file exists. Reveal: Finder
    opened on it. The clause link that opens the browser was not exercised.
  - `EP101_delivery` dropped: one queue item; against the Amazon 5.1 package profile the sheet
    landed inside the folder as `EP101_delivery/EP101_delivery.qc.html`. `bounces/` dropped:
    expanded to its two files at run time, two sheets written.
  - Watch tab on an empty folder, settle 2 s, Start: "Watching: 0 measured, 0 settling";
    `r128-ok.wav` copied in; the row appeared (PASS, -23.0 LUFS, -23.0 dBTP) with
    `cumple-log.csv`, the sheet and the JSON next to the file; Stop: "Stopped." A DAW writing
    a growing bounce is still pending.
  - Diff tab: `v12.wav` against `v13.wav` reads SAME MATERIAL with the same sentence as the
    CLI; stems mode with DX, MX, FX against PM reads NULLS.
- Finding: none.

Format for an entry:

```
### 2026-09-DD, <item>
- File(s): <description, never a client name>
- Command / action:
- Result:
- Finding (if any) and what was done about it:
```
