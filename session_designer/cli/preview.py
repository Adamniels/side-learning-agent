"""Rich terminal preview: approximates an app-style session summary."""

from __future__ import annotations

from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich.markup import escape

from session_designer.domain.output import SessionDesignResult


def _text_block(s: str) -> Text:
    t = Text()
    for line in s.splitlines():
        t.append(escape(line))
        t.append("\n")
    if t.plain.endswith("\n"):
        t.rstrip()
    return t


def print_session_preview(result: SessionDesignResult) -> None:
    console = Console(highlight=False)
    st = result.selected_topic

    header = Text.assemble(
        ("Session designer", "bold cyan"),
        " · ",
        ("preview", "dim"),
    )
    console.print(header)
    console.print()

    hero = Panel(
        Group(
            Text("Selected topic", style="bold white"),
            Text(st.title, style="bold green"),
            Text(st.summary, style="white"),
            Text(),
            Text("Level fit", style="dim"),
            Text(st.difficulty_alignment, style="italic"),
        ),
        title="[bold]Up next[/bold]",
        border_style="cyan",
        box=box.ROUNDED,
        padding=(1, 2),
    )
    console.print(hero)
    console.print()

    why = Panel(
        _text_block(result.why_chosen),
        title="[bold]Why this topic[/bold]",
        border_style="dim",
        box=box.ROUNDED,
        padding=(0, 1),
    )
    console.print(why)
    console.print()

    console.print(Rule("[bold]Candidates considered[/bold]", style="dim"))
    cand_table = Table(box=box.SIMPLE_HEAD, show_lines=False, padding=(0, 1))
    cand_table.add_column("#", style="dim", width=3)
    cand_table.add_column("Title", style="bold", ratio=1)
    cand_table.add_column("Fit", style="white", ratio=2)
    for i, c in enumerate(result.candidates_considered, start=1):
        mark = "→ " if st.candidate_id and c.id == st.candidate_id else ""
        cand_table.add_row(
            f"{i}",
            f"{mark}{escape(c.title)}",
            escape(c.one_line_fit),
        )
    console.print(cand_table)
    console.print()

    console.print(Rule("[bold]Your session[/bold]", style="cyan"))

    def _section(title: str, body: Text) -> Panel:
        return Panel(
            body,
            title=f"[bold]{title}[/bold]",
            border_style="blue",
            box=box.ROUNDED,
            padding=(0, 1),
        )

    console.print(_section("Goal", _text_block(result.goal)))
    console.print()
    console.print(_section("Context", _text_block(result.context)))
    console.print()
    ho = _text_block(result.hands_on)
    ho.append("\n")
    ho.append("Expected output: ", style="bold")
    ho.append(escape(result.hands_on_expected_output))
    console.print(_section("Hands-on", ho))
    console.print()
    console.print(_section("Extension", _text_block(result.extension)))
    console.print()

    console.print(Rule("[bold]Suggested resources[/bold]", style="dim"))
    if not result.suggested_resources:
        console.print(Text("None listed.", style="dim"))
    else:
        for r in result.suggested_resources:
            kind_label = r.kind.value.replace("_", " ").title()
            url_line = Text(escape(r.url), style="underline blue")
            block = Group(
                Text.assemble(
                    ("● ", "green"),
                    (escape(r.title), "bold white"),
                    "  ",
                    (f"({kind_label})", "cyan"),
                ),
                url_line,
                Text(escape(r.rationale), style="dim italic"),
            )
            console.print(Panel(block, box=box.MINIMAL, padding=(0, 0, 0, 2)))
    console.print()

    vr = result.validation
    val_style = "green" if vr.passed else "yellow"
    val_title = "Quality check — passed" if vr.passed else "Quality check — needs attention"
    lines: list[Text | Table] = []
    if vr.checklist:
        t = Table(box=box.SIMPLE, show_header=True, padding=(0, 1))
        t.add_column("Check", style="bold")
        t.add_column("OK", width=4)
        t.add_column("Detail", style="dim")
        for item in vr.checklist:
            sym = "✓" if item.passed else "✗"
            t.add_row(escape(item.name), sym, escape(item.detail))
        lines.append(t)
    if vr.issues:
        lines.append(Text("Issues:", style="bold yellow"))
        for issue in vr.issues:
            lines.append(Text(f"  • {escape(issue)}", style="yellow"))
    if vr.suggested_fixes:
        lines.append(Text("Suggested fixes:", style="bold dim"))
        for fx in vr.suggested_fixes:
            lines.append(Text(f"  • {escape(fx)}", style="dim"))
    if vr.overall_notes:
        lines.append(Text(escape(vr.overall_notes), style="italic dim"))

    console.print(
        Panel(
            Group(*lines) if lines else Text("No checklist details.", style="dim"),
            title=f"[{val_style}]{val_title}[/{val_style}]",
            subtitle=f"Revisions applied: {result.revision_count}",
            border_style=val_style,
            box=box.ROUNDED,
            padding=(0, 1),
        )
    )

    foot: list[str] = []
    if result.normalization_notes:
        foot.append("Input notes: " + "; ".join(result.normalization_notes))
    if result.prototype_notes:
        foot.append("; ".join(result.prototype_notes))
    if foot:
        console.print()
        console.print(Text("\n".join(foot), style="dim"))
