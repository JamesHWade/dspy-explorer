import type { Iteration, Phase } from "./types";

export function detectPhase(
  iter: Iteration,
  allIterations: Iteration[],
): Phase {
  const code = iter.code;
  const codeLower = code.toLowerCase();
  const reasoning = (iter.reasoning ?? "").toLowerCase();
  const idx = iter.iteration;
  const totalIters = allIterations.length;

  // SUBMIT or final answer = identify_gap
  if (iter.is_final || /SUBMIT\s*\(/.test(code)) {
    return "identify_gap";
  }

  // Orient: early iterations scanning overall structure
  if (
    idx <= 2 &&
    (/print\(.*\[:/.test(code) ||
      /context\s*\[\s*:\s*\d/.test(codeLower) ||
      /type\(|len\(|dir\(|\.keys\(/.test(codeLower) ||
      /structure|overview|explore|understand|preview|beginning|available|identify the/.test(
        reasoning,
      ))
  ) {
    return "orient";
  }

  // Reasoning-based signals
  const traceReasoning =
    /definition|implementation|method|dispatch|lifecycle|invoke|call\s*(path|chain)|inheritance|within the \w+ class|full\s*(content|definition)|analyz(e|ing)\s*(the|specific|request|how)/.test(
      reasoning,
    );
  const locateReasoning =
    /search(ing)?(\s+for)?|find(ing)?(\s+the)?|locat(e|ing)|extract(ing)?|filter(ing)?|look(ing)?\s*(for|at)|occurrenc|mention|scan(ning)?/.test(
      reasoning,
    );
  const synthesizeReasoning =
    /compile|synthesiz|format.*final|ready.*submit|structur(e|ing)\s*(the\s+)?find|prepare.*submission|present.*final/.test(
      reasoning,
    );

  // Near-end synthesis/compilation = approaching identify_gap
  if (synthesizeReasoning && idx >= totalIters - 2) {
    return "identify_gap";
  }

  // Both trace and locate signals — use position to disambiguate
  if (traceReasoning && locateReasoning) {
    return idx > Math.floor(totalIters * 0.4) ? "trace_code" : "locate";
  }

  // Strong trace signals
  if (traceReasoning) {
    return "trace_code";
  }

  // Code-level search patterns
  const hasRegexSearch = /re\.(findall|search|match)\s*\(/.test(codeLower);
  const hasListCompFilter = /\[.*\bfor\b.*\bin\b.*\bif\b/.test(codeLower);
  const hasFindIndex = /\.find\(|\.index\(|\.count\(/.test(codeLower);

  // Locate: searching/filtering with code or reasoning
  if (hasRegexSearch || hasListCompFilter || hasFindIndex || locateReasoning) {
    return "locate";
  }

  // Print with slices in early iterations = orient
  if (/print\(/.test(codeLower) && /\[.*:.*\]/.test(code) && idx <= 3) {
    return "orient";
  }

  // Defaults based on position
  if (idx <= 2) return "orient";
  return "locate";
}

export function annotatePhases(iterations: Iteration[]): Iteration[] {
  return iterations.map((iter) => ({
    ...iter,
    phase: iter.phase ?? detectPhase(iter, iterations),
  }));
}
