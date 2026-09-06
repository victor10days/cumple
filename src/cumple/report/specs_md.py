"""docs/SPECS.md: the destination matrix, generated from the profiles so it cannot drift."""

from __future__ import annotations

from datetime import date

from .. import __version__
from ..specs.schema import GRADE_LABEL, Profile


def _esc(s: str) -> str:
    return s.replace("|", "\\|").replace("\n", " ")


# Studios and platforms whose delivery specification was looked for and is not public. Recorded
# here so the absence is a statement with a date, not a gap.
NOT_PUBLIC: list[tuple[str, str]] = [
    (
        "Sony Pictures Entertainment and Sony Pictures Television",
        "no public delivery specification; SonyLIV's Indian spec is not a studio document",
    ),
    ("Lionsgate", "delivery schedules are per contract; third-party summaries only"),
    ("Starz", "the affiliate page says only that advertisements follow ATSC A/85"),
    (
        "Universal Pictures theatrical",
        "not public; NBCU's public document is the Linear Commercial Guidelines (nbcu-commercial)",
    ),
    (
        "Paramount+ originals",
        "not public; Paramount's public documents are the Pluto TV guide (paramount-pluto) and the CBS commercial manual (cbs-commercial)",
    ),
    (
        "HBO and Max brand A/V specs",
        "behind a login; the public WBD document is the Content Partner Hub audio spec (max-wbd)",
    ),
    ("Warner Bros. Pictures theatrical", "not public"),
    ("NBCUniversal Peacock programme delivery", "no public primary; see peacock, graded COMMUNITY"),
]
NOT_PUBLIC_DATE = "2026-09-06"


def render_specs_markdown(profiles: list[Profile]) -> str:
    out = [f"# Destinations known to cumple {__version__}\n"]
    out.append(
        f"Generated {date.today().isoformat()} from `src/cumple/specs/profiles/*.yaml`. Every number is traceable to the sources listed under each destination, and the grade says how good that trace is:\n"
    )
    out.append("\n".join(f"- **{g.value}**: {label}" for g, label in GRADE_LABEL.items()) + "\n")
    out.append("An asterisk after a grade means some value is the tool's own default where the source is silent.\n")
    out.append("## Matrix\n")
    out.append("| id | destination | family | loudness | peak | other rules | grade |")
    out.append("|---|---|---|---|---|---|---|")
    for p in sorted(profiles, key=lambda p: (p.family, p.id)):
        other = []
        if p.dynamics.lra_max is not None:
            other.append(f"LRA ≤ {p.dynamics.lra_max:g} LU")
        if p.dynamics.short_term_max is not None:
            other.append(f"max S ≤ {p.dynamics.short_term_max:g}")
        if p.format.sample_rates:
            other.append("/".join(f"{r / 1000:g}" for r in p.format.sample_rates) + " kHz")
        if p.format.bit_depths:
            other.append("/".join(str(b) for b in p.format.bit_depths) + "-bit")
        if p.format.packaging != "either":
            other.append(p.format.packaging)
        if p.padding.head_max_s is not None or p.padding.tail_max_s is not None:
            other.append("padding")
        if p.stems.must_sum_to_printmaster:
            other.append("stems sum")
        if p.format.lfe_lowpass_hz is not None:
            other.append("LFE band")
        if p.checks.mono_compatibility:
            other.append("mono fold")
        if p.checks.metadata_must_match:
            other.append("bext truth")
        if p.rms is not None:
            other.append("RMS + noise floor")
        out.append(
            f"| `{p.id}` | {_esc(p.name)} | {p.family} | {_esc(p.loudness_compact())} | {_esc(p.peak_summary())} | {_esc(', '.join(other))} | {p.grade.value}{'*' if p.has_defaults else ''} |"
        )
    out.append("")
    for p in sorted(profiles, key=lambda p: (p.family, p.id)):
        out.append(f"## {p.name} (`{p.id}`)\n")
        out.append(_esc(p.summary) + "\n")
        if p.loudness:
            out.append(
                "Loudness rules" + (" (any one applicable rule may pass)" if p.loudness.policy == "any" else "") + ":\n"
            )
            for r in p.loudness.rules:
                out.append(f"- {r.describe()}" + (f" · {_esc(r.notes)}" if r.notes else ""))
            out.append("")
        if p.clauses:
            out.append(
                "In the source's words"
                + ("" if p.clauses_verbatim else " (paraphrased; verbatim quotes pending)")
                + ":\n"
            )
            for code, text in p.clauses.items():
                out.append(f"- `{code}`: {_esc(text)}")
            out.append("")
        out.append("Sources:\n")
        for s in p.provenance:
            line = (
                f"- **{s.grade.value}** ({s.role}) {_esc(s.title)}"
                + (f", {s.version}" if s.version else "")
                + (f" ({s.published})" if s.published else "")
                + f" · {_esc(s.publisher)}"
            )
            if s.url:
                line += f" · <{s.url}>"
            line += f" · retrieved {s.retrieved.isoformat()}"
            if s.notes:
                line += f". {_esc(s.notes)}"
            out.append(line)
        out.append("")
    out.append(f"## Looked for, not public ({NOT_PUBLIC_DATE})\n")
    out.append(
        "These companies were searched for on the date above and publish no delivery specification a tool can quote. A profile built from a rumour would carry a grade it does not deserve, so there is none.\n"
    )
    for who, why in NOT_PUBLIC:
        out.append(f"- **{who}**: {why}")
    out.append("")
    return "\n".join(out)
