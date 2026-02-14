import { useState } from "react";
import { cn } from "@/lib/utils";
import type { Iteration, Phase } from "@/lib/types";
import { PHASE_INFO } from "@/lib/types";
import { CodeBlock } from "./CodeBlock";
import { OutputBlock } from "./OutputBlock";
import { ConceptCallout } from "./ConceptCallout";

interface IterationCardProps {
  iteration: Iteration;
  isNew: boolean;
}

const LLM_QUERY_RE = /llm_query\s*\(/;

function getConceptCallout(
  iter: Iteration,
): { title: string; body: string } | null {
  const code = iter.code;

  if (iter.iteration === 1) {
    return {
      title: "Context as Environment",
      body: "Input data sits in sandbox variables. The model only sees names and sizes \u2014 not the actual content. It must write Python code to explore.",
    };
  }

  if (iter.iteration <= 3 && /print\(.*\[.*:.*\]/.test(code) && !iter.is_final) {
    return {
      title: "Targeted Exploration",
      body: "The model slices and prints portions of the context. It reads only what it needs, keeping the context window small.",
    };
  }

  if (/\.find\(|\.index\(|\.count\(/.test(code) && iter.iteration <= 4) {
    return {
      title: "Pattern Search",
      body: "String methods like .find() locate specific patterns without loading everything into the LLM context.",
    };
  }

  if (LLM_QUERY_RE.test(code)) {
    return {
      title: "Recursive Sub-Query",
      body: "llm_query() delegates a sub-question to another LLM. The RLM can orchestrate multiple models \u2014 analyzing code snippets, comparing patterns, or synthesizing findings.",
    };
  }

  if (!iter.success && !iter.is_final) {
    return {
      title: "Self-Correction",
      body: "Failures are normal \u2014 the model sees the error and self-corrects. 2\u20134 errors per run is typical.",
    };
  }

  if (iter.is_final) {
    return {
      title: "Convergence",
      body: "SUBMIT() signals the model has enough evidence. It decides when to stop, not a fixed iteration count.",
    };
  }

  return null;
}

function truncateReasoning(text: string, maxLen: number): string {
  if (text.length <= maxLen) return text;
  const truncated = text.slice(0, maxLen);
  const lastSpace = truncated.lastIndexOf(" ");
  return (lastSpace > maxLen * 0.6 ? truncated.slice(0, lastSpace) : truncated) + "\u2026";
}

export function IterationCard({ iteration, isNew }: IterationCardProps) {
  const phase = iteration.phase as Phase | undefined;
  const phaseInfo = phase ? PHASE_INFO[phase] : null;
  const callout = getConceptCallout(iteration);

  // On mobile, cards start collapsed; on desktop, always expanded.
  // We use state so users can toggle. The `isNew` prop auto-expands the
  // latest card during playback so the user sees it arrive.
  const [mobileExpanded, setMobileExpanded] = useState(false);
  const showBody = mobileExpanded || isNew;

  return (
    <div
      className={cn(
        "relative group",
        isNew && "iteration-enter",
        iteration.is_final && "submit-pulse",
      )}
    >
      <div
        className={cn(
          "rounded-xl border bg-card overflow-hidden transition-all",
          !iteration.success && "border-l-4 border-l-destructive",
          iteration.is_final && "border-l-4 border-l-green-500 ring-1 ring-green-500/20",
        )}
      >
        {/* Header — tappable on mobile to toggle */}
        <button
          type="button"
          onClick={() => setMobileExpanded((prev) => !prev)}
          className="flex items-center gap-3 px-4 py-3 border-b bg-muted/30 w-full text-left lg:cursor-default"
        >
          <span className="flex items-center justify-center w-7 h-7 rounded-full bg-primary/10 text-primary text-sm font-semibold shrink-0">
            {iteration.iteration}
          </span>

          {phaseInfo && (
            <span
              className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium text-white shrink-0"
              style={{ backgroundColor: phaseInfo.color }}
            >
              {phaseInfo.label}
            </span>
          )}

          {LLM_QUERY_RE.test(iteration.code) && (
            <span className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-violet-100 text-violet-800 dark:bg-violet-900/30 dark:text-violet-400 shrink-0">
              Sub-LM
            </span>
          )}

          {iteration.is_final && (
            <span className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400 shrink-0">
              SUBMIT
            </span>
          )}

          {!iteration.success && !iteration.is_final && (
            <span className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400 shrink-0">
              Error
            </span>
          )}

          {/* Mobile-only: chevron + reasoning preview */}
          <span className="lg:hidden ml-auto text-muted-foreground shrink-0">
            <svg
              className={cn("w-4 h-4 transition-transform", showBody && "rotate-180")}
              fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
            </svg>
          </span>
        </button>

        {/* Reasoning — always visible on desktop; on mobile show truncated when collapsed */}
        <div className="px-4 py-3 text-sm text-muted-foreground border-b">
          {/* Desktop: full reasoning */}
          <p className="italic hidden lg:block">{iteration.reasoning}</p>
          {/* Mobile: truncated when collapsed, full when expanded */}
          <p className="italic lg:hidden">
            {showBody ? iteration.reasoning : truncateReasoning(iteration.reasoning, 120)}
          </p>
        </div>

        {/* Code + Output — always visible on desktop, collapsible on mobile */}
        <div className={cn("lg:block", showBody ? "block" : "hidden")}>
          {/* Code */}
          <CodeBlock code={iteration.code} />

          {/* Output */}
          <div className="p-4 pt-0">
            <OutputBlock output={iteration.output} success={iteration.success} />
          </div>
        </div>
      </div>

      {/* Educational callout — follows same visibility as body */}
      {callout && (
        <div className={cn("mt-3 lg:block", showBody ? "block" : "hidden")}>
          <ConceptCallout title={callout.title} body={callout.body} />
        </div>
      )}
    </div>
  );
}
