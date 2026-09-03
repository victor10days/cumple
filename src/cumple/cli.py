"""The cumple command line."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import __version__
from .checks import evaluate
from .io import load_package, probe
from .meters.measure import measure
from .report import print_report, report_to_dict
from .specs import ProfileNotFound, get, load_all
from .specs.schema import GRADE_LABEL, Profile

app = typer.Typer(
    help="Delivery QC for audio. ¿Cumple? Does this file comply?",
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode="rich",
)
console = Console()

NOT_YET = {
    "diff": "audio diff",
    "watch": "watch folder",
    "fix": "gain-only fix",
}


def _version(value: bool) -> None:
    if value:
        console.print(f"cumple {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(False, "--version", "-V", callback=_version, is_eager=True, help="Print the version."),
) -> None:
    pass


def _profile_or_exit(profile_id: str) -> Profile:
    try:
        return get(profile_id)
    except ProfileNotFound as e:
        console.print(f"[red]{e.args[0]}[/]")
        console.print("Run [bold]cumple specs[/] to list the destinations cumple knows.")
        raise typer.Exit(2)


@app.command()
def specs(
    family: str | None = typer.Option(None, "--family", "-f", help="streaming, broadcast, cinema, music, podcast, audiobook, standard"),
    as_json: bool = typer.Option(False, "--json", help="Machine-readable output."),
) -> None:
    """List the destinations cumple knows, with the grade of their sources."""
    profiles = [p for p in load_all().values() if family is None or p.family == family]
    profiles.sort(key=lambda p: (p.family, p.id))
    if as_json:
        rows = [
            {
                "id": p.id,
                "name": p.name,
                "family": p.family,
                "loudness": p.loudness_summary(),
                "peak": p.peak_summary(),
                "grade": p.grade.value,
            }
            for p in profiles
        ]
        console.print_json(json.dumps(rows))
        return
    table = Table(box=box.SIMPLE_HEAD, title=f"cumple {__version__}: {len(profiles)} destinations", title_justify="left")
    table.add_column("id", style="bold", no_wrap=True)
    table.add_column("destination", max_width=24)
    table.add_column("loudness", max_width=30)
    table.add_column("peak", no_wrap=True)
    table.add_column("grade", no_wrap=True)
    for p in profiles:
        table.add_row(p.id, p.name, p.loudness_compact(), p.peak_summary(), _grade_markup(p))
    console.print(table)
    console.print("[dim]grade = how the numbers were obtained: READ is a primary document read directly; SE, SECONDARY, GATED and COMMUNITY are weaker. * = some value is the tool's own default. `cumple explain <id>` shows the rules and sources.[/]")


def _grade_markup(p: Profile) -> str:
    colour = {"READ": "green", "SE": "yellow", "SECONDARY": "yellow", "GATED": "red", "COMMUNITY": "red", "TOOL_DEFAULT": "magenta"}[p.grade.value]
    star = "[magenta]*[/]" if p.has_defaults else ""
    return f"[{colour}]{p.grade.value}[/]{star}"


@app.command()
def explain(profile_id: str = typer.Argument(..., help="A profile id from `cumple specs`.")) -> None:
    """Show every rule of a destination, the source's words, and where they came from."""
    p = _profile_or_exit(profile_id)
    console.print(Panel(p.summary, title=f"{p.name}  [dim]({p.id}, {p.family})[/]", title_align="left"))

    rules = Table(box=box.SIMPLE_HEAD, title="Rules", title_justify="left")
    rules.add_column("what")
    rules.add_column("limit")
    if p.loudness:
        for r in p.loudness.rules:
            rules.add_row("loudness", r.describe())
        if len(p.loudness.rules) > 1:
            rules.add_row("", f"[dim]policy: {'any one applicable rule may pass' if p.loudness.policy == 'any' else 'every applicable rule must pass'}[/]")
    if p.peaks.true_peak_max is not None:
        rules.add_row("true peak", f"≤ {p.peaks.true_peak_max:g} dBTP" + (f" (recommended ≤ {p.peaks.true_peak_recommended:g})" if p.peaks.true_peak_recommended is not None else ""))
    if p.peaks.sample_peak_max is not None:
        rules.add_row("sample peak", f"≤ {p.peaks.sample_peak_max:g} dBFS")
    if p.dynamics.lra_max is not None:
        rules.add_row("loudness range", f"≤ {p.dynamics.lra_max:g} LU")
    if p.dynamics.short_term_max is not None:
        rules.add_row("max short-term", f"≤ {p.dynamics.short_term_max:g} LUFS")
    if p.leqm is not None:
        rules.add_row("Leq(m)", f"≤ {p.leqm.max_db:g} dB, {p.leqm.calibration_dbfs:g} dBFS = {p.leqm.calibration_spl_db:g} dBC")
    if p.rms is not None:
        rules.add_row("RMS", f"{p.rms.rms_min_dbfs:g} to {p.rms.rms_max_dbfs:g} dBFS" + (f", noise floor ≤ {p.rms.noise_floor_max_dbfs:g} dBFS" if p.rms.noise_floor_max_dbfs is not None else ""))
    f = p.format
    if f.sample_rates:
        rules.add_row("sample rate", ", ".join(f"{r/1000:g} kHz" for r in f.sample_rates))
    if f.bit_depths:
        rules.add_row("bit depth", ", ".join(f"{b}-bit" for b in f.bit_depths))
    if f.layouts:
        rules.add_row("layouts", ", ".join(f.layouts) + (f" ({f.channel_order} order)" if f.channel_order else ""))
    if f.packaging != "either":
        rules.add_row("packaging", f.packaging)
    if f.containers:
        rules.add_row("containers", ", ".join(f.containers))
    if f.lfe_lowpass_hz is not None:
        rules.add_row("LFE content", f"nothing above {f.lfe_lowpass_hz:g} Hz")
    if p.padding.head_max_s is not None:
        rules.add_row("head padding", f"≤ {p.padding.head_max_s:g} s")
    if p.padding.tail_max_s is not None:
        rules.add_row("tail padding", "not permitted" if p.padding.tail_max_s == 0 else f"≤ {p.padding.tail_max_s:g} s")
    if p.stems.must_sum_to_printmaster:
        rules.add_row("stems", f"must sum to the printmaster (residual ≤ {p.stems.residual_max_dbfs:g} dBFS)")
    if p.stems.me_must_have_no_speech:
        rules.add_row("M&E", "no speech")
    if p.checks.metadata_must_match:
        rules.add_row("metadata", "bext loudness fields must match the measurement")
    if p.checks.mono_compatibility:
        rules.add_row("mono", "stereo must fold to mono")
    console.print(rules)

    if p.clauses:
        clauses = Table(box=box.SIMPLE_HEAD, title="In the source's words" + ("" if p.clauses_verbatim else "  [dim](paraphrased; verbatim quotes pending)[/]"), title_justify="left")
        clauses.add_column("rule", style="bold")
        clauses.add_column("clause")
        for code, text in p.clauses.items():
            clauses.add_row(code, text)
        console.print(clauses)

    src = Table(box=box.SIMPLE_HEAD, title="Sources", title_justify="left")
    src.add_column("grade")
    src.add_column("role")
    src.add_column("document")
    src.add_column("retrieved")
    for s in p.provenance:
        doc = f"{s.title}" + (f", {s.version}" if s.version else "") + (f" ({s.published})" if s.published else "") + f"\n[dim]{s.publisher}[/]" + (f"\n[dim]{s.url}[/]" if s.url else "") + (f"\n[italic]{s.notes}[/]" if s.notes else "")
        src.add_row(s.grade.value, s.role, doc, s.retrieved.isoformat())
    console.print(src)
    console.print(f"[dim]Grade meanings: " + "; ".join(f"{g.value} = {label}" for g, label in GRADE_LABEL.items()) + "[/]")


