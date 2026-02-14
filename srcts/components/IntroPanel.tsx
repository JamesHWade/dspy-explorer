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
            Recursive Language Models
          </h1>
          <p className="text-lg text-muted-foreground max-w-lg mx-auto">
            An RLM doesn&rsquo;t receive all the source code in its prompt.
            It writes Python code to explore it incrementally.
          </p>
        </div>

        {/* Comparison */}
        <div className="grid sm:grid-cols-2 gap-4">
          <div className="rounded-xl border bg-card p-6 space-y-3">
            <div className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
              Paste everything
            </div>
            <pre className="font-mono text-sm text-muted-foreground leading-relaxed whitespace-pre"><span className="text-foreground">lm</span>({"\n"}  <span className="text-orange-600 dark:text-orange-400">question</span> + {"\n"}  <span className="text-destructive">all_source_code</span>{"\n"})</pre>
            <p className="text-sm text-muted-foreground mt-2">
              The entire codebase goes into the prompt. The model gets one shot to find what matters.
            </p>
          </div>

          <div className="rounded-xl border bg-card p-6 space-y-3">
            <div className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
              Explore incrementally
            </div>
            <pre className="font-mono text-sm leading-relaxed whitespace-pre"><span className="text-foreground">dspy</span>.<span className="text-foreground">RLM</span>({"\n"}  <span className="text-muted-foreground">"question -&gt; answer"</span>,{"\n"}  question=question,{"\n"}  <span className="text-primary font-semibold">max_iterations</span>=15{"\n"})</pre>
            <p className="text-sm text-muted-foreground mt-2">
              Source code lives in the sandbox. The model writes Python to explore what it needs.
            </p>
          </div>
        </div>

        {/* Key insight */}
        <div className="rounded-xl bg-muted/50 p-6 text-center space-y-2">
          <p className="text-sm font-medium">
            Megabytes of source code sit in the sandbox environment.
          </p>
          <p className="text-sm text-muted-foreground">
            The LLM only sees variable names and sizes. It writes code to transfer exactly what
            it needs into the context window.
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
            Traces show a real DSPy RLM exploring Flask&rsquo;s source code
          </p>
        </div>
      </div>
    </div>
  );
}
