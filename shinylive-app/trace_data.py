"""Load and serve pre-recorded RLM traces."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def _data_dir() -> Path:
    """Return the path to the bundled trace data directory."""
    return Path(__file__).parent / "data" / "runs"


def list_available_runs() -> list[dict[str, Any]]:
    """List available pre-recorded runs with metadata."""
    data_dir = _data_dir()
    if not data_dir.is_dir():
        return []

    runs = []
    for f in sorted(data_dir.glob("*.json")):
        try:
            data = json.loads(f.read_text())
            n_iter = data.get("iterations_used") or len(data.get("iterations", []))
            llm_calls = data.get("llm_calls_used", 1)

            if llm_calls > 1:
                description = f"{n_iter} iterations, {llm_calls} LLM calls"
            else:
                description = f"{n_iter} iterations"

            runs.append({
                "id": data.get("run_id", f.stem),
                "label": data.get("run_id", f.stem),
                "description": description,
                "question": data.get("question", ""),
                "model": data.get("model", ""),
                "iterations": n_iter,
                "total_tokens": data.get("total_tokens"),
            })
        except (json.JSONDecodeError, KeyError):
            continue

    return runs


def load_trace(run_id: str) -> dict[str, Any] | None:
    """Load a specific trace by run_id.

    Validates run_id to prevent path traversal attacks.
    """
    if not re.match(r"^[A-Za-z0-9_-]+$", run_id):
        return None

    filepath = _data_dir() / f"{run_id}.json"
    if not filepath.is_file():
        return None

    try:
        return json.loads(filepath.read_text())
    except (json.JSONDecodeError, OSError):
        return None
