# DSPy Explorer

Interactive visualizer for **DSPy RLM (Recursive Language Model)** execution traces. Watch how an LLM iteratively reasons, writes Python code, executes it in a sandboxed REPL, and self-corrects.

## Quick Start

### View Online (No Install)

Visit the hosted demo: **[jameshwade.github.io/dspy-explorer](https://jameshwade.github.io/dspy-explorer/)**

### Run Locally

```bash
# Install and run (replay mode — no DSPy needed)
uvx dspy-explorer

# Or install explicitly
uv pip install .
dspy-explorer run
```

### Live Mode (with DSPy)

```bash
# Install with DSPy support
uv pip install ".[live]"

# Run with live execution
dspy-explorer run
# Then switch to "Live" mode in the UI and configure your provider/model
```

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
git clone https://github.com/jameshwade/dspy-explorer.git
cd dspy-explorer

# Python deps
uv sync

# Node deps (React frontend)
npm install

# Start dev server (React watch + Shiny reload)
npm run dev
```

## Architecture

| Mode | How | Features | DSPy Required? |
|------|-----|----------|----------------|
| **GitHub Pages** | Visit hosted URL | Replay pre-recorded traces | No |
| **CLI** | `dspy-explorer run` | Replay + Live RLM execution | Optional |

The app uses:
- **Shiny for Python** — reactive server
- **React + TypeScript** — frontend UI
- **@posit/shiny-react** — Shiny-React bridge
- **Tailwind CSS v4** — styling
- **DSPy** (optional) — live RLM execution

## Recording New Traces

```bash
# Requires DSPy + API keys + Deno (for Python sandbox)
uv run python scripts/record_traces.py
```

## License

MIT
