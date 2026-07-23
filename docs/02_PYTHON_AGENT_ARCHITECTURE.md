# Python Agent Architecture Specification

> **Status:** Definitive architecture reference for Python implementation.
> **Principle:** Interface-driven, async-first, plugin-architecture, event-sourced.
> **Target:** Python 3.12+, no framework dependency beyond stdlib + httpx + Pydantic.

---

## 1. Overall Architecture

### 1.1 Architectural Style

**Hexagonal Architecture (Ports & Adapters)** with an **Event-Driven Pipeline** core.

```
┌──────────────────────────────────────────────────────────────┐
│                     EXTERNAL ADAPTERS                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │
│  │ LLM API  │  │FileSystem│  │ Web/HTTP │  │ Vector Store │ │
│  │ (DeepSeek│  │ (Local)  │  │ (Search) │  │  (TF-IDF)   │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘ │
└───────┼─────────────┼─────────────┼───────────────┼─────────┘
        │             │             │               │
        ▼             ▼             ▼               ▼
┌──────────────────────────────────────────────────────────────┐
│                      PORT INTERFACES                          │
│  LLMClient    FileSystem    HttpClient    VectorStore        │
│  (Protocol)   (Protocol)    (Protocol)    (Protocol)         │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                    APPLICATION CORE                           │
│                                                              │
│  ┌─────────────┐  ┌──────────┐  ┌──────────────────────┐    │
│  │  Pipeline   │  │  Event   │  │   Capability Layer   │    │
│  │  (Stages)   │◄─┤   Bus    │──┤   (Tools + Skills +  │    │
│  │             │  │          │  │    Search + Providers)│    │
│  └──────┬──────┘  └──────────┘  └──────────────────────┘    │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────────────────────────────────────────────┐    │
│  │                   DOMAIN SERVICES                     │    │
│  │                                                      │    │
│  │  Memory    Reasoning    Planner    Evolution   Policy │    │
│  │  Service   Service      Service    Service    Service │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │                   DOMAIN MODEL                        │    │
│  │  CognitiveState   Episode   Concept   Mutation   ...  │    │
│  └──────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

### 1.2 Core Design Principles

| Principle | Implementation |
|-----------|---------------|
| **Ports & Adapters** | Every external dependency (LLM, FS, HTTP) is behind a Protocol interface |
| **Event-Driven Pipeline** | Pipeline stages communicate via typed events on an internal bus |
| **Plugin Architecture** | Tools, skills, search providers, pipeline stages are all pluggable via registry |
| **Dependency Inversion** | High-level modules depend on abstractions (Protocols), not implementations |
| **Single Source of Truth** | CognitiveState is the authoritative state snapshot; all writes go through MutationEngine |
| **Async-First** | All I/O operations are async; CPU-bound work is isolated |
| **Immutable Events** | Pipeline events are frozen dataclasses — never mutated, only created |

---

## 2. Layered Architecture

```
Layer 0: Infrastructure
  ├── llm/            (LLM client protocol + implementations)
  ├── storage/        (File system abstraction)
  ├── http/           (HTTP client protocol)
  └── vector/         (Vector store protocol)

Layer 1: Domain Model
  ├── models/         (Pydantic models: Episode, Concept, CognitiveState, Mutation, ...)
  └── events/         (Pipeline events: UserInputReceived, ToolExecuted, MemoryUpdated, ...)

Layer 2: Domain Services
  ├── memory/         (WorkingMemory, EpisodicMemory, UserProfile, ToolMemory, MemoryWriter)
  ├── concepts/       (ConceptExtractor)
  ├── reasoning/      (ConceptGraphBuilder, ConceptReasoner)
  ├── evolution/      (MemoryEvolution, ConceptEvolver, FeedbackProcessor)
  ├── policy/         (DriftController)
  ├── routing/        (ToolRouter, RouterTelemetry)
  └── retrieval/      (VectorStore, RagFeedback)

Layer 3: Capability Layer
  ├── tools/          (Tool Protocol + ToolRegistry + built-in tools)
  ├── skills/         (Skill Protocol + SkillRegistry + built-in skills)
  ├── search/         (SearchProvider Protocol + SearchManager + providers)
  ├── planner/        (IntentParser, DomainClassifier, ExecutionPlanner)
  └── execution/      (ExecutionEngine: orchestrate tool/skill/search execution)

Layer 4: Orchestration
  ├── pipeline/       (Pipeline: ordered sequence of PipelineStage)
  └── bus/            (EventBus: typed event emission + subscription)

Layer 5: Application
  └── agent.py        (Agent: public API, configuration, lifecycle management)
