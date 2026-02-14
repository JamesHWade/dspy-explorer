"""Helper script to record DSPy RLM traces for the explorer.

Usage:
    uv run python scripts/record_traces.py

Requires:
    - DSPy installed (uv pip install dspy)
    - API keys set (OPENAI_API_KEY, etc.)
    - Deno installed (for DSPy's Python sandbox)
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


def record_rlm_trace(
    lm_name: str,
    context: str,
    question: str,
    output_path: Path,
) -> dict[str, Any]:
    """Record a single RLM trace and save to JSON."""
    import dspy

    lm = dspy.LM(lm_name)
    dspy.configure(lm=lm)

    rlm = dspy.RLM(
        signature="context, question -> answer",
        max_iterations=15,
    )

    result = rlm(context=context, question=question)
    trajectory = getattr(result, "trajectory", [])

    trace = {
        "run_id": output_path.stem,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "question": question,
        "model": lm_name,
        "context_variables": [],
        "iterations": [
            {
                "iteration": i + 1,
                "reasoning": step.get("reasoning", ""),
                "code": step.get("code", ""),
                "output": step.get("output", ""),
                "success": not step.get("error", False),
                "is_final": i == len(trajectory) - 1,
            }
            for i, step in enumerate(trajectory)
        ],
        "final_answer": getattr(result, "answer", str(result)),
        "iterations_used": len(trajectory),
        "llm_calls_used": len(trajectory),
    }

    output_path.write_text(json.dumps(trace, indent=2))
    print(f"Recorded trace: {output_path} ({len(trajectory)} iterations)")
    return trace


def main() -> None:
    """Record demo traces."""
    output_dir = Path("src/dspy_explorer/data/runs")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Example traces to record - customize as needed
    demos = [
        {
            "lm": "openai/gpt-4o-mini",
            "context": "You have access to a Python environment. Explore the data and answer the question.",
            "question": "What are the top 5 most common Python built-in functions and what do they do?",
            "name": "dspy-rlm-run-1",
        },
    ]

    for demo in demos:
        record_rlm_trace(
            lm_name=demo["lm"],
            context=demo["context"],
            question=demo["question"],
            output_path=output_dir / f"{demo['name']}.json",
        )


if __name__ == "__main__":
    main()
