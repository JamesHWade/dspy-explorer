export interface ContextVariable {
  name: string;
  size_chars: number;
  n_files: number;
}

export interface TokenUsage {
  input: number;
  output: number;
}

export interface Iteration {
  iteration: number;
  reasoning: string;
  code: string;
  output: string;
  success: boolean;
  is_final: boolean;
  phase?: Phase;
}

export type Phase =
  | "orient"
  | "locate"
  | "trace_code"
  | "cross_reference"
  | "identify_gap";

export interface TraceData {
  run_id: string;
  timestamp: string;
  question: string;
  model: string;
  context_variables: ContextVariable[];
  iterations: Iteration[];
  final_answer: string;
  iterations_used: number;
  llm_calls_used: number;
  total_tokens?: TokenUsage;
}

export interface RunMeta {
  id: string;
  label: string;
  description: string;
  question: string;
  model: string;
  iterations: number;
  is_live?: boolean;
  total_tokens?: TokenUsage;
}

export interface LiveConfig {
  provider: string;
  model: string;
  api_key?: string;
  question: string;
  context?: string;
  signature?: string;
}

export interface ProviderOption {
  provider: string;
  label: string;
  models: { value: string; label: string }[];
  env_var: string;
}

export const PROVIDERS: ProviderOption[] = [
  {
    provider: "openai",
    label: "OpenAI",
    models: [
      { value: "gpt-4o", label: "GPT-4o" },
      { value: "gpt-4o-mini", label: "GPT-4o Mini" },
      { value: "o1-mini", label: "o1-mini" },
    ],
    env_var: "OPENAI_API_KEY",
  },
  {
    provider: "anthropic",
    label: "Anthropic",
    models: [
      { value: "claude-sonnet-4-5-20250929", label: "Claude Sonnet 4.5" },
      { value: "claude-haiku-4-5-20251001", label: "Claude Haiku 4.5" },
    ],
    env_var: "ANTHROPIC_API_KEY",
  },
  {
    provider: "google",
    label: "Google Gemini",
    models: [
      { value: "gemini-2.5-flash", label: "Gemini 2.5 Flash" },
      { value: "gemini-2.5-pro", label: "Gemini 2.5 Pro" },
    ],
    env_var: "GOOGLE_API_KEY",
  },
  {
    provider: "groq",
    label: "Groq",
    models: [
      { value: "llama-3.3-70b-versatile", label: "Llama 3.3 70B" },
      { value: "deepseek-r1-distill-llama-70b", label: "DeepSeek R1 Distill 70B" },
    ],
    env_var: "GROQ_API_KEY",
  },
  {
    provider: "deepseek",
    label: "DeepSeek",
    models: [
      { value: "deepseek-chat", label: "DeepSeek V3" },
      { value: "deepseek-reasoner", label: "DeepSeek Reasoner" },
    ],
    env_var: "DEEPSEEK_API_KEY",
  },
  {
    provider: "mistral",
    label: "Mistral",
    models: [
      { value: "mistral-large-latest", label: "Mistral Large" },
      { value: "mistral-small-latest", label: "Mistral Small" },
    ],
    env_var: "MISTRAL_API_KEY",
  },
  {
    provider: "ollama_chat",
    label: "Ollama (local)",
    models: [
      { value: "llama3.2", label: "Llama 3.2" },
      { value: "qwen2.5-coder", label: "Qwen 2.5 Coder" },
      { value: "mistral", label: "Mistral" },
    ],
    env_var: "OLLAMA_HOST",
  },
];

export interface LiveStatus {
  status: "idle" | "running" | "complete" | "error";
  message?: string;
}

export type AppMode = "replay" | "live";

export type PlaybackState = "idle" | "playing" | "paused" | "done";

export type PlaybackSpeed = 1 | 2 | 3;

export const PHASE_INFO: Record<
  Phase,
  { label: string; color: string; description: string }
> = {
  orient: {
    label: "Orient",
    color: "var(--phase-orient)",
    description: "Scanning source structure and available modules",
  },
  locate: {
    label: "Locate",
    color: "var(--phase-locate)",
    description: "Finding specific code regions via inspect and search",
  },
  trace_code: {
    label: "Trace",
    color: "var(--phase-trace-code)",
    description: "Following code dependency chains and call paths",
  },
  cross_reference: {
    label: "Cross-ref",
    color: "var(--phase-cross-ref)",
    description: "Comparing across multiple source packages",
  },
  identify_gap: {
    label: "Identify",
    color: "var(--phase-identify)",
    description: "Pinpointing the specific gap or answer",
  },
};

export interface ConceptAnnotation {
  trigger_iteration: number;
  trigger_condition?: (iter: Iteration) => boolean;
  title: string;
  body: string;
}