```

### Dependency Rules

```
Layer 5 → depends on → Layer 4
Layer 4 → depends on → Layer 3 + Layer 2
Layer 3 → depends on → Layer 2 + Layer 1
Layer 2 → depends on → Layer 1 + Layer 0 (Protocols only)
Layer 1 → depends on → nothing internal (Pydantic + stdlib only)
Layer 0 → depends on → nothing internal (stdlib + external libs only)
```

**Forbidden:**
- Layer 2 must never import from Layer 3 or Layer 4
- Layer 1 must never import from any other layer
- Layer 0 implementations must never be imported directly by Layer 2+ (use Protocols)

---

## 3. Package Structure

```
agent/
├── __init__.py
├── agent.py                      # Agent: public API entry point
├── config.py                     # AgentConfig (Pydantic Settings)
├── exceptions.py                 # AgentException hierarchy
│
├── models/                       # Layer 1: Domain Model
│   ├── __init__.py
│   ├── state.py                  # CognitiveState, MemoryState, ConceptGraphState, ...
│   ├── memory.py                 # Episode, WorkingMemoryEntry, UserProfileData
│   ├── concepts.py               # Concept, ExtractedConcept, ConceptGraphNode, ConceptGraphEdge
│   ├── tools.py                  # ToolDefinition, ToolResult, ToolCallRecord
│   ├── skills.py                 # SkillDefinition, SkillResult, SkillExecutionRecord
│   ├── routing.py                # RouterResult, RoutingRecord, ToolMetrics
│   ├── reasoning.py              # ReasoningResult, ReasoningTrace
│   ├── evolution.py              # ScoredMemory, EvolutionSignal, ConsolidationResult, ...
│   ├── policy.py                 # CognitivePolicy, CompressionSignal, DriftMetrics
│   ├── mutations.py              # StateMutation union type, all 7 variants
│   ├── retrieval.py              # VectorSearchResult, RetrievalRecord, DocumentWeight
│   ├── search.py                 # SearchResult, SearchQuery, SearchProviderInfo
│   └── events.py                 # PipelineEvent union type, all event variants
│
├── ports/                        # Layer 0: Port Interfaces (Protocols)
│   ├── __init__.py
│   ├── llm.py                    # LLMClient Protocol
│   ├── storage.py                # FileStorage Protocol
│   ├── http_client.py            # HttpClient Protocol
│   ├── vector_store.py           # VectorStore Protocol
│   ├── event_bus.py              # EventBus Protocol
│   └── logger.py                 # Logger Protocol
│
├── infrastructure/               # Layer 0: Adapter Implementations
│   ├── __init__.py
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── deepseek.py           # DeepSeek API adapter (OpenAI-compatible)
│   │   └── mock.py               # Mock LLM for testing
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── local_fs.py           # Local file system adapter
│   │   └── memory_fs.py          # In-memory file system for testing
│   ├── http/
│   │   ├── __init__.py
│   │   └── httpx_client.py       # HTTPX-based adapter
│   ├── vector/
│   │   ├── __init__.py
│   │   └── tfidf_store.py        # TF-IDF VectorStore implementation
│   └── logging/
│       ├── __init__.py
│       └── structlog_adapter.py  # Structlog adapter
│
├── memory/                       # Layer 2: Memory Services
│   ├── __init__.py
│   ├── working.py                # WorkingMemory
│   ├── episodic.py               # EpisodicMemory
│   ├── profile.py                # UserProfile
│   ├── tool_stats.py             # ToolMemory
│   ├── store.py                  # MemoryStore (YAML frontmatter persistence)
│   └── writer.py                 # MemoryWriter (post-interaction classification)
│
├── concepts/                     # Layer 2: Concept Services
│   ├── __init__.py
│   └── extractor.py              # ConceptExtractor
│
├── reasoning/                    # Layer 2: Reasoning Services
│   ├── __init__.py
│   ├── graph.py                  # ConceptGraphBuilder
│   ├── reasoner.py               # ConceptReasoner
│   └── feedback.py               # FeedbackProcessor
│
├── evolution/                    # Layer 2: Evolution Services
│   ├── __init__.py
│   ├── scoring.py                # Pure scoring functions (decay, reinforce, consolidate)
│   ├── memory_evolution.py       # Episodic memory evolution cycle
│   └── concept_evolver.py        # ConceptEvolver (merge, split, decay)
│
├── policy/                       # Layer 2: Policy Services
│   ├── __init__.py
│   └── controller.py             # DriftController
│
├── routing/                      # Layer 2: Routing Services
│   ├── __init__.py
│   ├── router.py                 # ToolRouter (keyword-scoring classifier)
│   └── telemetry.py              # RouterTelemetry
│
├── retrieval/                    # Layer 2: Retrieval Services
│   ├── __init__.py
│   └── feedback.py               # RagFeedback
│
├── tools/                        # Layer 3: Tool System
│   ├── __init__.py
│   ├── protocol.py               # Tool Protocol (abstract base)
│   ├── registry.py               # ToolRegistry (discovery + registration)
│   ├── decision.py               # ToolDecisionPolicy (LLM-based decision)
│   └── builtins/
│       ├── __init__.py
│       ├── web_search.py         # WebSearchTool
│       ├── todos.py              # GetTodosTool, AddTodosTool, TodoStatsTool
│       ├── time.py               # GetCurrentTimeTool
│       └── wiki_crud.py          # ListWikiTool, ReadWikiTool, WriteWikiTool, DeleteWikiTool, SearchWikiTool
│
├── skills/                       # Layer 3: Skill System
│   ├── __init__.py
│   ├── protocol.py               # Skill Protocol (abstract base)
│   ├── registry.py               # SkillRegistry
│   └── builtins/
│       ├── __init__.py
│       ├── location.py           # GetLocationSkill
│       └── file_reader.py        # ReadFileSkill
│
├── search/                       # Layer 3: Search Framework
│   ├── __init__.py
│   ├── protocol.py               # SearchProvider Protocol (abstract base)
│   ├── manager.py                # SearchManager (orchestrate, merge, rank, dedup)
│   └── providers/
│       ├── __init__.py
│       ├── bing.py               # BingSearchProvider
│       ├── duckduckgo.py         # DuckDuckGoSearchProvider
│       ├── bilibili.py           # BilibiliSearchProvider
│       ├── github.py             # GitHubSearchProvider
│       ├── arxiv.py              # ArXivSearchProvider
│       ├── local.py              # LocalFileSearchProvider
│       └── obsidian.py           # ObsidianVaultSearchProvider
│
├── planner/                      # Layer 3: Planner
│   ├── __init__.py
│   ├── intent.py                 # IntentParser (Intent + Domain + Platform)
│   ├── plan.py                   # ExecutionPlan, PlanStep
│   └── planner.py                # Planner: Intent → ExecutionPlan
│
├── execution/                    # Layer 3: Execution Engine
│   ├── __init__.py
│   ├── engine.py                 # ExecutionEngine: execute plan steps (seq/parallel)
│   ├── fallback.py               # FallbackStrategy: provider downgrade
│   └── verifier.py               # ResultVerifier: validate tool outputs
│
├── pipeline/                     # Layer 4: Pipeline
│   ├── __init__.py
│   ├── protocol.py               # PipelineStage Protocol
│   ├── context.py                # PipelineContext (immutable state carrier)
│   ├── pipeline.py               # Pipeline: ordered stage sequence executor
│   └── stages/
│       ├── __init__.py
│       ├── sanitize.py           # SanitizeStage
│       ├── route.py              # RouteStage
│       ├── retrieve.py           # RetrieveStage
│       ├── reason.py             # ReasonStage
│       ├── plan.py               # PlanStage (Intent → ExecutionPlan)
│       ├── execute.py            # ExecuteStage (run plan steps)
│       ├── prompt.py             # PromptStage (build system prompt)
│       ├── generate.py           # GenerateStage (LLM streaming call)
│       ├── sanitize_response.py  # ResponseSanitizeStage (strip leaked tool calls)
│       ├── persist.py            # PersistStage (memory write + state save)
│       ├── learn.py              # LearnStage (telemetry + feedback + evolution)
│       └── health.py             # HealthStage (periodic health check)
│
├── bus/                          # Layer 4: Event Bus
│   ├── __init__.py
│   ├── protocol.py               # EventBus Protocol
│   └── memory_bus.py             # InMemoryEventBus implementation
│
└── observability/                # Cross-cutting
    ├── __init__.py
    ├── health.py                  # HealthCheck service
    ├── metrics.py                 # MetricsCollector
    └── tracer.py                  # ExecutionTracer (audit trail)
