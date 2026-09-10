# Contributing to cumple

Thank you for looking. This page is everything you need to run the code, add a
destination, or report a number that disagrees with a published document.

## Set up

```
git clone https://github.com/victor10days/cumple
cd cumple
uv sync            # Python 3.12, runtime and dev dependencies
uv run pytest      # 195 tests; the 29 EBU cases skip until you fetch the test set into ~/.cache/cumple
uv run ruff check src tests scripts && uv run ruff format --check src tests scripts
uv sync --extra app --group packaging     # the desktop app (pywebview) and PyInstaller
uv run cumple app                         # the window, from the source tree
uv run pyinstaller packaging/cumple.spec --noconfirm --clean   # dist/cumple.app or dist/cumple-app
uv run python scripts/make_icons.py       # re-render the app icon from the tokens (needs Chrome)
```

The EBU Loudness Test Set v5.0 is free from tech.ebu.ch under EBU terms and is
not redistributed here. Download `ebu-loudness-test-setv05.zip` in a browser
(the site refuses command-line downloads) and put the zip or its unpacked
folder in `~/.cache/cumple/`, or point `CUMPLE_EBU_TEST_SET` at it. The 29
conformance cases then run, and `scripts/conformance_report.py` regenerates
`docs/CONFORMANCE.md`.

## Add a destination

A destination is one YAML file. Built-in ones live in
`src/cumple/specs/profiles/`; your own go in `~/.config/cumple/profiles/` and
override a built-in with the same `id`. The schema is `src/cumple/specs/schema.py`
and rejects unknown keys, so a typo fails loudly.

Rules for a profile that will be merged:

1. **Every number has a source.** Each entry in `provenance` carries the
   document title, publisher, version, retrieval date, URL where one exists,
   and a `grade`: `READ` (you read the primary document), `SE` (the primary
   page is a JavaScript app and the values came from search extraction),
   `GATED` (partner portal, values from secondary summaries), `SECONDARY`
   (another standards body's table), `COMMUNITY` (the platform publishes
   nothing; third-party measurement). Do not upgrade a grade you cannot back.
2. **Where the source is silent, say so.** A tolerance or residual the
   document does not state is a tool default: add a provenance entry with
   `grade: TOOL_DEFAULT` and `role: default`, and explain the choice in the
   rule's `notes`. `cumple specs` marks such profiles with an asterisk.
3. **Quote when you can.** `clauses` maps a finding code (`loudness.integrated`,
   `peak.true`, `format.layout`, ...) to the source's words. Set
   `clauses_verbatim: true` only when every clause is a direct quote;
   paraphrases stay marked as paraphrases.
4. **Check it renders.** `cumple explain <id>` shows the rules, clauses and
   sources; `cumple check <file> --spec <id>` must run on a synthetic file.
   `tests/test_specs.py` loads every profile and `tests/test_cli_edges.py`
   evaluates all of them against a synthetic programme, so a new profile is
   covered by the existing suite.
5. Regenerate the matrix: `uv run cumple specs --markdown > docs/SPECS.md`.

## Report a wrong number

Open an issue with the destination id, the document (title, version, date,
where you read it), the value cumple uses and the value the document states.
A photo or quote of the clause settles it fastest. The profile's `retrieved`
date tells you how old our reading is; delivery specs change without notice.

## Code

- Meters stream in blocks and keep energies, never the audio; a two-hour 5.1
  file must run in constant memory (`docs/PERF.md`).
- New measurements get a synthetic test with a known answer, not a golden
  file. See `tests/test_bs1770.py` and `tests/test_truepeak.py` for the pattern.
- `ruff` is the formatter and linter; line length 120.
- The documents cumple writes (the QC sheet, the diff sheet) follow `design.md`.
  Colours and type come from `src/cumple/report/tokens.css` through `var()`,
  never inline; a test enforces it. `scripts/build_fonts.py` rebuilds the
  embedded font subsets in `src/cumple/report/fonts/`.
- Never commit audio from a client or a platform. Fixtures are generated at
  test time or come from the official EBU and ITU test signals, which stay in
  your cache.

## License

By contributing you agree that your contribution is licensed under the MIT
License in `LICENSE`.

## Merging

`main` is protected: a pull request merges only when the four test checks
(ubuntu-latest, macos-15, windows-latest, EBU conformance) are green on its
head, history stays linear (rebase merges), and nobody pushes to `main`
directly, administrators included. To bypass in an emergency, turn the rule
off under Settings, Branches, and turn it back on afterwards.

## The landing page

`site/` is hand written and shipped as it stands; there is no build step. A
merge to `main` deploys it twice over: the Pages mirror redeploys itself when
`site/` changes, and the `deploy` job in `.github/workflows/tests.yml` calls
Render's deploy hook once the suite is green, which is what serves
[cumple-uxa7.onrender.com](https://cumple-uxa7.onrender.com/). Nothing is
pressed by hand. The job needs the repository secret `RENDER_DEPLOY_HOOK`, and
says so in the log if it is missing. Editing `render.yaml` itself still needs
Blueprints, cumple, Manual sync, Approve: a deploy does not re-read that file.

## Releasing

1. Bump `__version__` in `src/cumple/__init__.py` and the `softwareVersion` in
   `site/index.html` on a branch; merge.
2. Tag main: `git tag -a vX.Y.Z origin/main -m "..."` and push the tag from a
   feature-branch checkout (the push hook refuses a main checkout).
3. The release workflow builds the four assets, self-tests each, opens the
   Windows and Linux windows in CI, and creates a draft release with the builds
   only.
4. Download the macOS zip with the quarantine bit set, follow the README's
   first-launch steps, check a file with it, and log the result in
   `docs/QA.md`; then publish the draft with notes that name what changed and
   any known issue.

