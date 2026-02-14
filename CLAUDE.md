# CLAUDE.md

## Project Overview

DSPy Explorer is an interactive visualizer for **DSPy RLM (Recursive Language Model)** execution traces. It shows how an LLM iteratively writes Python code, executes it in a sandboxed REPL, and self-corrects to answer questions about large contexts.

The app has two modes:
- **Replay**: Browse pre-recorded trace JSON files (works offline, on GitHub Pages via Shinylive)
- **Live**: Run real `dspy.RLM` queries against any LLM provider (requires DSPy + Deno)

## Tech Stack

- **Python backend**: Shiny for Python (`src/dspy_explorer/`)
- **React frontend**: TypeScript + React 19 (`srcts/`)
- **Bridge**: `@posit/shiny-react` connects Shiny reactive outputs to React state
- **Styling**: Tailwind CSS v4 with shadcn/ui components
- **Build**: esbuild (`build.ts`)
- **Live execution**: DSPy's `dspy.RLM` with Deno + Pyodide sandbox

## Development Commands

```bash
# Install dependencies
uv sync                    # Python
npm install                # Node

# Development (React watch + Shiny reload)
npm run dev

# Build React frontend only
npm run build              # Production → www/
npm run watch              # Watch mode

# Run Shiny app directly
uv run shiny run src/dspy_explorer/app.py --port 8000 --reload

# CLI
uv run dspy-explorer       # Run locally
uv run dspy-explorer open  # Open GitHub Pages demo
```

## Project Structure

### Python Backend (`src/dspy_explorer/`)

| File | Purpose |
|------|---------|
| `app.py` | Shiny server: `available_runs` and `trace_data` reactive outputs, live mode handler |
| `shinyreact.py` | Bridge: `page_react()`, `render_json`, `post_message()` |
| `trace_data.py` | Load/list pre-recorded JSON traces from `data/runs/` |
| `dspy_live.py` | Live `dspy.RLM` execution, posts results via `post_message()` |
| `cli.py` | Click CLI with `run` and `open` commands |
| `data/runs/*.json` | Pre-recorded trace files |

### React Frontend (`srcts/`)

| File | Purpose |
|------|---------|
| `components/App.tsx` | Root: manages view state (intro/toolkit/traces), Shiny communication |
| `components/IntroPanel.tsx` | Landing page explaining DSPy and RLMs |
| `components/ToolkitPanel.tsx` | Educational panel: print, .find, llm_query, SUBMIT tools |
| `components/IterationCard.tsx` | Single REPL iteration: reasoning, code, output, concept callouts |
| `components/REPLTimeline.tsx` | Scrollable list of IterationCards controlled by playback |
| `components/PlaybackControls.tsx` | Play/pause/step/speed controls (sticky footer) |
| `components/PhaseTimeline.tsx` | Phase progress bar (orient/locate/trace/cross-ref/identify) |
| `components/ContextPanel.tsx` | Sidebar: context variables, tool call counts, token budget |
| `components/TokenBudget.tsx` | Token usage visualization |
| `components/Header.tsx` | Top bar: mode toggle, run selector, navigation |
| `components/LiveModePanel.tsx` | Provider/model/API key config form for live execution |
| `components/RunComparison.tsx` | Compare multiple runs after playback completes |
| `components/CodeBlock.tsx` | Syntax-highlighted code with RLM tool highlighting |
| `components/OutputBlock.tsx` | REPL output display (success/error styling) |
| `components/ConceptCallout.tsx` | Educational annotation card |
| `hooks/usePlayback.ts` | Playback state machine (play/pause/step/speed/jump) |
| `hooks/usePhaseDetection.ts` | Detect investigation phases from code patterns |
| `lib/types.ts` | TypeScript interfaces: Iteration, TraceData, Phase, providers |
| `lib/phases.ts` | Phase detection logic (orient/locate/trace_code/cross_reference/identify_gap) |
| `lib/utils.ts` | Utilities: cn(), formatChars() |
| `components/ui/` | shadcn/ui primitives (badge, button, collapsible, tabs, tooltip, etc.) |

### Other

| Path | Purpose |
|------|---------|
| `scripts/record_traces.py` | Record real DSPy RLM traces (requires API keys + Deno) |
| `shinylive-app/` | Stripped replay-only app for Shinylive/GitHub Pages export |
| `build.ts` | esbuild configuration |
| `.github/workflows/deploy-pages.yml` | CI: build React, export Shinylive, deploy to GitHub Pages |

## Trace Data Format

Each trace JSON file (`data/runs/*.json`) has this structure:

```typescript
{
  run_id: string;           // e.g., "dspy-rlm-run-1"
  timestamp: string;        // ISO 8601
  question: string;         // The question asked
  model: string;            // e.g., "openai/gpt-4o-mini"
  context_variables: [      // Input variables passed to the RLM
    { name: string, size_chars: number, n_files: number }
  ];
  iterations: [             // REPL execution trace
    {
      iteration: number,
      reasoning: string,    // LLM's reasoning before writing code
      code: string,         // Python code executed in sandbox
      output: string,       // Execution output (stdout or error)
      success: boolean,     // Whether execution succeeded
      is_final: boolean     // Whether this iteration calls SUBMIT()
    }
  ];
  final_answer: string;
  iterations_used: number;
  llm_calls_used: number;
  total_tokens?: { input: number, output: number };
}
```

## Recording Real Traces

```bash
# Set API keys (or have them in ~/.Renviron)
export OPENAI_API_KEY="sk-..."

# Record all demo traces
uv run python scripts/record_traces.py

# Record a single trace
uv run python scripts/record_traces.py --run dspy-rlm-run-1
```

Edit `scripts/record_traces.py` to add new questions/contexts in the `DEMOS` list.

## Shiny-React Communication

The Python backend communicates with React via `@posit/shiny-react`:

- **Shiny → React** (outputs): `render_json` decorator creates reactive outputs consumed by `useShinyOutput()` hooks
- **React → Shiny** (inputs): `useShinyInput()` hooks send values that appear as `input.xyz()` in Python
- **Server → Client** (messages): `post_message(session, type, data)` sends one-shot messages handled by `useShinyMessageHandler()` — used for live mode status/results

## Known Issues

- **Deno + package.json conflict**: DSPy's `PythonInterpreter` uses `npm:pyodide` in Deno. If a `package.json` exists in the CWD or a parent directory, Deno 2.x tries to resolve npm packages from `node_modules` instead of its own cache. The workaround is `DENO_NO_PACKAGE_JSON=1`, which is set automatically in `dspy_live.py` and `scripts/record_traces.py`.
- **Shinylive limitations**: The GitHub Pages version can only replay pre-recorded traces. No network access from Pyodide means no live LLM calls.
- The `www/` directory (built React bundle) is gitignored. The GitHub Actions workflow builds it during CI.

## Coding Conventions

- Use `uv` for all Python operations
- Frontend uses TypeScript strict mode with `@/*` path alias for `srcts/`
- Prefer editing existing files over creating new ones
- shadcn/ui components live in `srcts/components/ui/` — add new ones with the same pattern
- Phase detection logic is in `srcts/lib/phases.ts` — update when trace code patterns change
- Tool highlighting is in `srcts/components/CodeBlock.tsx` (`RLM_TOOLS` array)