```

---

## 4. Core Lifecycle

### 4.1 Agent Lifecycle

```
Agent.__init__(config)
  → Load configuration
  → Initialize infrastructure adapters (LLM, Storage, HTTP, Vector)
  → Initialize domain services (Memory, Reasoning, Evolution, Policy, Routing, Retrieval)
  → Initialize capability layer (ToolRegistry, SkillRegistry, SearchManager, Planner, ExecutionEngine)
  → Initialize event bus
  → Build pipeline from stages
  → Load persisted state (episodes, concepts, profile, policy, vector index)
  → Health check

Agent.process(user_input, session_id) → AgentResponse
  → Create PipelineContext with user input + session state
  → Execute pipeline stages in sequence
  → Return AgentResponse {text, tool_calls, events}

Agent.shutdown()
  → Save all state
  → Close connections
  → Emit shutdown event
```

### 4.2 Pipeline Execution Lifecycle

```
PipelineContext (immutable, carried through all stages)

Stage 1:  SanitizeStage
  Input:  raw user text
  Output: sanitized text (≤4000 chars, injection-free)
  Events: InputSanitized

Stage 2:  RouteStage
  Input:  sanitized text
  Output: RouterResult {intent, confidence, reason}
  Events: IntentClassified

Stage 3:  RetrieveStage
  Input:  sanitized text + RouterResult
  Output: MemoryContext {wiki_results, episodic_ctx, profile_ctx, reasoning_ctx}
  Events: MemoryRetrieved, ConceptsReasoned

Stage 4:  ReasonStage
  Input:  MemoryContext
  Output: ReasoningResult (injected into MemoryContext)
  Events: ReasoningCompleted

Stage 5:  PlanStage
  Input:  sanitized text + MemoryContext
  Output: ExecutionPlan {steps: [{tool/skill/search, args, priority, parallel_group}]}
  Events: PlanGenerated

Stage 6:  ExecuteStage
  Input:  ExecutionPlan
  Output: ExecutionResult {results: [{tool, success, data, latency}], failures: [...]}
  Events: ToolExecuted*, SkillExecuted*, SearchExecuted*

Stage 7:  PromptStage
  Input:  MemoryContext + ExecutionResult
  Output: SystemPrompt (≤8000 chars)
  Events: PromptBuilt

Stage 8:  GenerateStage
  Input:  SystemPrompt + ChatHistory + UserText
  Output: StreamingResponse (chunk callback)
  Events: LLMCallStarted, LLMChunkReceived*, LLMCallCompleted

Stage 9:  SanitizeResponseStage
  Input:  Raw LLM response
  Output: Cleaned response
  Events: ResponseSanitized

Stage 10: PersistStage
  Input:  Full interaction record
  Output: Persisted memory state
  Events: MemoryWritten, ConceptsExtracted, StateSaved

Stage 11: LearnStage
  Input:  Interaction outcome
  Output: Updated telemetry + feedback + evolution (if cycle trigger)
  Events: RouterLearned, RAGUpdated, EvolutionCycleCompleted*

Stage 12: HealthStage (conditional: every 15 interactions)
  Input:  Current cognitive state
  Output: HealthReport
  Events: HealthCheckCompleted
```

### 4.3 Session Lifecycle

```
Session = {
  session_id: str
  working_memory: WorkingMemory        (per-session, in-memory only)
  conversation_history: list[Message]   (for LLM context)
  created_at: datetime
  last_active: datetime
}

Sessions are ephemeral. On restart, only long-term memory persists.
Working memory and conversation history are lost.
```

---

## 5. Memory Architecture

### 5.1 Memory Types

| Type | Scope | Persistence | Capacity | Update Trigger |
|------|-------|-------------|----------|---------------|
| Working Memory | Session | None (ephemeral) | 20 messages | Every message |
| Episodic Memory | Global | JSON + Markdown files | 200 entries | After each interaction |
| Semantic Memory (Concepts) | Global | Markdown files (YAML) | Unlimited | After each interaction |
| User Profile | Global | JSON + Markdown file | 1 record | After profile-relevant interactions |
| Tool Memory | Global | JSON file | Per-tool records | After every tool execution |

### 5.2 Memory Service Interfaces

```python
# Protocol: all memory services follow this pattern
class MemoryStore(Protocol[T]):
    async def load(self) -> T: ...
    async def save(self, data: T) -> None: ...
    async def query(self, **filters) -> list[T]: ...

# WorkingMemory (ephemeral)
class WorkingMemory:
    def push(self, entry: WorkingMemoryEntry) -> None: ...
    def get_last(self, n: int) -> list[WorkingMemoryEntry]: ...
    def get_recent_context(self, max_tokens: int) -> str: ...
    def clear(self) -> None: ...

# EpisodicMemory (persistent)
class EpisodicMemory:
    async def add(self, entry: Episode) -> Episode: ...
    async def search(self, query: str, top_k: int) -> list[Episode]: ...
    async def reinforce(self, episode_id: str, amount: float) -> bool: ...
    async def apply_decay(self) -> int: ...  # returns decayed count
    async def get_candidates_for_removal(self) -> list[Episode]: ...
    async def get_active_entries(self) -> list[Episode]: ...
    def format_for_context(self, max_entries: int) -> str: ...

