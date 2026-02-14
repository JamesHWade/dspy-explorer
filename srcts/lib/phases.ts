import type { Iteration, Phase } from "./types";

export function detectPhase(
  iter: Iteration,
  allIterations: Iteration[],
): Phase {
  const code = iter.code.toLowerCase();
  const reasoning = (iter.reasoning ?? "").toLowerCase();
  const idx = iter.iteration;

  // SUBMIT or final answer construction = identify_gap
  if (iter.is_final || /submit\s*\(/.test(code)) {
    return "identify_gap";
  }

  // Early iterations that print/explore to understand structure = orient
  if (
    idx <= 2 &&
    (/print\(.*\[:/.test(code) ||
      /type\(|len\(|dir\(|\.keys\(/.test(code) ||
      /structure|overview|explore|understand/.test(reasoning))
  ) {
    return "orient";
  }

  // Cross-referencing: using llm_query for semantic analysis
  if (/llm_query/.test(code)) {
    return "cross_reference";
  }

  // Code tracing: following definitions, imports, class hierarchies
  if (
    /import|class\s|def\s|super\(\)|__init__|\.find\(.*class/.test(code) ||
    /trace|follow|logic|chain|hierarchy/.test(reasoning)
  ) {
    return "trace_code";
  }

  // Locate: searching, slicing, finding specific content
  if (
    /\.find\(|\.index\(|\.count\(|\[.*:.*\]/.test(code) ||
    /search|find|locate|identify|look for/.test(reasoning)
  ) {
    return "locate";
  }

  // Default to orient for early iterations, locate for later
  return idx <= 3 ? "orient" : "locate";
}

export function annotatePhases(iterations: Iteration[]): Iteration[] {
  return iterations.map((iter) => ({
    ...iter,
    phase: iter.phase ?? detectPhase(iter, iterations),
  }));
}
