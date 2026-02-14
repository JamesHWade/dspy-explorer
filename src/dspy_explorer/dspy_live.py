"""Live RLM execution via DSPy."""

from __future__ import annotations

import os
import time
from typing import Any

from shiny import Session

from dspy_explorer.shinyreact import post_message


async def run_live_rlm(session: Session, config: dict[str, Any]) -> None:
    """Run a DSPy RLM query and stream results back to the client."""
    await post_message(session, "live_status", {"status": "running"})

    # Prevent Deno from using project's package.json for npm resolution
    os.environ.setdefault("DENO_NO_PACKAGE_JSON", "1")

    try:
        import dspy

        # Configure DSPy LM
        provider = config.get("provider", "openai")
        model = config.get("model", "gpt-4o-mini")

        lm_kwargs: dict[str, Any] = {}
        api_key = config.get("api_key")
        if api_key:
            lm_kwargs["api_key"] = api_key

        # DSPy uses litellm-style model strings
        model_str = f"{provider}/{model}" if provider != "openai" else model
        lm = dspy.LM(model_str, **lm_kwargs)
        dspy.configure(lm=lm)

        # Build RLM with signature
        signature = config.get("signature", "context, question -> answer")
        rlm = dspy.RLM(
            signature=signature,
            max_iterations=15,
        )

        # Build input kwargs
        inputs = config.get("inputs", {})
        if "question" in config and "question" not in inputs:
            inputs["question"] = config["question"]
        if "context" in config and "context" not in inputs:
            inputs["context"] = config.get("context", "")

        # Run it
        result = rlm(**inputs)

        # Convert trajectory to our trace format
        iterations = []
        trajectory = getattr(result, "trajectory", [])
        for i, step in enumerate(trajectory):
            iterations.append({
                "iteration": i + 1,
                "reasoning": step.get("reasoning", ""),
                "code": step.get("code", ""),
                "output": step.get("output", ""),
                "success": not step.get("error", False),
                "is_final": i == len(trajectory) - 1,
            })

        trace = {
            "run_id": f"live-{int(time.time())}",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "question": config.get("question", ""),
            "model": model,
            "context_variables": [],
            "iterations": iterations,
            "final_answer": getattr(result, "answer", str(result)),
            "iterations_used": len(trajectory),
            "llm_calls_used": len(trajectory),
        }

        await post_message(session, "live_result", trace)
        await post_message(session, "live_status", {"status": "complete"})

    except Exception as e:
        await post_message(session, "live_status", {
            "status": "error",
            "message": str(e),
        })