# MemoryWriter (post-interaction coordinator)
class MemoryWriter:
    async def analyze(self, interaction: Interaction) -> list[MemoryWriteDecision]: ...
    async def commit(self, decisions: list[MemoryWriteDecision], interaction: Interaction) -> None: ...
    async def run_maintenance(self) -> None: ...
```

### 5.3 Memory Update Policy

```
After EVERY interaction:
  1. analyze() → classify interaction into decisions
     - Profile: regex patterns for identity/project/interest statements
     - Episodic: keyword detection for goals/decisions/milestones
     - Semantic: fact detection for persistent knowledge
     - Tool: unconditional tool usage record
  2. commit() → persist decisions
     - Consolidation check (Jaccard > 0.85 → reinforce existing, skip new)
     - Write to episodic store (with evolution fields)
     - Trigger concept extraction
     - Write to markdown mirror (best-effort)

Every 10 interactions:
  3. run_maintenance() → decay + reinforcement cycle
     - Exponential decay: decayScore = importanceScore × e^(-0.03 × (1 - usageFreq × 0.6) × cycles)
     - Mark for removal: decayScore < 0.25 AND unused AND ≥14 cycles
     - Prune: remove marked entries when over capacity (200)
```

---

## 6. Reasoning Architecture

### 6.1 Concept Extraction Flow

```
Episode content (markdown string)
  → extract_from_headings()      # ##, ### headings → confidence +0.35
  → extract_from_bigrams()       # Chinese bigrams (CJK) → frequency × 0.3
  → extract_from_trigrams()      # Chinese trigrams → frequency × 0.5
  → extract_from_english_terms() # CamelCase, snake_case, 2-word phrases → ×0.4
  → match_existing()             # boost +0.2 if matches known concept
  → rank_and_filter()            # min confidence 0.25, max 6 concepts
  → deduplicate()                # remove subset/similar (≥60% word overlap)
  → ExtractedConcept[]
```

### 6.2 Concept Graph Construction

```
load_concepts() → ConceptData[]
  → build_full_graph() → ConceptGraph
    Nodes: ConceptGraphNode {id, name, slug, confidence, source_episodes, related, tags, degree}
    Edges:
      Type "related":       explicit related[] links (weight 0.8)
      Type "shared-episode": concepts sharing source episodes (weight = shared/max(2, min_sources))
      Type "tag-overlap":    concepts sharing tags (weight = shared_tags/max_tags)
    → compute degree per node (total edge count)

  → build_subgraph(full_graph, seed_slugs) → ConceptSubgraph
    → 1-hop expansion from seeds
    → collect all edges among seed + neighbor nodes
    → identify central concepts (highest subgraph degree)
```

### 6.3 Reasoning Engine (3 Strategies)

```
reason(query, subgraph, full_graph) → ReasoningResult:
  Strategy 1 (Graph Traversal):
    → high-degree nodes → key_concepts
    → nodes bridging clusters → bridging_concepts
    → edge labels → relationships
  Strategy 2 (Pattern Matching):
    → query-co-occurring concepts → key_concepts
    → co-occurrence without explicit edge → inferred_insights
    → contradictory co-occurrence → contradictions
  Strategy 3 (Abstraction):
    → dense node groups → concept_clusters
    → cluster themes → inferred_insights
    → conflicting membership → contradictions

  Merge: union of results from all strategies
  Confidence: 0.4 × traversal + 0.3 × pattern + 0.3 × abstraction
```

### 6.4 Service Interfaces

```python
class ConceptExtractor:
    def extract(self, content: str, existing_concepts: list[str]) -> list[ExtractedConcept]: ...

class ConceptGraphBuilder:
    def build_full(self, concepts: list[ConceptData]) -> ConceptGraph: ...
    def build_subgraph(self, full: ConceptGraph, seeds: list[str]) -> ConceptSubgraph: ...

class ConceptReasoner:
    def reason(self, query: str, subgraph: ConceptSubgraph, full: ConceptGraph) -> ReasoningResult: ...
```

---

## 7. Planner Architecture

### 7.1 Intent Model

```
Intent = {
  action: "search" | "read" | "write" | "analyze" | "summarize" | "chat" | "execute"
  domain: "code" | "video" | "paper" | "local_file" | "knowledge" | "general"
  platform: "bilibili" | "github" | "arxiv" | "obsidian" | "local" | "web" | "none"
  confidence: float  # 0..1
}
```

### 7.2 Execution Plan

```
ExecutionPlan = {
  plan_id: str
  steps: list[PlanStep]
  strategy: "sequential" | "parallel" | "mixed"
  fallback: FallbackStrategy
  created_at: datetime
}

PlanStep = {
  step_id: str
  capability_type: "tool" | "skill" | "search"
  capability_name: str
  args: dict
  priority: int          # lower = higher priority
  parallel_group: int | None  # steps in same group run in parallel
  depends_on: list[str]  # step_ids that must complete first
  retry_policy: RetryPolicy
  timeout_ms: int
}

FallbackStrategy = {
  max_retries: int
  alternative_providers: list[str]  # fallback capability names
  degrade_policy: "best_available" | "fail_fast" | "partial_results"
}
```

### 7.3 Planner Service

```python
class IntentParser:
    """Parse user query into structured Intent."""
    def parse(self, query: str, context: MemoryContext) -> Intent: ...

class ExecutionPlanner:
    """Build ExecutionPlan from Intent + available capabilities."""
    async def plan(
        self,
        intent: Intent,
        available_tools: list[ToolInfo],
        available_skills: list[SkillInfo],
        available_providers: list[SearchProviderInfo],
    ) -> ExecutionPlan: ...

class Planner:
    """Orchestrate Intent parsing → Execution planning."""
    def __init__(
        self,
        intent_parser: IntentParser,
        execution_planner: ExecutionPlanner,
    ): ...
    async def plan(self, query: str, context: MemoryContext) -> ExecutionPlan: ...
