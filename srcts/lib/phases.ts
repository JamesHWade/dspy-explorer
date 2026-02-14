import type { Iteration, Phase } from "./types";

function findSourceVars(code: string): Set<string> {
  const vars = new Set<string>();
  // Match patterns like exec_source('name', ...) or inspect_source('name', ...)
  const matches = code.matchAll(/(?:exec_source|inspect_source)\s*\(\s*['"](\w+)['"]/g);
  for (const m of matches) {
    vars.add(m[1]);
  }
  return vars;
}

export function detectPhase(
  iter: Iteration,
  allIterations: Iteration[],
): Phase {
  const code = iter.code.toLowerCase();
  const idx = iter.iteration;

  // Early iterations that scan structure = orient
  if (idx <= 2 && /list_files|grep|overview|structure/.test(code)) {
    return "orient";
  }

  // SUBMIT or final comparison patterns = identify_gap
  if (iter.is_final || /submit\s*\(/.test(code)) {
    return "identify_gap";
  }

  // Cross-referencing: accessing a different source var than previous iterations
  const currentVars = findSourceVars(iter.code);

  if (currentVars.size > 0 && idx > 3) {
    const previousVars = new Set<string>();
    for (const prev of allIterations.slice(0, idx - 1)) {
      for (const v of findSourceVars(prev.code)) {
        previousVars.add(v);
      }
    }

    const newVars = [...currentVars].filter((v) => !previousVars.has(v));
    if (newVars.length > 0) {
      return "cross_reference";
    }
  }

  // Code tracing patterns (following imports, class hierarchies, etc.)
  if (/import|class\s|def\s|super\(\)|__init__|inherit|base/.test(code)) {
    return "trace_code";
  }

  // General locate: inspect/search/grep patterns
  if (/inspect_source|exec_source.*grep|search|find/.test(code)) {
    return "locate";
  }

  // Default to orient for early, locate for later
  return idx <= 3 ? "orient" : "locate";
}

export function annotatePhases(iterations: Iteration[]): Iteration[] {
  return iterations.map((iter) => ({
    ...iter,
    phase: iter.phase ?? detectPhase(iter, iterations),
  }));
}
