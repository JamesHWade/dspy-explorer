# DSPy Explorer

Interactive visualizer for **DSPy RLM (Recursive Language Model)** execution traces. Watch how an LLM iteratively reasons, writes Python code, executes it in a sandboxed REPL, and self-corrects to answer questions about large contexts.

Built with [Shiny for Python](https://shiny.posit.co/py/) + [React](https://react.dev/) + [DSPy](https://dspy.ai).

## Quick Start

### View Online (No Install)

Visit the hosted demo: **[jameshwade.github.io/dspy-explorer](https://jameshwade.github.io/dspy-explorer/)**

The GitHub Pages version runs entirely in the browser via [Shinylive](https://shiny.posit.co/py/get-started/shinylive.html) (Pyodide/WASM) and replays pre-recorded traces.

### Run Locally

```bash
# Install and run (replay mode — no DSPy needed)
uv pip install .
dspy-explorer

# Or run directly without installing
uvx dspy-explorer
```

### Live Mode (with DSPy)

Run your own RLM queries against any LLM provider:

```bash
# Install with DSPy support
uv pip install ".[live]"

# Set your API key
export OPENAI_API_KEY="sk-..."

# Run — then switch to "Live" mode in the UI
dspy-explorer run
```

Live mode requires [Deno](https://deno.com/) for DSPy's sandboxed Python interpreter.

## Pre-recorded Traces

The app ships with 3 real traces recorded using `dspy.RLM`:

| Run | Model | Question | Iterations |
|-----|-------|----------|------------|
| run-1 | gpt-4o-mini | Flask decorator patterns | 4 |
| run-2 | gpt-4o-mini | Python collections comparison | 4 |
| run-3 | gpt-4o | Flask request lifecycle | 5 |

## CLI Commands

```bash
dspy-explorer              # Run locally (default)
dspy-explorer run          # Same as above
dspy-explorer run --port 3000   # Custom port
dspy-explorer run --no-live     # Replay-only (no DSPy needed)
dspy-explorer open         # Open GitHub Pages demo in browser
```

## Development

```bash
# Clone and install dependencies
git clone https://github.com/JamesHWade/dspy-explorer.git
cd dspy-explorer

# Python deps
uv sync

# Node deps (React frontend)
npm install

# Start dev server (React watch + Shiny reload)
npm run dev
```

### Project Structure

```
dspy-explorer/
├── src/dspy_explorer/       # Python backend
│   ├── app.py               # Shiny server (reactive outputs, live mode handler)
│   ├── shinyreact.py        # Shiny-React bridge (page_react, render_json, post_message)
│   ├── trace_data.py        # Load pre-recorded JSON traces
│   ├── dspy_live.py         # Live RLM execution via dspy.RLM
│   ├── cli.py               # Click CLI (run, open)
│   └── data/runs/           # Pre-recorded trace JSON files
├── srcts/                   # React TypeScript source
│   ├── components/          # UI components (App, Header, IterationCard, etc.)
│   ├── hooks/               # usePlayback, usePhaseDetection
│   └── lib/                 # types, phases, utils
├── www/                     # Built React bundle (esbuild output, gitignored)
├── scripts/
│   └── record_traces.py     # Helper to record real DSPy RLM traces
├── shinylive-app/           # Replay-only app for Shinylive/GitHub Pages export
├── build.ts                 # esbuild config
├── package.json             # npm: React 19, esbuild, Tailwind v4
├── pyproject.toml           # Python: shiny, click, optional dspy
└── .github/workflows/
    └── deploy-pages.yml     # Build + Shinylive export + GitHub Pages deploy
```

### Build Commands

```bash
npm run build     # Production build (React → www/)
npm run watch     # Watch mode (rebuild on change)
npm run dev       # Watch + Shiny dev server
```

## Recording New Traces

Record real DSPy RLM traces for the explorer:

```bash
# Requires: DSPy, API keys (or ~/.Renviron), Deno
uv pip install ".[live]"

# Record all demo traces
uv run python scripts/record_traces.py

# Record a single trace
uv run python scripts/record_traces.py --run dspy-rlm-run-1
```

The script loads API keys from `~/.Renviron` if they're not in the environment. Edit `scripts/record_traces.py` to add new questions/contexts.

**Note**: DSPy's `PythonInterpreter` uses Deno + Pyodide for sandboxed execution. If you get `npm:pyodide` errors, the script automatically sets `DENO_NO_PACKAGE_JSON=1` to prevent Deno from using the project's `package.json` for npm resolution.

## Architecture

| Mode | How | Features | DSPy Required? |
|------|-----|----------|----------------|
| **GitHub Pages** | Visit hosted URL | Replay pre-recorded traces | No |
| **CLI (replay)** | `dspy-explorer run --no-live` | Replay traces locally | No |
| **CLI (live)** | `dspy-explorer run` | Replay + live RLM execution | Yes |

**Tech stack:**
- **Shiny for Python** — reactive server
- **React 19 + TypeScript** — frontend UI
- **@posit/shiny-react** — Shiny-React bridge
- **Tailwind CSS v4** — styling with shadcn/ui components
- **esbuild** — fast bundling
- **DSPy** (optional) — live `dspy.RLM` execution with any LLM provider

## License

MIT