@app.command()
def info(path: Path = typer.Argument(..., exists=True, help="An audio file or a directory of discrete channel files.")) -> None:
    """What the file is: container, rate, depth, channels, duration, embedded metadata."""
    if path.is_dir():
        pkg = load_package(path)
        table = Table(box=box.SIMPLE_HEAD, title=f"package {path.name}: {pkg.layout_guess}", title_justify="left")
        for col in ("role", "file", "rate", "depth", "channels", "duration"):
            table.add_column(col)
        for role, i in pkg.infos.items():
            table.add_row(role, i.path.name, f"{i.samplerate}", f"{i.bit_depth}", f"{i.channels}", f"{i.duration_s:.3f} s")
        console.print(table)
        for problem in pkg.consistent():
            console.print(f"[red]problem:[/] {problem}")
        return
    i = probe(path)
    table = Table(box=box.SIMPLE_HEAD, show_header=False, title=str(path), title_justify="left")
    table.add_column("field", style="bold")
    table.add_column("value")
    table.add_row("container", i.container)
    table.add_row("encoding", f"{i.subtype} ({'float' if i.is_float else 'integer'}, {i.bit_depth}-bit)")
    table.add_row("sample rate", f"{i.samplerate} Hz")
    table.add_row("channels", str(i.channels))
    table.add_row("frames", f"{i.frames}")
    table.add_row("duration", f"{i.duration_s:.3f} s")
    bext = i.bext
    if bext:
        for k, v in bext.items():
            if v not in (None, "", 0, 0.0):
                table.add_row(f"bext.{k}", str(v))
    if "adm" in i.metadata:
        table.add_row("adm", str(i.metadata["adm"]))
    console.print(table)


def _not_yet(name: str) -> None:
    console.print(f"[yellow]cumple {name}[/] is not in this build yet ({NOT_YET[name]}).")
    raise typer.Exit(3)


@app.command()
def check(
    path: Path = typer.Argument(..., exists=True, help="An audio file, or a directory of discrete channel files."),
    spec: str = typer.Option(..., "--spec", "-s", help="Destination profile id (see `cumple specs`)."),
    as_json: bool = typer.Option(False, "--json", help="Print the full report as JSON instead of a table."),
    clauses: bool = typer.Option(False, "--clauses", help="Print the source's words under each finding."),
) -> None:
    """Measure a file or package against a destination. Exit 0 on PASS, 1 on FAIL."""
    profile = _profile_or_exit(spec)
    try:
        m = measure(path)
    except ValueError as e:
        console.print(f"[red]cannot measure {path}:[/] {e}")
        raise typer.Exit(2)
    report = evaluate(profile, m)
    if as_json:
        console.print_json(json.dumps(report_to_dict(report)))
    else:
        print_report(report, console, show_clauses=clauses)
    raise typer.Exit(0 if report.passed else 1)


@app.command()
def diff(a: Path = typer.Argument(..., exists=True), b: Path = typer.Argument(..., exists=True)) -> None:
    """Say in words how two audio files differ."""
    _not_yet("diff")


@app.command()
def watch(folder: Path = typer.Argument(..., exists=True), spec: str = typer.Option(..., "--spec", "-s")) -> None:
    """Sit on a bounce folder and QC every file that lands in it."""
    _profile_or_exit(spec)
    _not_yet("watch")


@app.command()
def fix(path: Path = typer.Argument(..., exists=True), spec: str = typer.Option(..., "--spec", "-s")) -> None:
    """Write a gain-corrected copy when gain alone can make a file comply. Never limits."""
    _profile_or_exit(spec)
    _not_yet("fix")


if __name__ == "__main__":
    app()
