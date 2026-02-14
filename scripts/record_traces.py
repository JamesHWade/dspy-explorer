"""Record real DSPy RLM traces for the explorer.

Usage:
    # Set API keys first (or have them in ~/.Renviron / env vars)
    export OPENAI_API_KEY="sk-..."

    # Record all demo traces
    uv run python scripts/record_traces.py

    # Record a single trace
    uv run python scripts/record_traces.py --run dspy-rlm-run-1

Requires:
    - DSPy >= 2.6 (uv pip install dspy)
    - API key for the chosen provider
    - Deno installed (for DSPy's PythonInterpreter sandbox)
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any


def load_env_from_renviron() -> None:
    """Load API keys from ~/.Renviron if they're not already in env."""
    renviron = Path.home() / ".Renviron"
    if not renviron.exists():
        return
    for line in renviron.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and value and key not in os.environ:
                os.environ[key] = value


def fix_deno_env() -> None:
    """Prevent Deno from using the project's package.json for npm resolution.

    DSPy's PythonInterpreter uses Deno with `npm:pyodide`. If there's a
    package.json in the CWD or a parent, Deno 2.x tries to resolve npm
    packages from node_modules instead of its own cache, which fails.
    """
    os.environ["DENO_NO_PACKAGE_JSON"] = "1"


def record_rlm_trace(
    lm_name: str,
    question: str,
    output_path: Path,
    signature: str = "context, question -> answer",
    verbose: bool = True,
    **input_kwargs: Any,
) -> dict[str, Any]:
    """Record a single RLM trace and save to JSON.

    Args:
        lm_name: litellm-style model string (e.g., "openai/gpt-4o-mini")
        question: The question for the RLM to answer
        output_path: Where to save the JSON trace
        signature: DSPy signature string
        verbose: Whether to print progress
        **input_kwargs: Additional input kwargs for the RLM (e.g., context=...)

    Returns:
        The trace dict that was saved
    """
    import dspy
    from dspy.primitives.repl_types import REPLVariable

    lm = dspy.LM(lm_name)
    dspy.configure(lm=lm)

    rlm = dspy.RLM(
        signature=signature,
        max_iterations=15,
        verbose=verbose,
    )

    # Build inputs
    inputs: dict[str, Any] = {"question": question, **input_kwargs}

    if verbose:
        print(f"Running RLM with {lm_name}...")
        print(f"  Question: {question[:100]}...")
        print(f"  Inputs: {list(inputs.keys())}")

    start_time = time.time()
    result = rlm(**inputs)
    elapsed = time.time() - start_time

    # Extract trajectory
    trajectory: list[dict[str, str]] = getattr(result, "trajectory", [])

    # Build context_variables metadata. Count "# --- pkg/file.py ---" headers
    # to get the real file count (from load_package_source), falling back to 1.
    context_variables = []
    for name, value in inputs.items():
        value_str = str(value)
        # Count file headers injected by load_package_source
        import re as _re
        n_files = len(_re.findall(r"^# --- .+\.py ---$", value_str, _re.MULTILINE))
        if n_files == 0:
            n_files = 1
        context_variables.append({
            "name": name,
            "size_chars": len(value_str),
            "n_files": n_files,
        })

    # Detect which iteration has the SUBMIT call
    def has_submit(code: str) -> bool:
        return "SUBMIT(" in code

    # Build iterations
    iterations = []
    for i, step in enumerate(trajectory):
        code = step.get("code", "")
        output = step.get("output", "")
        is_final = has_submit(code) or i == len(trajectory) - 1
        # Check if the output indicates an error
        success = not any(
            marker in output
            for marker in ["Traceback (most recent call last)", "Error:", "Exception:"]
        )
        iterations.append({
            "iteration": i + 1,
            "reasoning": step.get("reasoning", ""),
            "code": code,
            "output": output,
            "success": success,
            "is_final": is_final,
        })

    # Try to get token usage from DSPy's LM history
    total_tokens = None
    try:
        history = lm.history
        if history:
            total_input = sum(
                entry.get("usage", {}).get("prompt_tokens", 0)
                for entry in history
            )
            total_output = sum(
                entry.get("usage", {}).get("completion_tokens", 0)
                for entry in history
            )
            if total_input > 0 or total_output > 0:
                total_tokens = {"input": total_input, "output": total_output}
    except Exception:
        pass

    # Count llm_query calls in the code
    llm_calls = sum(
        step.get("code", "").count("llm_query(")
        + step.get("code", "").count("llm_query_batched(")
        for step in trajectory
    )

    trace = {
        "run_id": output_path.stem,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "question": question,
        "model": lm_name,
        "context_variables": context_variables,
        "iterations": iterations,
        "final_answer": getattr(result, "answer", str(result)),
        "iterations_used": len(trajectory),
        "llm_calls_used": len(trajectory) + llm_calls,
    }
    if total_tokens:
        trace["total_tokens"] = total_tokens

    output_path.write_text(json.dumps(trace, indent=2))
    if verbose:
        print(f"Recorded: {output_path}")
        print(f"  Iterations: {len(trajectory)}")
        print(f"  Time: {elapsed:.1f}s")
        if total_tokens:
            print(
                f"  Tokens: {total_tokens['input']} in / {total_tokens['output']} out"
            )

    return trace