```

---

## 8. Execution Engine

### 8.1 Responsibilities

1. Accept an ExecutionPlan
2. Resolve dependencies (topological sort)
3. Execute steps in order (sequential groups) or parallel (same parallel_group)
4. Handle failures per-step (retry, fallback provider)
5. Collect results
6. Apply result verification
7. Return ExecutionResult

### 8.2 Interfaces

```python
class ExecutionEngine:
    def __init__(
        self,
        tool_registry: ToolRegistry,
        skill_registry: SkillRegistry,
        search_manager: SearchManager,
        fallback: FallbackStrategy,
        verifier: ResultVerifier,
        event_bus: EventBus,
    ): ...

    async def execute(self, plan: ExecutionPlan) -> ExecutionResult: ...

class FallbackStrategy:
    """Determine next action when a step fails."""
    async def on_failure(
        self,
        step: PlanStep,
        error: Exception,
        attempt: int,
        available_alternatives: list[str],
    ) -> FallbackAction: ...  # retry | switch_provider | skip | abort

class ResultVerifier:
    """Validate tool execution outputs."""
    async def verify(self, result: ToolResult) -> VerificationResult: ...
    # VerificationResult: {valid: bool, issues: list[str], quality: float}
```

### 8.3 Execution Flow

```
ExecutionEngine.execute(plan):
  1. Validate plan (check all capabilities exist in registries)
  2. Topological sort steps by depends_on
  3. Group steps by parallel_group (None = sequential)
  4. For each group (sequential):
     a. For each step in group (parallel):
        - Resolve capability from appropriate registry
        - Execute with timeout
        - On failure: consult FallbackStrategy
        - Verify result with ResultVerifier
        - Emit ToolExecuted/SkillExecuted/SearchExecuted event
     b. Await all parallel steps in group
  5. Assemble ExecutionResult
  6. Return
```

---

## 9. Capability Layer

### 9.1 Design Principle

Every capability (Tool, Skill, SearchProvider) implements a common pattern:

```python
class Capability(ABC):
    """Base for all executable capabilities."""
    name: str                          # unique identifier
    description: str                   # human-readable
    version: str                       # semantic version
    metadata: CapabilityMetadata       # tags, permissions, cost, timeout

    @abstractmethod
    async def execute(self, args: dict, context: ExecutionContext) -> CapabilityResult: ...

    @abstractmethod
    def validate_args(self, args: dict) -> bool: ...
```

### 9.2 Tool Protocol

```python
class Tool(Capability):
    """External-world interaction capability."""
    permissions: Literal["safe"]  # tools are always safe (no privileged access)
    parameters: JsonSchema        # JSON Schema for args validation
    examples: list[ToolExample]   # few-shot examples for LLM decision

    @abstractmethod
    async def execute(self, args: dict, context: ExecutionContext) -> ToolResult: ...

class ToolRegistry:
    """Auto-discover and register tools."""
    def register(self, tool: Tool) -> None: ...
    def unregister(self, name: str) -> None: ...
    def get(self, name: str) -> Tool: ...
    def list_all(self) -> list[ToolInfo]: ...
    def discover(self, package_path: str) -> int: ...  # auto-import from package
    def get_for_llm(self) -> list[dict]: ...  # OpenAI-compatible tool descriptions
```

### 9.3 Skill Protocol

```python
class Skill(Capability):
    """Privileged system capability."""
    permissions: Literal["safe", "privileged"]

    @abstractmethod
    async def execute(self, args: dict, context: ExecutionContext) -> SkillResult: ...

class SkillRegistry:
    """Register and manage skills."""
    def register(self, skill: Skill) -> None: ...
    def get(self, name: str) -> Skill: ...
    def list_all(self) -> list[SkillInfo]: ...
    def validate_permissions(self, name: str, context: ExecutionContext) -> bool: ...
```

### 9.4 Search Provider Protocol

```python
class SearchProvider(Capability):
    """Search source capability."""
    domain: str                        # "web", "video", "code", "paper", "local"
    platforms: list[str]               # "bing", "bilibili", "github", "arxiv"
    fallback_providers: list[str]      # alternative provider names
    rate_limit: RateLimit              # requests per minute

    @abstractmethod
    async def search(self, query: str, num_results: int) -> SearchResult: ...

class SearchManager:
    """Orchestrate multi-provider search with merge/rank/dedup."""
    def register_provider(self, provider: SearchProvider) -> None: ...
    async def search(
        self,
        query: str,
        providers: list[str] | None = None,  # None = all registered
        strategy: SearchStrategy = SearchStrategy.PARALLEL,
    ) -> MergedSearchResult: ...
    def rank(self, results: list[SearchResult], query: str) -> list[SearchResult]: ...
    def deduplicate(self, results: list[SearchResult]) -> list[SearchResult]: ...
```

---

## 10. Event Bus

### 10.1 Purpose

Decouple pipeline stages. Stages emit typed events. Observability, logging, and audit trail consume events without modifying pipeline logic.

### 10.2 Event Types

```python
# Pipeline lifecycle events
class InputSanitized(PipelineEvent): ...
class IntentClassified(PipelineEvent): ...
class MemoryRetrieved(PipelineEvent): ...
class ConceptsReasoned(PipelineEvent): ...
class PlanGenerated(PipelineEvent): ...
class ToolExecuted(PipelineEvent): ...
class SkillExecuted(PipelineEvent): ...
class SearchExecuted(PipelineEvent): ...
class PromptBuilt(PipelineEvent): ...
class LLMCallStarted(PipelineEvent): ...
class LLMChunkReceived(PipelineEvent): ...
class LLMCallCompleted(PipelineEvent): ...
class ResponseSanitized(PipelineEvent): ...
class MemoryWritten(PipelineEvent): ...
class ConceptsExtracted(PipelineEvent): ...
class StateSaved(PipelineEvent): ...
class RouterLearned(PipelineEvent): ...
class RAGUpdated(PipelineEvent): ...
class EvolutionCycleCompleted(PipelineEvent): ...
class HealthCheckCompleted(PipelineEvent): ...

