# Manual QA log

Hands-on checks on real bounces, done by a person, recorded here with a date.
The automated suite (`uv run pytest`, 171 tests) and the conformance report
cover the measurement; this log covers the surfaces an engineer actually
touches. An item without a dated entry has **not** been done.

## Checklist for a release

| item | what to do | status |
|---|---|---|
| Drag-and-drop app, one file | Build `cumple QC.app` with `integrations/macos/build_app.sh`, drop a real bounce on it, pick a destination, confirm the sheet opens next to the file and its verdict matches `cumple check` in a terminal. | pending |
| Drag-and-drop app, folder | Drop a delivery folder of discrete mono files; confirm the roles are read from the filename suffixes and the sheet lands inside the folder. | pending |
| Watch folder during a bounce | Run `cumple watch <folder> --spec <id>` and bounce from a DAW into that folder. The file must not be measured while it is still growing, and the sheet plus a CSV line must appear after it settles. | pending |
| PDF sheet | Open a generated `.qc.pdf` in Preview and read it end to end: verdict, findings, fixes, timeline, clauses, sources. Nothing clipped, nothing wrong. | pending |
| Diff on real versions | `cumple diff v1.wav v2.wav` on two real mix versions; the offset, gain and spectral summary must match what was changed in the session. | pending |
| Diff sheet | `cumple diff v1.wav v2.wav --sheet --pdf` on two real versions; open the HTML and the PDF, read the stamp, the strip, the levels and the band chart; nothing clipped, the type is Barlow and Plex, not Helvetica. | pending |
| Stems against the printmaster | `cumple diff DX MX FX --against PM` on a real stem set; the residual must reflect the real null. | pending |
| Desktop app, one file | Open `cumple.app` (or `cumple app`), drop a real bounce, pick a destination, press Check; the sheet appears in the window and lands next to the file, and its verdict matches `cumple check` in a terminal. | pending |
| Desktop app, a package and a folder | Drop a delivery folder of discrete mono files (one item, the sheet inside the folder) and a folder of bounces (one item per file). | pending |
| Desktop app, Save PDF and Reveal | Save PDF writes `<name>.qc.pdf` next to the sheet through the local Chrome; Reveal selects it in Finder or Explorer; a clause link in the sheet opens in the browser. | pending |
| Desktop app, watch during a bounce | The Watch tab on the bounce folder while a DAW bounces into it: the file is left alone until it settles, then the row, the sheet and the CSV line appear. | pending |
| Desktop app, the diff | Two real versions in the Diff tab, then real stems against their printmaster; the prose and the diff sheet match the CLI. | pending |
| Windows build launches | The CI zip on a Windows 10 or 11 machine: SmartScreen's More info, Run anyway; the window opens, a WAV checks, Save PDF works with Edge or Chrome installed. | pending |
| Linux build launches | The CI tarball on an x86_64 desktop: the window opens (Qt), a WAV checks, the `.desktop` file works from the launcher. | pending |

## Entries

_None yet._

Format for an entry:

```
### 2026-09-DD, <item>
- File(s): <description, never a client name>
- Command / action:
- Result:
- Finding (if any) and what was done about it:
```
