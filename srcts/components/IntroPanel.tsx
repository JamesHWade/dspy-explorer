interface IntroPanelProps {
  onLearnToolkit: () => void;
  onJumpToTraces: () => void;
}

export function IntroPanel({ onLearnToolkit, onJumpToTraces }: IntroPanelProps) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-6">
      <div className="max-w-2xl w-full space-y-8">
        {/* Hero */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight">
            How RLMs Work
          </h1>
          <p className="text-lg text-muted-foreground max-w-lg mx-auto">
            What if an LLM could write code to explore a codebase
            instead of reading it all at once?
          </p>
        </div>

        {/* Comparison */}
        <div className="grid sm:grid-cols-2 gap-4">
          <div className="rounded-xl border bg-card p-6 space-y-3">
            <div className="text-sm font-semibold text-destructive/80 uppercase tracking-wider">
              Traditional Approach
            </div>
            <h3 className="text-base font-semibold">Paste everything into the prompt</h3>
            <pre className="font-mono text-sm text-muted-foreground leading-relaxed whitespace-pre"><span className="text-foreground">lm</span>({"\n"}  <span className="text-orange-600 dark:text-orange-400">question</span> + {"\n"}  <span className="text-destructive">entire_codebase</span>  <span className="text-destructive/60"># 338K chars</span>{"\n"})</pre>
            <p className="text-sm text-muted-foreground">
              The full source code goes into one prompt. The model gets a single pass to find what matters.
            </p>
          </div>

          <div className="rounded-xl border-2 border-primary/30 bg-primary/5 p-6 space-y-3">
            <div className="text-sm font-semibold text-primary uppercase tracking-wider">
              Recursive Language Model
            </div>
            <h3 className="text-base font-semibold">Write code to explore incrementally</h3>
            <pre className="font-mono text-sm leading-relaxed whitespace-pre"><span className="text-foreground">dspy</span>.<span className="text-foreground">RLM</span>({"\n"}  <span className="text-muted-foreground">"question -&gt; answer"</span>,{"\n"}  question=question,{"\n"}  <span className="text-primary font-semibold">max_iterations</span>=15{"\n"})</pre>
            <p className="text-sm text-muted-foreground">
              Source code lives in a sandbox. The model writes Python to search, slice, and analyze only what it needs.
            </p>
          </div>
        </div>

        {/* Key insight */}
        <div className="rounded-xl bg-muted/50 p-6 text-center space-y-2">
          <p className="text-sm font-medium">
            338K characters of Flask source code, but only 2-5% enters the context window.
          </p>
          <p className="text-sm text-muted-foreground">
            The LLM writes Python to explore the codebase, transferring
            just the fragments it needs to reason about.
          </p>
        </div>

        {/* Addressing the obvious question */}
        <div className="space-y-2 text-sm text-muted-foreground">
          <p className="font-medium text-foreground">
            &ldquo;Isn&rsquo;t this just giving an agent tools?&rdquo;
          </p>
          <p>
            Sort of. The difference is constraint. An agent picks from a menu of
            tools (web search, file read, API call) and the orchestration
            logic is where things get fragile. An RLM has exactly one tool: a Python
            interpreter. The model decides what to do by writing code, not by
            choosing from a fixed set of actions. There&rsquo;s no routing layer,
            no tool descriptions to prompt-engineer, no retry heuristics. The
            sandbox is deterministic: same code in, same output out.
          </p>
          <p>
            The tradeoff: you give up the breadth of arbitrary tools
            for a tighter loop that&rsquo;s easier to reason about and optimize with
            DSPy&rsquo;s compiler.
          </p>
        </div>

        {/* CTA */}
        <div className="text-center space-y-3">
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <button
              onClick={onLearnToolkit}
              className="inline-flex items-center justify-center rounded-lg bg-primary px-8 py-3 text-sm font-medium text-primary-foreground shadow-sm hover:bg-primary/90 transition-colors"
            >
              How does this work?
            </button>
            <button
              onClick={onJumpToTraces}
              className="inline-flex items-center justify-center rounded-lg border px-8 py-3 text-sm font-medium hover:bg-muted/50 transition-colors"
            >
              Jump to traces
            </button>
          </div>
          <p className="text-xs text-muted-foreground">
            Watch a real DSPy RLM explore Flask&rsquo;s source code step by step
          </p>
        </div>
      </div>
    </div>
  );
}
