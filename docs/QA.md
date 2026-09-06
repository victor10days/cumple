# Manual QA log

Hands-on checks on real bounces, done by a person, recorded here with a date.
The automated suite (`uv run pytest`, 148 tests) and the conformance report
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