def load_package_source(package_name: str) -> tuple[str, int]:
    """Load all .py source files from an installed package into a single string.

    Returns:
        (context_string, n_files) — concatenated source and file count
    """
    import importlib

    mod = importlib.import_module(package_name)
    src_dir = Path(mod.__file__).parent
    py_files = sorted(src_dir.rglob("*.py"))

    parts = []
    for f in py_files:
        rel = f.relative_to(src_dir)
        try:
            content = f.read_text(errors="ignore")
        except OSError:
            continue
        parts.append(f"# --- {package_name}/{rel} ---\n{content}")

    context = "\n\n".join(parts)
    return context, len(py_files)


DEMOS: list[dict[str, Any]] = [
    {
        "name": "dspy-rlm-run-1",
        "lm": "openai/gpt-4o-mini",
        "signature": "context, question -> answer",
        "question": (
            "What are the three main decorator patterns in Flask "
            "and how does the request lifecycle work?"
        ),
        "package": "flask",
    },
    {
        "name": "dspy-rlm-run-2",
        "lm": "openai/gpt-4o-mini",
        "signature": "context, question -> answer",
        "question": (
            "How does Click parse command-line arguments? Trace the path from "
            "@click.command() through parameter parsing to the callback invocation."
        ),
        "package": "click",
    },
    {
        "name": "dspy-rlm-run-3",
        "lm": "openai/gpt-4o",
        "signature": "context, question -> answer",
        "question": (
            "Trace through the Flask request lifecycle from WSGI call "
            "to final response. What hooks can modify the request/response?"
        ),
        "package": "flask",
    },
]


def main() -> None:
    """Record demo traces."""
    load_env_from_renviron()
    fix_deno_env()

    output_dir = Path("src/dspy_explorer/data/runs")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Allow recording a single run by name
    target = None
    if len(sys.argv) > 1:
        if sys.argv[1] == "--run" and len(sys.argv) > 2:
            target = sys.argv[2]
        elif sys.argv[1] == "--help":
            print(__doc__)
            sys.exit(0)
        else:
            target = sys.argv[1]

    demos_to_run = DEMOS
    if target:
        demos_to_run = [d for d in DEMOS if d["name"] == target]
        if not demos_to_run:
            print(f"Unknown run: {target}")
            print(f"Available: {', '.join(d['name'] for d in DEMOS)}")
            sys.exit(1)

    for demo in demos_to_run:
        print(f"\n{'=' * 60}")
        print(f"Recording: {demo['name']}")
        print(f"{'=' * 60}\n")
        try:
            # Load real package source as context
            pkg = demo["package"]
            print(f"Loading source for {pkg}...")
            context, n_files = load_package_source(pkg)
            print(f"  {n_files} files, {len(context):,d} chars ({len(context)/1000:.0f}K)")

            record_rlm_trace(
                lm_name=demo["lm"],
                question=demo["question"],
                output_path=output_dir / f"{demo['name']}.json",
                signature=demo.get("signature", "context, question -> answer"),
                context=context,
            )
        except Exception as e:
            print(f"FAILED: {demo['name']}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