# System events
class AgentInitialized(PipelineEvent): ...
class AgentShutdown(PipelineEvent): ...
class ErrorOccurred(PipelineEvent): ...
class ReentrancyBlocked(PipelineEvent): ...
```

### 10.3 EventBus Protocol

```python
class EventBus(Protocol):
    """Typed event emission and subscription."""

    async def emit(self, event: PipelineEvent) -> None: ...
    def subscribe(self, event_type: type[PipelineEvent], handler: Callable) -> None: ...
    def unsubscribe(self, event_type: type[PipelineEvent], handler: Callable) -> None: ...

    # Convenience: context manager for temporary subscriptions
    @contextmanager
    def collect(self, *event_types: type[PipelineEvent]) -> AsyncIterator[list[PipelineEvent]]: ...

class InMemoryEventBus:
    """Default implementation. Supports async handlers."""
    # Internal: dict[type, set[Callable]]
    # emit() calls all handlers for the event's type concurrently
```

---

## 11. Provider System

### 11.1 Philosophy

Every external integration (LLM, search, file system, HTTP) is behind a Protocol. The Agent core never depends on concrete implementations. This enables:

- **Testing:** Swap real providers with mocks
- **Evolution:** Swap DeepSeek for another LLM without changing agent logic
- **Multi-provider:** Run multiple search providers in parallel, merge results

### 11.2 Provider Protocols

```python
class LLMClient(Protocol):
    """Abstract LLM API client."""
    async def stream(
        self,
        messages: list[Message],
        on_chunk: Callable[[str], Awaitable[None]],
        **kwargs,
    ) -> str: ...

    async def complete(
        self,
        messages: list[Message],
        **kwargs,
    ) -> LLMResponse: ...

class FileStorage(Protocol):
    """Abstract file system."""
    async def read(self, path: str) -> str: ...
    async def write(self, path: str, content: str) -> None: ...
    async def exists(self, path: str) -> bool: ...
    async def list_dir(self, path: str) -> list[str]: ...
    async def delete(self, path: str) -> None: ...
    async def mkdir(self, path: str) -> None: ...

class HttpClient(Protocol):
    """Abstract HTTP client."""
    async def get(self, url: str, **kwargs) -> HttpResponse: ...
    async def post(self, url: str, json: dict, **kwargs) -> HttpResponse: ...

class VectorStore(Protocol):
    """Abstract vector store."""
    async def build(self, documents: list[Document]) -> None: ...
    async def search(self, query: str, top_k: int) -> list[VectorSearchResult]: ...
    async def apply_feedback(self, doc_path: str, delta: float) -> None: ...
    def serialize(self) -> str: ...
    def deserialize(self, data: str) -> None: ...
```

---

## 12. Configuration System

### 12.1 Design

```python
class AgentConfig(BaseSettings):
    """All agent configuration. Loaded from env vars / config file / defaults."""

    # LLM
    llm_endpoint: str = "https://api.deepseek.com/v1"
    llm_model: str = "deepseek-chat"
    llm_api_key: str = ""
    llm_timeout_ms: int = 60_000
    llm_max_tokens: int = 4096
    llm_temperature: float = 0.7

    # Memory
    memory_working_capacity: int = 20
    memory_episodic_capacity: int = 200
    memory_base_path: str = "./agent-memory"

    # Evolution
    evolution_cycle_interval: int = 10       # memory evolution
    evolution_concept_interval: int = 20     # concept evolution
    evolution_health_interval: int = 15      # health check

    # Safety
    safety_max_update_per_cycle: float = 0.05
    safety_min_confirmations: int = 3
    safety_low_confidence_threshold: float = 0.3
    safety_max_input_chars: int = 4000
    safety_max_prompt_chars: int = 8000

    # Decay
    decay_base_rate: float = 0.03
    decay_usage_damping: float = 0.6
    decay_removal_threshold: float = 0.25
    decay_removal_cycles: int = 14

    # Concept Evolution
    concept_merge_similarity: float = 0.7
    concept_decay_days: int = 7
    concept_decay_rate: float = 0.05
    concept_decay_floor: float = 0.15

    # Search
    search_default_providers: list[str] = ["bing", "duckduckgo"]
    search_max_results: int = 10
    search_timeout_ms: int = 15_000

    # Pipeline
    pipeline_stages: list[str] = [
        "sanitize", "route", "retrieve", "reason", "plan",
        "execute", "prompt", "generate", "sanitize_response",
        "persist", "learn", "health",
    ]

    # Observability
    log_level: str = "INFO"
    metrics_enabled: bool = True
    tracer_enabled: bool = True

    model_config = SettingsConfigDict(env_prefix="AGENT_", env_file=".env")
```

---

## 13. State Management

### 13.1 Cognitive State (SSOT)

```python
class CognitiveState(BaseModel):
    """Immutable snapshot of the entire cognitive system. Read-only after creation."""
    memory: MemoryState
    concepts: ConceptGraphState
    reasoning: ReasoningState
    feedback: FeedbackState
    policy: PolicyState
    version: int
    last_updated: datetime

    def with_memory(self, **updates) -> CognitiveState: ...  # returns new instance
    def with_concepts(self, **updates) -> CognitiveState: ...
    # ... (immutable update pattern)

class MemoryState(BaseModel):
    episodic_count: int
    episodic_active: int
    working_memory_size: int
    profile_fields: int
    profile_initialized: bool
```

### 13.2 Mutation System

```python
# All state changes go through mutations — never direct writes
StateMutation = Annotated[
    ConceptUpdateMutation
    | ConceptMergeMutation
    | ConceptDecayMutation
    | MemoryWriteMutation
    | PolicyUpdateMutation
    | ReasoningTraceMutation
    | RelationshipMarkMutation,
    Field(discriminator="type"),
]

class MutationQueue:
    """Buffer mutations within a single interaction cycle."""
    def add(self, mutation: StateMutation) -> None: ...
    async def flush(self, engine: StateMutationEngine) -> FlushResult: ...
    def new_cycle(self) -> None: ...

class StateMutationEngine:
    """Validate, clamp, and apply mutations."""
    def validate(self, mutation: StateMutation) -> ValidationResult: ...
    async def apply(self, mutation: StateMutation) -> ApplyResult: ...
    async def apply_batch(self, mutations: list[StateMutation]) -> BatchResult: ...
