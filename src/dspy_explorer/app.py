"""DSPy Explorer — Shiny for Python app."""

from __future__ import annotations

from pathlib import Path

from shiny import App, Inputs, Outputs, Session, reactive

from dspy_explorer.shinyreact import page_react, render_json, post_message
from dspy_explorer.trace_data import list_available_runs, load_trace


def server(input: Inputs, output: Outputs, session: Session):
    # ---- Available Runs ----
    @render_json
    def available_runs():
        return list_available_runs()

    # ---- Replay Mode ----
    @render_json
    def trace_data():
        run_id = input.selected_run()
        if not run_id:
            return None
        return load_trace(run_id)

    # ---- Live Mode ----
    @reactive.effect
    @reactive.event(input.start_live_run)
    async def handle_live_run():
        config = input.start_live_run()
        if not config:
            return
        try:
            from dspy_explorer.dspy_live import run_live_rlm
            await run_live_rlm(session, config)
        except ImportError:
            await post_message(session, "live_status", {
                "status": "error",
                "message": "Live mode requires DSPy. Install with: uv pip install 'dspy-explorer[live]'",
            })


# Resolve static assets path
www_dir = Path(__file__).parent.parent.parent / "www"
if not www_dir.is_dir():
    # Fallback for installed package
    www_dir = Path(__file__).parent / "www"

app = App(
    page_react(title="How RLMs Work — DSPy Explorer"),
    server,
    static_assets=str(www_dir),
)
