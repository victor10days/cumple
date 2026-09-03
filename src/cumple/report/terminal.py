"""The verdict in the terminal."""

from __future__ import annotations

from rich import box
from rich.console import Console
from rich.table import Table

from ..checks.engine import Report, Status

ICON = {
    Status.PASS: "[green]PASS[/]",
    Status.FAIL: "[bold red]FAIL[/]",
    Status.WARN: "[yellow]WARN[/]",
    Status.INFO: "[dim]info[/]",
    Status.SKIP: "[dim]skip[/]",
}


def print_report(report: Report, console: Console | None = None, show_clauses: bool = False) -> None:
    console = console or Console()
    m, p = report.measurement, report.profile
    kind = "package" if m.is_package else "file"
    console.print(
        f"[bold]{m.path.name}[/]  [dim]{kind}, {m.layout}, {m.samplerate / 1000:g} kHz, {m.duration_s:.1f} s[/]"
    )
    console.print(f"against [bold]{p.name}[/] [dim]({p.id}, sources graded {p.grade.value})[/]")
    table = Table(box=box.SIMPLE_HEAD, show_edge=False, pad_edge=False)
    table.add_column("")
    table.add_column("check")
    table.add_column("measured")
    table.add_column("limit")
    table.add_column("note", max_width=60)
    for f in report.findings:
        note = f.note or ""
        if show_clauses and f.clause:
            note = (note + "\n" if note else "") + f"[dim]{f.clause}[/]"
        table.add_row(ICON[f.status], f.what, f.measured, f.limit, note)
    console.print(table)
    colour = "green" if report.passed else "red"
    console.print(f"[bold {colour}]{report.verdict}[/]  {p.name}")
    for fix in report.fixes():
        console.print(f"  [yellow]fix:[/] {fix}")