```

### 13.3 Immutability Rule

Once a `CognitiveState` snapshot is created, it is never mutated. New state is derived via `state.with_*(**updates)`. The MutationEngine is the only path to persistent state change.

---

## 14. Error Handling

### 14.1 Exception Hierarchy

```
AgentException (base)
├── ConfigurationError
├── PipelineError
│   ├── StageExecutionError
│   └── StageTimeoutError
├── LLMError
│   ├── LLMTimeoutError
│   ├── LLMAuthenticationError
│   └── LLMRateLimitError
├── ToolError
│   ├── ToolNotFoundError
│   ├── ToolExecutionError
│   └── ToolTimeoutError
├── SkillError
│   ├── SkillNotFoundError
│   ├── SkillPermissionError
│   └── SkillExecutionError
├── SearchError
│   ├── ProviderNotFoundError
│   ├── ProviderTimeoutError
│   └── AllProvidersFailedError
├── MemoryError
│   ├── MemoryLoadError
│   └── MemorySaveError
├── ValidationError
└── ReentrancyError
```

### 14.2 Error Handling Policy

| Layer | Policy |
|-------|--------|
| Pipeline Stage | Catch domain errors → emit ErrorOccurred event → return degraded PipelineContext |
| Execution Engine | Per-step try/catch → FallbackStrategy → partial results on non-critical failures |
| LLM Client | Timeout → retry once → degrade with user-facing error message |
| Memory | Best-effort writes; Markdown mirror failures are silent (JSON is source of truth) |
| Evolution | Any failure → skip cycle, log warning (evolution is best-effort) |
| Agent (top-level) | Always returns an AgentResponse, never raises to caller |

---

## 15. Logging & Observability

### 15.1 Structured Logging

```python
# All logs are structured (JSON). Use structlog.
logger = structlog.get_logger()

# Pipeline stage entry/exit
logger.info("stage.started", stage="retrieve", session_id=sid)
logger.info("stage.completed", stage="retrieve", duration_ms=42, results_count=3)

# LLM calls
logger.info("llm.stream_started", model=config.llm_model, message_count=5)
logger.info("llm.stream_completed", total_tokens=512, duration_ms=3200)

# Tool execution
logger.info("tool.executed", tool="web_search", success=True, latency_ms=850, result_count=5)
logger.warning("tool.failed", tool="web_search", error="timeout", fallback="duckduckgo")

# Errors
logger.error("pipeline.stage_failed", stage="generate", error=str(e), session_id=sid)
```

### 15.2 Metrics

```python
class MetricsCollector:
    """Collect and expose agent metrics."""

    # Counters
    interactions_total: Counter
    tool_executions_total: Counter        # labels: tool_name, status
    llm_calls_total: Counter              # labels: status
    errors_total: Counter                 # labels: error_type

    # Histograms
    pipeline_stage_duration_ms: Histogram # labels: stage_name
    llm_call_duration_ms: Histogram
    tool_execution_duration_ms: Histogram # labels: tool_name
    llm_tokens_per_call: Histogram

    # Gauges
    memory_episodic_count: Gauge
    memory_concept_count: Gauge
    cognitive_health_score: Gauge
    evolution_cycles_run: Gauge
```

### 15.3 Tracing

```python
class ExecutionTracer:
    """Record complete execution trace for audit/debug."""

    async def trace_interaction(
        self,
        session_id: str,
        pipeline_context: PipelineContext,
        events: list[PipelineEvent],
        duration_ms: int,
    ) -> TraceRecord: ...

    async def get_trace(self, session_id: str) -> TraceRecord | None: ...
    async def list_recent_traces(self, limit: int) -> list[TraceRecord]: ...
```

---

## 16. Testing Strategy

### 16.1 Test Pyramid

```
┌────────────────────┐
│    E2E Tests       │  10%  — Full pipeline with mock LLM
├────────────────────┤
│  Integration Tests │  30%  — Multi-module interactions
├────────────────────┤
│   Unit Tests       │  60%  — Individual services, pure functions
└────────────────────┘
```

### 16.2 Testability Design

1. **All external dependencies are behind Protocols** → mock everything
2. **Pipeline stages are independent** → test each stage in isolation
3. **Pure functions for algorithms** (scoring, decay, reasoning) → no mocking needed
4. **Event bus is injectable** → capture events in tests
5. **InMemoryEventBus** → no async I/O needed for event testing
6. **InMemoryFileStorage** → no filesystem needed for memory tests
7. **MockLLMClient** → no API key needed for pipeline tests

### 16.3 Test Fixtures

```python
# Standard test fixture for pipeline tests
@pytest.fixture
async def agent_with_mocks():
    config = AgentConfig(
        llm_api_key="test",
        memory_base_path=":memory:",  # in-memory storage
    )
    llm = MockLLMClient(responses=["This is a test response."])
    storage = InMemoryFileStorage()
    http = MockHttpClient()
    vector = InMemoryVectorStore()
    event_bus = InMemoryEventBus()

    agent = Agent(config, llm=llm, storage=storage, http=http, vector=vector, event_bus=event_bus)
    await agent.initialize()
    yield agent
    await agent.shutdown()
```

---

## 17. Pipeline Protocol

### 17.1 Stage Interface

```python
class PipelineStage(ABC):
    """A single step in the request processing pipeline."""

    name: str                          # unique stage identifier
    priority: int                      # execution order (lower = earlier)

    @abstractmethod
    async def execute(self, context: PipelineContext) -> PipelineContext: ...

    # Lifecycle hooks (optional)
    async def on_startup(self) -> None: ...    # called once at agent init
    async def on_shutdown(self) -> None: ...   # called once at agent shutdown

class PipelineContext(BaseModel, frozen=True):
    """Immutable context carried through the pipeline. Each stage returns a new instance."""
    session_id: str
    user_input_raw: str
    user_input_sanitized: str | None = None
    router_result: RouterResult | None = None
    memory_context: MemoryContext | None = None
    execution_plan: ExecutionPlan | None = None
    execution_result: ExecutionResult | None = None
    system_prompt: str | None = None
    llm_response: str | None = None
    llm_response_clean: str | None = None
    errors: list[StageError] = Field(default_factory=list)
    events: list[PipelineEvent] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=datetime.now)
    stage_timings: dict[str, float] = Field(default_factory=dict)  # stage_name → ms

    # Immutable update helpers
    def with_sanitized(self, text: str) -> PipelineContext: ...
    def with_router_result(self, result: RouterResult) -> PipelineContext: ...
    # ... (one per field)
