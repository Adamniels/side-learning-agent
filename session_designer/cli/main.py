from __future__ import annotations

import json
import os
from pathlib import Path

import anthropic
import typer
from dotenv import find_dotenv, load_dotenv

from session_designer.cli.preview import print_session_preview
from session_designer.data.repository import load_context_from_json
from session_designer.graph.builder import run_session_design
from session_designer.graph.deps import GraphDeps
from session_designer.providers.anthropic_provider import AnthropicLLMProvider
from session_designer.providers.mock_provider import MockLLMProvider
from session_designer.resources.gatherer import LLMResourceGatherer

# Typer merges a lone command onto the root app; keep a second command so `run` stays a subcommand.
app = typer.Typer(no_args_is_help=True, help="LangGraph session designer prototype CLI.")


def _load_dotenv_for_run(fixture: Path) -> None:
    """Load `.env` by walking up from the fixture directory, then fall back to CWD search."""
    resolved = fixture.resolve()
    for d in [resolved.parent, *resolved.parents]:
        candidate = d / ".env"
        if candidate.is_file():
            load_dotenv(candidate)
            return
    load_dotenv(find_dotenv(usecwd=True))


@app.command("version")
def version_cmd() -> None:
    """Print package version."""
    from session_designer import __version__

    typer.echo(__version__)


@app.command("run")
def run_cmd(
    fixture: Path = typer.Option(
        ...,
        "--fixture",
        help="Path to JSON user learning context (see examples/).",
        exists=True,
        dir_okay=False,
        readable=True,
    ),
    mock: bool = typer.Option(
        False,
        "--mock",
        help="Use deterministic MockLLMProvider (no API key).",
    ),
    max_revisions: int = typer.Option(
        2,
        "--max-revisions",
        help="Maximum validation-driven session revisions.",
        min=0,
        max=5,
    ),
    compact: bool = typer.Option(
        False,
        "--compact",
        help="Shorthand for --format compact (single-line JSON).",
    ),
    output_format: str = typer.Option(
        "preview",
        "--format",
        help="preview: app-style terminal layout; json: indented JSON; compact: one-line JSON.",
    ),
) -> None:
    """Run the session designer graph and print results (default: Rich preview)."""
    _load_dotenv_for_run(fixture)
    ctx = load_context_from_json(fixture)
    if mock:
        llm: AnthropicLLMProvider | MockLLMProvider = MockLLMProvider()
        model = "mock"
    else:
        try:
            llm = AnthropicLLMProvider()
        except ValueError as e:
            typer.secho(str(e), fg=typer.colors.RED, err=True)
            typer.secho(
                "Set ANTHROPIC_API_KEY in .env (see .env.example) or use --mock.",
                err=True,
            )
            raise typer.Exit(code=1) from e
        model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
    gatherer = LLMResourceGatherer(llm)
    deps = GraphDeps(
        llm=llm,
        resource_gatherer=gatherer,
        model=model,
        max_revisions=max_revisions,
    )
    try:
        result = run_session_design(deps, ctx)
    except anthropic.APIError as e:
        typer.secho("Anthropic API request failed.", fg=typer.colors.RED, err=True)
        typer.secho(str(e), err=True)
        if "credit balance is too low" in str(e).lower():
            typer.secho(
                "Billing: prepaid credits for this API key’s organization are not available. "
                "Confirm the key was created under the same org as your Billing page, or add credits there. "
                "Until then, use: session-designer run --fixture ... --mock",
                err=True,
            )
        raise typer.Exit(code=1) from e

    fmt = "compact" if compact else output_format.lower().strip()
    allowed = {"preview", "json", "compact"}
    if fmt not in allowed:
        typer.secho(
            f"Unknown --format {fmt!r}; use one of: {', '.join(sorted(allowed))}.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=2)

    payload = result.model_dump(mode="json")
    if fmt == "preview":
        print_session_preview(result)
    elif fmt == "compact":
        typer.echo(json.dumps(payload, separators=(",", ":")))
    else:
        typer.echo(json.dumps(payload, indent=2))


def main() -> None:
    app()


if __name__ == "__main__":
    main()
