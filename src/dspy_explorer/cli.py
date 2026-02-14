"""CLI for DSPy Explorer."""

from __future__ import annotations

import webbrowser
from pathlib import Path

import click

PAGES_URL = "https://jameshwade.github.io/dspy-explorer/"


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx: click.Context) -> None:
    """DSPy Explorer — Interactive RLM trace visualizer."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(run)


@main.command()
def open() -> None:
    """Open the hosted demo on GitHub Pages."""
    click.echo(f"Opening {PAGES_URL}")
    webbrowser.open(PAGES_URL)


@main.command()
@click.option("--port", default=8000, help="Port to run on.")
@click.option("--no-live", is_flag=True, help="Replay-only mode (no DSPy needed).")
def run(port: int, no_live: bool) -> None:
    """Run the explorer locally."""
    app_path = str(Path(__file__).parent / "app.py")
    click.echo(f"Starting DSPy Explorer on http://localhost:{port}")

    from shiny import run_app

    run_app(app_path, port=port, launch_browser=True)