```

### 17.2 Pipeline

```python
class Pipeline:
    """Ordered sequence of pipeline stages."""

    def __init__(self, stages: list[PipelineStage], event_bus: EventBus): ...

    async def execute(self, context: PipelineContext) -> PipelineContext:
        """Execute all stages in priority order. On stage failure, record error and continue."""
        for stage in sorted(self.stages, key=lambda s: s.priority):
            start = time.monotonic()
            try:
                context = await stage.execute(context)
            except Exception as e:
                context = context.with_error(StageError(stage=stage.name, error=str(e)))
                await self.event_bus.emit(ErrorOccurred(stage=stage.name, error=str(e)))
            finally:
                duration = (time.monotonic() - start) * 1000
                context = context.with_stage_timing(stage.name, duration)
        return context

    def add_stage(self, stage: PipelineStage) -> None: ...
    def remove_stage(self, name: str) -> None: ...
    def reorder(self, name: str, new_priority: int) -> None: ...
```

---

## 18. Agent Public API

```python
class Agent:
    """Public API for the Agent Framework."""

    def __init__(
        self,
        config: AgentConfig,
        *,
        llm: LLMClient | None = None,
        storage: FileStorage | None = None,
        http: HttpClient | None = None,
        vector: VectorStore | None = None,
        event_bus: EventBus | None = None,
    ): ...

    # Lifecycle
    async def initialize(self) -> None: ...
    async def shutdown(self) -> None: ...

    # Core
    async def process(
        self,
        user_input: str,
        session_id: str | None = None,
        *,
        on_stream: Callable[[str], Awaitable[None]] | None = None,
    ) -> AgentResponse: ...

    # Health
    async def health_check(self) -> HealthReport: ...

    # State inspection
    async def get_state(self) -> CognitiveState: ...
    async def get_memory_stats(self) -> MemoryStats: ...
    async def get_evolution_stats(self) -> EvolutionStats: ...

    # Memory query
    async def search_episodic(self, query: str, top_k: int = 5) -> list[Episode]: ...
    async def search_wiki(self, query: str, top_k: int = 3) -> list[VectorSearchResult]: ...

    # Maintenance
    async def rebuild_vector_index(self) -> None: ...
    async def save_state(self) -> None: ...

    # Plugin
    def register_tool(self, tool: Tool) -> None: ...
    def register_skill(self, skill: Skill) -> None: ...
    def register_search_provider(self, provider: SearchProvider) -> None: ...
    def register_pipeline_stage(self, stage: PipelineStage) -> None: ...

class AgentResponse(BaseModel):
    text: str
    tool_calls: list[ToolCallRecord]
    session_id: str
    events: list[PipelineEvent]
    duration_ms: int
```

---

## 19. Future Extensibility

### 19.1 Adding a New Tool

```python
# 1. Implement the Tool protocol
class MyNewTool(Tool):
    name = "my_tool"
    description = "Does something useful"
    permissions = "safe"
    parameters = {...}  # JSON Schema

    async def execute(self, args, context):
        # implementation
        return ToolResult(success=True, data=...)

# 2. Register — zero changes to agent core
agent.register_tool(MyNewTool())
```

### 19.2 Adding a New Search Provider

```python
class MySearchProvider(SearchProvider):
    name = "my_search"
    domain = "web"
    platforms = ["my_platform"]

    async def search(self, query, num_results):
        # implementation
        return SearchResult(...)

agent.register_search_provider(MySearchProvider())
```

### 19.3 Adding a New Pipeline Stage

```python
class MyCustomStage(PipelineStage):
    name = "my_stage"
    priority = 99  # runs after all default stages

    async def execute(self, context):
        # modify context
        return context.with_*(...)

agent.register_pipeline_stage(MyCustomStage())
```

### 19.4 MCP Integration (Future)

```
External MCP Server
  → MCPClient (implements Tool protocol as proxy)
  → ToolRegistry.register(mcp_tool)
  → Agent can use MCP tools transparently
```

### 19.5 Multi-Agent (Future)

```
Agent → Planner → ExecutionPlan with "handoff" steps
  → HandoffStep {target_agent: str, task: str, context: dict}
  → ExecutionEngine. execute_handoff()
  → Sub-agent processes and returns result
```

---

## 20. Dependency Summary

### Allowed Imports

| From | May Import |
|------|-----------|
| `models/` | `pydantic`, `datetime`, `enum`, `typing` |
| `ports/` | `models/`, `abc`, `typing` |
| `infrastructure/` | `ports/`, `models/`, external libs (`httpx`, `openai`, ...) |
| `memory/`, `concepts/`, `reasoning/`, `evolution/`, `policy/`, `routing/`, `retrieval/` | `models/`, `ports/` (Protocols only, not implementations) |
| `tools/`, `skills/`, `search/` | `models/`, `ports/` |
| `planner/`, `execution/` | `models/`, `tools/protocol.py`, `skills/protocol.py`, `search/protocol.py` |
| `pipeline/` | `models/`, `ports/event_bus.py` |
| `bus/` | `models/events.py` |
| `agent.py` | Everything (composition root) |

### Forbidden Imports

| From | Must NOT Import |
|------|-----------------|
| Any domain service | `tools/`, `skills/`, `search/`, `planner/`, `execution/`, `pipeline/` |
| Any domain service | `infrastructure/` (use `ports/` Protocols instead) |
| `ports/` | `infrastructure/` (Protocols define the contract, not the implementation) |
| `models/` | Anything outside `models/` (models are pure data) |
| `tools/`, `skills/`, `search/` | `agent.py` (capabilities are independent of the agent) |

---

*This specification is the definitive architecture reference for the Python Agent implementation. All implementation decisions should be traceable to principles defined herein.*
