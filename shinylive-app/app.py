"""DSPy Explorer — Shinylive replay-only app."""

from pathlib import Path

from shiny import App, Inputs, Outputs, Session, reactive

from shinyreact import page_react, render_json, post_message
from trace_data import list_available_runs, load_trace


def server(input: Inputs, output: Outputs, session: Session):
    @render_json
    def available_runs():
        return list_available_runs()

    @render_json
    def trace_data():
        run_id = input.selected_run()
        if not run_id:
            return None
        return load_trace(run_id)

    @reactive.effect
    @reactive.event(input.start_live_run)
    async def handle_live_run():
        await post_message(session, "live_status", {
            "status": "error",
            "message": (
                "Live mode is not available in the browser. "
                "Install locally with: pip install dspy-explorer[live]"
            ),
        })


app = App(
    page_react(title="How RLMs Work — DSPy Explorer"),
    server,
    static_assets=str(Path(__file__).parent / "www"),
)
