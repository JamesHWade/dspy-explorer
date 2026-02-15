import { Eye, Search, MessageCircle, CheckCircle2 } from "lucide-react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { CodeBlock } from "./CodeBlock";

interface ToolkitPanelProps {
  onContinue: () => void;
  onBack: () => void;
}

const actions = [
  {
    tab: "explore",
    name: "print()",
    icon: Eye,
    signature: "print(context[start:end])",
    oneLiner: "Explore variables by slicing and printing",
    example: "print(context[:1000])  # Read the first 1000 chars",
    description:
      "The model slices input variables and prints portions to understand their structure. Only what's printed enters the next prompt.",
    note:
      "The full context can be millions of characters. The model reads it in chunks, deciding what to look at next.",
  },
  {
    tab: "search",
    name: ".find() / slicing",
    icon: Search,
    signature: "context[context.find('class Flask'):...]",
    oneLiner: "Search and extract specific regions",
    example: "idx = context.find('def route')\nprint(context[idx:idx+500])",
    description:
      "Python string methods locate specific patterns. The model navigates large contexts by searching, not scanning.",
    note:
      "Standard Python is the toolkit. The model uses .find(), .count(), slicing, regex, and more to explore.",
  },
  {
    tab: "ask",
    name: "llm_query()",
    icon: MessageCircle,
    signature: "llm_query(prompt)",
    oneLiner: "Send a sub-question to another LLM call",
    example: "summary = llm_query('Summarize this routing mechanism:\\n' + snippet)",
    description:
      "Delegates a focused question to a separate LLM call. Useful for summarising or interpreting code excerpts that need semantic understanding.",
    note:
      "The outer model stays on task while a cheaper inner call handles a detail question. Use llm_query_batched() for multiple prompts.",
  },
  {
    tab: "submit",
    name: "SUBMIT()",
    icon: CheckCircle2,
    signature: "SUBMIT(answer=...)",
    oneLiner: "Return the final answer and stop",
    example: "SUBMIT(answer='Flask decorators work by...')",
    description:
      "Terminates the REPL loop. The model calls this when it has enough evidence to answer.",
    note:
      "There is no fixed iteration limit. The model decides when to stop.",
  },
] as const;

const loopSteps = [
  { label: "Think", num: "1" },
  { label: "Write Python", num: "2" },
  { label: "Execute", num: "3" },
  { label: "Read output", num: "4" },
] as const;

export function ToolkitPanel({ onContinue, onBack }: ToolkitPanelProps) {
  return (
    <div className="min-h-screen bg-background pb-20">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 py-12 space-y-12">
        {/* 1. Header */}
        <div className="space-y-3">
          <button
            onClick={onBack}
            className="text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5" />
            </svg>
            Back
          </button>
          <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">
            How the RLM explores
          </h1>
          <p className="text-sm text-muted-foreground max-w-xl">
            The LLM never sees all the input at once. Instead, it writes
            Python code in a REPL loop, using standard tools to pull in
            only what it needs.
          </p>
        </div>

        {/* 2. Tabbed action cards */}
        <Tabs defaultValue="explore" className="w-full">
          <TabsList className="w-full grid grid-cols-4">
            {actions.map((a) => {
              const Icon = a.icon;
              return (
                <TabsTrigger key={a.tab} value={a.tab} className="text-xs sm:text-sm gap-1.5">
                  <Icon className="w-3.5 h-3.5 hidden sm:block" />
                  {a.tab.charAt(0).toUpperCase() + a.tab.slice(1)}
                </TabsTrigger>
              );
            })}
          </TabsList>

          {actions.map((a) => {
            const Icon = a.icon;
            return (
              <TabsContent key={a.tab} value={a.tab}>
                <div className="rounded-xl border bg-card p-6 space-y-4 mt-2">
                  <div className="flex items-center gap-3 flex-wrap">
                    <div className="flex items-center gap-2">
                      <Icon className="w-4 h-4 text-primary" />
                      <Badge variant="secondary" className="font-mono text-xs">
                        {a.name}
                      </Badge>
                    </div>
                    <span className="text-sm text-muted-foreground">
                      {a.oneLiner}
                    </span>
                  </div>

                  <div className="font-mono text-xs text-muted-foreground bg-muted/50 rounded-md px-3 py-2">
                    {a.signature}
                  </div>

                  <p className="text-sm">{a.description}</p>

                  <CodeBlock code={a.example} className="text-xs" />

                  <p className="text-xs text-muted-foreground">{a.note}</p>
                </div>
              </TabsContent>
            );
          })}
        </Tabs>

        {/* 3. The loop */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">The REPL loop</h2>
          <p className="text-sm text-muted-foreground max-w-lg">
            Each iteration follows the same cycle. Code executes in a
            sandboxed Python interpreter (Deno + Pyodide). The model only sees the printed output.
          </p>

          <div className="flex items-center justify-center gap-0 py-4 overflow-x-auto">
            {loopSteps.map((step, i) => (
              <div key={step.label} className="flex items-center">
                <div className="flex flex-col items-center gap-1.5">
                  <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-lg border bg-card flex items-center justify-center text-sm font-mono font-semibold text-muted-foreground">
                    {step.num}
                  </div>
                  <span className="text-[10px] sm:text-xs font-medium text-muted-foreground whitespace-nowrap">
                    {step.label}
                  </span>
                </div>
                {i < loopSteps.length - 1 && (
                  <svg
                    className="w-6 h-4 sm:w-8 text-muted-foreground/40 shrink-0 mx-1"
                    viewBox="0 0 24 12"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path d="M2 6h16m0 0-4-4m4 4-4 4" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                )}
              </div>
            ))}
          </div>

          <div className="flex justify-center">
            <div className="text-xs text-muted-foreground border border-dashed border-muted-foreground/30 rounded-full px-4 py-1.5">
              repeats until <code className="font-mono font-semibold text-foreground">SUBMIT()</code>
            </div>
          </div>
        </div>
      </div>

      {/* Sticky bottom CTA */}
      <div className="fixed bottom-0 inset-x-0 border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80 z-30">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between">
          <span className="text-sm text-muted-foreground hidden sm:block">
            See these tools in action on real Flask source code
          </span>
          <button
            onClick={onContinue}
            className="inline-flex items-center justify-center rounded-lg bg-primary px-6 py-2.5 text-sm font-medium text-primary-foreground shadow-sm hover:bg-primary/90 transition-colors w-full sm:w-auto"
          >
            Continue to traces
            <svg className="w-4 h-4 ml-2" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
