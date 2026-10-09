# Scoring iZotope RX 8 on the repair set

RX 8 has no command line and no scripting interface, so its columns in [docs/REPAIR.md](../REPAIR.md) come from
its Batch Processor, run by hand from this recipe. `scripts/benchmark_repair.py` reads the outputs back; until they
exist the RX columns read "not run (RX 8 outputs not present; see docs/repair/rx8-recipe.md)".

Parameter names below are the ones in RX 8's own factory preset files
(`/Library/Application Support/iZotope/RX 8 Audio Editor/Presets/De-click/*.xml` and `De-clip/*.xml`) and its help
pages (RX 8.5.0), read 2026-10-08. `Presets/De-click` and `Presets/De-clip` hold no preset named "Default", so
every value is spelled out here rather than left to a preset name. The factory De-clip thresholds run from
-0.25 dB to -6.6 dB, which is why the threshold is set by hand.

## The two modules

### De-clip

| Parameter (preset `ParamID`) | Value |
|---|---|
| Threshold (`Single Band Threshold`) | -0.5 dBFS, typed in, on the positive and the negative side (Threshold link on) |
| Suggest | not pressed |
| Quality (`Single Band Quality`) | High (the factory "High Quality - Clipping at (-1dB)" preset stores 2) |
| Makeup gain (`Single Band Gain Makeup`) | 0 dB |
| Post-limiter (`Single Band Enable Limiter`) | off |

The input folder is scaled so the clip plateau sits at 0.95, which is -0.45 dBFS. -0.5 dBFS is just under it, as
RX's help says to set it ("just below the actual level of clipping"). Suggest is off so the threshold does not
depend on RX's histogram of a given file. The post-limiter is off because it would change samples outside the
repaired intervals; the files are 32-bit float, so values above 0 dBFS are stored intact.

### De-click

| Parameter (preset `ParamID`) | Value |
|---|---|
| Algorithm (`Declicker Algorithm`) | Single Band (`Single-band Click.xml` carries no value for it, which makes it the default) |
| Sensitivity (`Declicker Sensitivity`) | the value the module shows when it opens: READ OFF AND WRITE HERE: ______ |
| Click widening (`Declicker Widening`) | the value the module shows when it opens: ______ |
| Frequency skew | greyed out in Single Band |
| Output clicks only | off |

Open the De-click module on a fresh session, change nothing, write the three shown values into the blanks above and
commit this file with them. Those are the numbers a user gets by opening the module and pressing Render, which is
the comparison this table is for. Single Band is the algorithm RX describes as working "well on very narrow
'digital' clicks", the kind the IMPULSE damage preset adds.

## Batch Processing

1. Run `uv run python scripts/make_repair_set.py`. It writes `~/.cache/cumple/repair/rx8-input/`: every damaged file,
   32-bit float. The clip files are scaled so their plateau sits at 0.95, because RX's De-clip threshold range and
   histogram are built around levels near full scale, and the survey levels put the plateau as low as 0.01. The scale
   of each file is in `manifest.json` (`rx_input[].scale`); the harness divides RX's output by it before scoring.
   The click files are not scaled (scale 1.0).
2. In RX 8, open Window > Batch Processor (Cmd+B).
3. Add the clip files: drag the files named `*.clip*.wav` from `rx8-input/` into the Input section.
4. In Module Chain, add De-clip with the values above. Wow & Flutter is not available in the Batch Processor and is
   not used.
5. Output: Choose folder, `~/.cache/cumple/repair/rx8/`. Format WAVE, 32-bit float. Leave the Naming field empty so the
   output keeps the input's name; the harness looks for `rx8/<name>.wav`, where `<name>` is the input's file name.
   If RX appends a suffix anyway, remove it by renaming.
6. Process. Then replace the module with De-click at the values above, add the files named `*.impulse*.wav` and
   `*.burst*.wav`, keep the same output folder, and process.
7. Fill the table below and run `uv run python scripts/benchmark_repair.py > docs/REPAIR.md`.

The harness accepts `rx8/` only if the files in `rx8-input/` still match the SHA-256 values in `manifest.json`, so
the outputs it scores are the outputs of the files it expects.

## Manifest table

Victor fills one row per output after the batch runs. The input hash and scale come from `manifest.json`.

| Name | Input SHA-256 | Scale | Output SHA-256 (`rx8/<name>.wav`) |
|---|---|---|---|
| (126 rows, one per damaged file, in manifest order) | | | |
