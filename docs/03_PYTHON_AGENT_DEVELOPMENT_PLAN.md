# Python Agent Development Plan

> **Reference Architecture:** `PYTHON_AGENT_ARCHITECTURE.md`
> **Behavioral Specification:** `PYTHON_RECONSTRUCTION_SPEC.md`
> **Principle:** Every stage delivers a runnable, testable project.

---

## Project Milestones

| Milestone | After Stage | Deliverable |
|-----------|-------------|-------------|
| M0: Skeleton | Stage 0 | Empty project with linting, CI, test harness |
| M1: Foundation | Stage 1 | All Pydantic models, config, exceptions, port protocols |
| M2: Cognitive Core | Stage 3 | Memory + Reasoning fully functional, testable with mock LLM |
| M3: Capability System | Stage 6 | Tools, Skills, Search, Planner, Execution Engine all wired |
| M4: Complete Agent | Stage 9 | Full pipeline, public API, observability, end-to-end tested |
| M5: Extensible | Stage 10 | Plugin SDK, docs, examples, third-party tool support |

---

## Branch Strategy

```
main              ← Production-ready, tagged releases
  └── develop     ← Integration branch
       ├── stage/0-project-init
       ├── stage/1-core
       ├── stage/2-memory
       ├── stage/3-reasoning
       ├── stage/4-planner
       ├── stage/5-execution
       ├── stage/6-search
       ├── stage/7-providers
       ├── stage/8-evolution
       ├── stage/9-api
       └── stage/10-plugin-sdk
```

Each stage branch merges into `develop` after review. `main` is tagged at each milestone.

---

## Recommended Git Commits (per stage)

Each stage should be committed as a single squashed commit on `develop`:

```
M0: "feat: project initialization with build system and CI"
M1: "feat(core): models, config, ports, and exceptions"
M2: "feat(memory): working, episodic, profile, tool memory, and concept extraction"
M3: "feat(reasoning): concept graph builder and 3-strategy reasoner"
M4: "feat(planner): intent parser and execution planner"
M5: "feat(execution): execution engine with fallback and verification"
M6: "feat(search): search framework with provider protocol and manager"
M7: "feat(providers): LLM, storage, HTTP, and vector store implementations"
M8: "feat(evolution): memory evolution, concept evolver, feedback, drift control"
M9: "feat(api): agent class, pipeline, event bus, observability"
M10: "feat(plugins): plugin SDK, auto-discovery, documentation"
```

---

## Complexity Estimates

| Stage | Complexity | Est. Files | Est. Hours | Risk Level |
|-------|-----------|------------|------------|------------|
| 0: Init | Low | 5 | 2 | Low |
| 1: Core | Low | 15 | 8 | Low |
| 2: Memory | Medium | 10 | 16 | Medium |
| 3: Reasoning | Medium | 6 | 12 | Low |
| 4: Planner | Medium | 5 | 10 | Medium |
| 5: Execution | High | 6 | 16 | Medium |
| 6: Search | Medium | 10 | 12 | Low |
| 7: Providers | Medium | 8 | 10 | Low |
| 8: Evolution | High | 8 | 16 | Medium |
| 9: API | High | 14 | 20 | High |
| 10: Plugin SDK | Medium | 6 | 8 | Low |
| **Total** | | **93** | **130** | |

---

## Stage 0: Project Initialization

### Goal
Empty Python project with build system, linting, type checking, test harness, and CI.

### Files Created
```
pyproject.toml                    # Project metadata, dependencies, build config
.python-version                   # 3.12
.gitignore
.pre-commit-config.yaml           # ruff, mypy, pytest
.github/workflows/ci.yml          # Lint + type check + test on push
agent/
  __init__.py                     # Version: "0.1.0-dev"
  py.typed                        # PEP 561 marker
tests/
  __init__.py
  conftest.py                     # Shared fixtures placeholder
```

### Dependencies (pyproject.toml)
```toml
[project]
name = "agent-framework"
version = "0.1.0"
requires-python = ">=3.12"

[project.dependencies]
pydantic = ">=2.0"
pydantic-settings = ">=2.0"
httpx = ">=0.27"
structlog = ">=24.0"

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "pytest-cov>=5.0",
    "ruff>=0.5",
    "mypy>=1.11",
    "pre-commit>=3.0",
]
```

### Acceptance Criteria
- [ ] `pip install -e ".[dev]"` succeeds
- [ ] `ruff check .` passes (no files yet = auto-pass)
- [ ] `mypy agent/` passes
- [ ] `pytest` runs and reports 0 tests collected (no failures)
- [ ] `python -c "import agent; print(agent.__version__)"` prints "0.1.0-dev"
- [ ] CI workflow runs and passes on push

### Testing
No code yet. Verify build tooling only.

### Risks
None.

### Rollback
Delete the repository and re-clone.

---

## Stage 1: Core

### Goal
All Pydantic data models, configuration system, exception hierarchy, and port protocols. Zero business logic. Pure data and contracts.

### Files Created
```
agent/
  config.py                       # AgentConfig (Pydantic BaseSettings)
  exceptions.py                   # AgentException hierarchy (14 classes)
  models/
    __init__.py                   # Re-export all models
    state.py                      # CognitiveState, MemoryState, ConceptGraphState, ReasoningState, FeedbackState, PolicyState
    memory.py                     # Episode, WorkingMemoryEntry, UserProfileData, ToolUsageRecord, MemoryWriteDecision
    concepts.py                   # Concept, ExtractedConcept, ConceptGraphNode, ConceptGraphEdge, ConceptGraph, ConceptSubgraph
    tools.py                      # ToolDefinition, ToolResult, ToolCallRecord, ToolInfo
    skills.py                     # SkillDefinition, SkillResult, SkillExecutionRecord, SkillInfo
    routing.py                    # RouterResult, RoutingRecord, ToolMetrics
    reasoning.py                  # ReasoningResult, ReasoningTrace
    evolution.py                  # ScoredMemory, EvolutionSignal, ConsolidationResult, EvolutionResult, MergeCandidate, SplitCandidate, DecayResult
    policy.py                     # CognitivePolicy, CompressionSignal, DriftMetrics
    mutations.py                  # StateMutation (Annotated Union, 7 variants), MutationPriority
    retrieval.py                  # VectorSearchResult, RetrievalRecord, DocumentWeight, QueryCluster
    search.py                     # SearchResult, SearchQuery, SearchProviderInfo, MergedSearchResult
    events.py                     # PipelineEvent (Annotated Union, 18 variants)
  ports/
    __init__.py
    llm.py                        # LLMClient Protocol
    storage.py                    # FileStorage Protocol
    http_client.py                # HttpClient Protocol
    vector_store.py               # VectorStore Protocol
    event_bus.py                  # EventBus Protocol
    logger.py                     # Logger Protocol
```

### Key Interfaces
```python
# All models are frozen Pydantic BaseModels
class Episode(BaseModel, frozen=True):
    id: str
    timestamp: datetime
    type: Literal["event", "goal", "decision", "milestone", "question"]
    summary: str
    detail: str
    importance: float = Field(ge=0, le=1)
    tags: list[str] = Field(default_factory=list)
    related_files: list[str] = Field(default_factory=list)
    importance_score: float = Field(default=0.5, ge=0, le=1)
    usage_frequency: int = 0
    last_access_time: datetime = Field(default_factory=datetime.now)
    decay_score: float = Field(default=1.0, ge=0, le=1)
    usefulness_score: float = Field(default=0.5, ge=0, le=1)
    marked_for_removal: bool = False

class CognitiveState(BaseModel, frozen=True):
    memory: MemoryState
    concepts: ConceptGraphState
    reasoning: ReasoningState
    feedback: FeedbackState
    policy: PolicyState
    version: int
    last_updated: datetime
```

### Dependencies
- `pydantic` (models)
- `pydantic-settings` (config)
- `typing`, `abc` (protocols)
- `datetime`, `enum` (stdlib)

### Acceptance Criteria
- [ ] All 13 model files exist with Pydantic models, all frozen
- [ ] All 6 port protocols exist as abstract classes (ABC)
- [ ] `AgentConfig` loads from environment variables with `AGENT_` prefix
- [ ] All 14 exception classes exist with proper hierarchy
- [ ] `StateMutation` discriminated union works (7 types, field discriminator)
- [ ] `PipelineEvent` discriminated union works (18 types)
- [ ] `CognitiveState` can be instantiated with all sub-states
- [ ] Unit test: every model can be constructed and serialized/deserialized
- [ ] Unit test: every model validates field constraints (ge/le/max_length/etc)
- [ ] Unit test: mutation discriminated union parses correctly from JSON
- [ ] `mypy` passes with strict mode on `agent/models/`
- [ ] `ruff check` passes

### Testing Strategy
- 1 test file per model module
- Test valid construction
- Test invalid construction (field constraints)
- Test JSON round-trip (model_dump_json → model_validate_json)
- Test discriminated union parsing

### Risks
- **Low.** Pure data models, no business logic.

### Rollback
Files are isolated in `models/` and `ports/`. Remove and restart.

---

## Stage 2: Memory

### Goal
All memory services: WorkingMemory, EpisodicMemory, UserProfile, ToolMemory, MemoryStore (persistence), MemoryWriter (post-interaction coordinator).

### Files Created
```
agent/
  memory/
    __init__.py
    working.py                    # WorkingMemory
    episodic.py                   # EpisodicMemory
    profile.py                    # UserProfile
    tool_stats.py                 # ToolMemory
    store.py                      # MemoryStore (YAML frontmatter I/O via FileStorage port)
    writer.py                     # MemoryWriter (classify, commit, maintain)
  concepts/
    __init__.py
    extractor.py                  # ConceptExtractor
tests/
  memory/
    test_working.py
    test_episodic.py
    test_profile.py
    test_tool_stats.py
    test_store.py                 # Requires InMemoryFileStorage
    test_writer.py                # Requires all memory stores + mock store
  concepts/
    test_extractor.py
```

### Key Interfaces
```python
class WorkingMemory:
    def __init__(self, capacity: int = 20): ...
    def push(self, entry: WorkingMemoryEntry) -> None: ...
    def get_last(self, n: int) -> list[WorkingMemoryEntry]: ...
    def get_recent_context(self, max_tokens: int = 4000) -> str: ...
    def clear(self) -> None: ...
    @property
    def count(self) -> int: ...

class EpisodicMemory:
    def __init__(self, max_entries: int = 200): ...
    def add(self, entry: EpisodeData) -> Episode: ...
    def update(self, id: str, updates: dict) -> bool: ...
    def mark_accessed(self, id: str) -> bool: ...
    def reinforce(self, id: str, amount: float) -> bool: ...
    def apply_decay(self) -> int: ...
    def get_candidates_for_removal(self) -> list[Episode]: ...
    def get_active_entries(self) -> list[Episode]: ...
    def search(self, query: str, top_k: int = 5) -> list[Episode]: ...
    def format_for_context(self, max_entries: int = 5) -> str: ...
    def serialize(self) -> str: ...
    def deserialize(self, json: str) -> None: ...

class MemoryStore:
    def __init__(self, storage: FileStorage, base_path: str): ...
    async def load_episodes(self) -> list[Episode]: ...
    async def write_episode(self, episode: Episode) -> None: ...
    async def sync_episodes(self, episodes: list[Episode]) -> None: ...
    async def load_concepts(self) -> list[Concept]: ...
    async def upsert_concept(self, concept: Concept) -> None: ...
    async def update_concept_weight(self, slug: str, delta: float) -> None: ...
    async def mark_concept_relationship(self, a: str, b: str, weight: float) -> None: ...
    async def load_profile(self) -> UserProfileData | None: ...
    async def save_profile(self, profile: UserProfileData) -> None: ...
    async def load_policy(self) -> CognitivePolicy | None: ...
    async def save_tool_decision(self, record: ToolDecisionRecord) -> None: ...
    async def save_reasoning_trace(self, trace: ReasoningTrace) -> None: ...

class MemoryWriter:
    def __init__(self, episodic: EpisodicMemory, profile: UserProfile, tool_memory: ToolMemory,
                 store: MemoryStore, mutation_queue: MutationQueue | None = None): ...
    def analyze(self, interaction: Interaction) -> list[MemoryWriteDecision]: ...
    async def commit(self, decisions: list[MemoryWriteDecision], interaction: Interaction) -> None: ...
    def run_maintenance(self) -> None: ...

class ConceptExtractor:
    def __init__(self, custom_stop_words: list[str] | None = None): ...
    def extract(self, content: str, existing_concepts: list[str] = []) -> list[ExtractedConcept]: ...
```

### Dependencies
- `models/` (Episode, WorkingMemoryEntry, UserProfileData, ToolUsageRecord, ExtractedConcept, Concept, ...)
- `ports/storage.py` (FileStorage Protocol — injected, not imported directly)
- `ports/vector_store.py` (VectorStore Protocol — for future use)
- `core/` (MutationQueue) — **Not yet built!** Use `| None` with graceful degradation

### Key Algorithms Implemented
1. Episodic search: keyword + tag + type matching with recency + usefulness scoring
2. Episodic decay: `decayScore = importance × exp(-0.03 × (1 - usageFreq × 0.6) × cycles)`
3. Episodic prune: marked entries first, then lowest composite score
4. MemoryWriter.analyze(): profile regex, episodic keyword detection, semantic fact detection
5. MemoryWriter.commit(): consolidation check (Jaccard > 0.85 → merge)
6. ConceptExtractor: headings (+0.35), bigrams (×0.3), trigrams (×0.5), English terms (×0.4)
7. ConceptExtractor: match existing (+0.2), rank, dedup (Jaccard ≥0.6), cap 6

### Acceptance Criteria
- [ ] WorkingMemory: push 25 entries, verify only last 20 retained
- [ ] EpisodicMemory: add 250 entries, verify 200 retained with correct pruning
- [ ] EpisodicMemory: search returns scored results with recency + usefulness bonus
- [ ] EpisodicMemory: apply_decay marks entries below 0.25 threshold
- [ ] EpisodicMemory: serialize/deserialize round-trip preserves all fields
- [ ] UserProfile: set/get with confidence tracking
- [ ] UserProfile: addToArray/removeFromArray with dedup
- [ ] ToolMemory: recordCall updates rolling averages correctly
- [ ] ToolMemory: suggestAlternate returns better tool for similar patterns
- [ ] MemoryStore: load/save episodes via InMemoryFileStorage
- [ ] MemoryStore: YAML frontmatter generation is valid
- [ ] MemoryWriter: analyze produces correct decision types for sample interactions
- [ ] MemoryWriter: commit skips duplicates (consolidation check)
- [ ] ConceptExtractor: extracts concepts from Chinese + English markdown content
- [ ] ConceptExtractor: deduplicates similar concepts
- [ ] ConceptExtractor: respects max 6 concepts limit

### Testing Strategy
- All tests use `InMemoryFileStorage` — no filesystem needed
- All tests use `MutationQueue | None` — mutation queue is optional
- Test data: inline strings, no fixture files
- Each service tested in isolation
- MemoryWriter integration test: wire all stores, feed sample interaction, verify output

### Risks
- **Medium.** MemoryWriter has 5 dependencies. If MutationQueue isn't ready, use None gracefully.
- ConceptExtractor Chinese tokenization must handle edge cases (pure punctuation, empty content).
- YAML frontmatter serialization must handle special characters in strings.

### Rollback
All files are in `memory/` and `concepts/`. Models and ports are in Stage 1 and unaffected.

---

## Stage 3: Reasoning

### Goal
ConceptGraphBuilder, ConceptReasoner (3 strategies), FeedbackProcessor. Pure computation layer — no I/O beyond reading from MemoryStore.

### Files Created
```
agent/
  reasoning/
    __init__.py
    graph.py                      # ConceptGraphBuilder
    reasoner.py                   # ConceptReasoner (3 strategies)
    feedback.py                   # FeedbackProcessor
tests/
  reasoning/
    test_graph.py
    test_reasoner.py
    test_feedback.py
```

### Key Interfaces
```python
class ConceptGraphBuilder:
    def build_full(self, concepts: list[ConceptData], episode_slugs: list[str] = []) -> ConceptGraph: ...
    def build_subgraph(self, full_graph: ConceptGraph, seed_slugs: list[str]) -> ConceptSubgraph: ...

class ConceptReasoner:
    def reason(self, query: str, subgraph: ConceptSubgraph, full_graph: ConceptGraph) -> ReasoningResult: ...

class FeedbackProcessor:
    def __init__(self, store: MemoryStore, drift_controller: DriftController | None = None,
                 mutation_queue: MutationQueue | None = None): ...
    async def process(self, reasoning: ReasoningResult, query: str) -> None: ...
    async def load_policy(self) -> None: ...
    def get_usage_stats(self) -> dict[str, int]: ...
    def get_stats(self) -> FeedbackStats: ...
    @property
    def controller(self) -> DriftController: ...
```

### Key Algorithms
1. Graph construction: 3 edge types (related 0.8 / shared-episode 0.3+ / tag-overlap 0.3+)
2. Subgraph: 1-hop expansion from seeds, collect edges, identify central nodes
3. Strategy 1 (Graph Traversal): degree centrality → key concepts, between-cluster edges → bridging concepts
4. Strategy 2 (Pattern Matching): query term co-occurrence with concept names/tags
5. Strategy 3 (Abstraction): cluster detection, theme inference, contradiction detection
6. Merge results: union of all findings, weighted confidence (0.4 × traversal + 0.3 × pattern + 0.3 × abstraction)

### Dependencies
- `models/` (ConceptGraph, ConceptSubgraph, ReasoningResult, ReasoningTrace, FeedbackStats)
- `memory/store.py` (MemoryStore — for FeedbackProcessor to persist traces)
- `policy/controller.py` (DriftController) — **Not yet built!** Create with default, override later

### Acceptance Criteria
- [ ] GraphBuilder.build_full() creates correct edges from concept relationships
- [ ] GraphBuilder.build_subgraph() returns 1-hop neighbors + all edges among them
- [ ] GraphBuilder: degree computed correctly for all nodes
- [ ] Reasoner: with 10+ concepts and 5+ edges, produces non-empty ReasoningResult
- [ ] Reasoner: with 1 concept and 0 edges, returns low-confidence empty result (no crash)
- [ ] Reasoner: key concepts from traversal include highest-degree nodes
- [ ] Reasoner: bridging concepts correctly identify between-cluster nodes
- [ ] Reasoner: confidence is within [0, 1] range
- [ ] FeedbackProcessor: process() stores a reasoning trace (async)
- [ ] FeedbackProcessor: concept usage counts are tracked across calls
- [ ] FeedbackProcessor: strategy outcomes are tracked
- [ ] FeedbackProcessor: creates DriftController with default policy if none provided
- [ ] All unit tests pass with constructed concept data (no filesystem needed)

### Testing Strategy
- Construct synthetic concept graphs (5-15 nodes, known edges)
- Verify build_subgraph returns expected 1-hop expansion
- Verify reasoner identifies expected central/bridging concepts
- Verify reasoner handles edge cases (0 concepts, 1 concept, disconnected graph)
- FeedbackProcessor uses mock MemoryStore

### Risks
- **Low.** Pure computation, no I/O. Well-defined algorithms.

### Rollback
Files are in `reasoning/`. Memory and concepts are unaffected.

---

## Stage 4: Planner

### Goal
IntentParser, ExecutionPlanner, Planner. Transform user query + memory context into structured ExecutionPlan.

### Files Created
```
agent/
  planner/
    __init__.py
    intent.py                     # IntentParser (Intent + Domain + Platform)
    plan.py                       # ExecutionPlan, PlanStep data models
    planner.py                    # Planner (orchestrate intent → plan)
tests/
  planner/
    test_intent.py
    test_planner.py
```

### Key Interfaces
```python
class IntentParser:
    """Parse user query into structured Intent without LLM."""
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
    def __init__(self, intent_parser: IntentParser, execution_planner: ExecutionPlanner): ...
    async def plan(self, query: str, context: MemoryContext) -> ExecutionPlan: ...
```

### Key Algorithms
1. Intent parsing: keyword + pattern matching for action (search/read/write/analyze/chat), domain (code/video/paper/local/knowledge/general), platform (bilibili/github/arxiv/obsidian/local/web)
2. Plan building: intent → matching capabilities → ordered steps with dependency resolution
3. Parallel group assignment: independent steps (different data sources) → same group

### Dependencies
- `models/` (Intent, ExecutionPlan, PlanStep, ToolInfo, SkillInfo, SearchProviderInfo, MemoryContext)
- No external dependencies — pure logic

### Acceptance Criteria
- [ ] IntentParser: "搜索B站编译原理" → {action: "search", domain: "video", platform: "bilibili"}
- [ ] IntentParser: "帮我写个函数" → {action: "write", domain: "code", platform: "none"}
- [ ] IntentParser: "你好" → {action: "chat", domain: "general", platform: "none"}
- [ ] IntentParser: "读一下笔记" → {action: "read", domain: "knowledge", platform: "obsidian"}
- [ ] IntentParser: bare minimum confidence for unclear queries
- [ ] ExecutionPlanner: with available tools, generates plan with correct steps
- [ ] ExecutionPlanner: steps with no data dependency → same parallel_group
- [ ] ExecutionPlanner: steps with dependency → sequential, correct depends_on
- [ ] Planner.plan() returns valid ExecutionPlan with plan_id
- [ ] All tests pass with mock capability info lists

### Testing Strategy
- Table-driven tests: query → expected Intent
- Mock capability lists for ExecutionPlanner tests
- Test edge cases: empty query, pure punctuation, non-Chinese queries

### Risks
- **Medium.** Intent classification accuracy depends on keyword coverage. Initial version uses keyword patterns (same as TypeScript router), can be upgraded to LLM-based later.
- IntentParser is a NEW module — no TypeScript equivalent. Design is forward-looking.

### Rollback
Planner is isolated. If it fails, pipeline can fall back to direct ToolDecisionPolicy (Stage 9 wiring).

---

## Stage 5: Execution Engine

### Goal
ExecutionEngine, FallbackStrategy, ResultVerifier. Execute ExecutionPlan steps (sequential/parallel), handle failures, verify results.

### Files Created
```
agent/
  execution/
    __init__.py
    engine.py                     # ExecutionEngine
    fallback.py                   # FallbackStrategy
    verifier.py                   # ResultVerifier
tests/
  execution/
    test_engine.py
    test_fallback.py
    test_verifier.py
```

### Key Interfaces
```python
class ExecutionEngine:
    def __init__(
        self,
        tool_registry: ToolRegistry | None = None,
        skill_registry: SkillRegistry | None = None,
        search_manager: SearchManager | None = None,
        fallback: FallbackStrategy | None = None,
        verifier: ResultVerifier | None = None,
        event_bus: EventBus | None = None,
    ): ...
    async def execute(self, plan: ExecutionPlan) -> ExecutionResult: ...

class FallbackStrategy:
    async def on_failure(
        self, step: PlanStep, error: Exception, attempt: int,
        available_alternatives: list[str],
    ) -> FallbackAction: ...

class ResultVerifier:
    async def verify(self, result: CapabilityResult) -> VerificationResult: ...
```

### Key Algorithms
1. Plan execution: topological sort → parallel groups → per-step execute with timeout
2. Fallback: retry with backoff → switch provider → partial results → abort
3. Verification: check result structure, data completeness, error flags

### Dependencies
- `models/` (ExecutionPlan, PlanStep, ExecutionResult, ToolResult, SkillResult, SearchResult)
- `tools/protocol.py` (Tool) — **Not yet built!** Accept None for ToolRegistry
- `skills/protocol.py` (Skill) — **Not yet built!** Accept None
- `search/protocol.py` (SearchProvider) — **Not yet built!** Accept None
- `ports/event_bus.py` (EventBus) — **Not yet built!** Accept None

### Acceptance Criteria
- [ ] ExecutionEngine: executes sequential plan with 2 steps in order
- [ ] ExecutionEngine: executes parallel plan with 2 steps concurrently
- [ ] ExecutionEngine: handles step failure with retry (FallbackStrategy)
- [ ] ExecutionEngine: handles all steps failing gracefully
- [ ] ExecutionEngine: timeout per step works (cancels after timeout_ms)
- [ ] ExecutionEngine: emits ToolExecuted event per step
- [ ] ExecutionEngine: works with all registries as None (no-op for missing tools)
- [ ] FallbackStrategy: returns RETRY on first attempt, SWITCH_PROVIDER on second
- [ ] FallbackStrategy: returns ABORT after max_retries
- [ ] ResultVerifier: accepts valid result structure
- [ ] ResultVerifier: rejects malformed result

### Testing Strategy
- Mock Tool that succeeds/fails/sleeps on demand
- Mock Skill that returns specific data
- InMemoryEventBus for event capture
- Test all fallback paths (retry → switch → abort)
- Test concurrent execution correctness (no race conditions)
- Test empty plan (0 steps)

### Risks
- **Medium.** Concurrent execution (asyncio.gather) must handle exceptions correctly. return_exceptions=True in gather.

### Rollback
Execution engine is isolated. Pipeline can call tools directly with simple sequential execution if this fails.

---

## Stage 6: Search Framework

### Goal
SearchProvider protocol, SearchManager (parallel search, merge, rank, dedup). Built-in providers: Bing, DuckDuckGo.

### Files Created
```
agent/
  search/
    __init__.py
    protocol.py                   # SearchProvider Protocol
    manager.py                    # SearchManager
    providers/
      __init__.py
      bing.py                     # BingSearchProvider
      duckduckgo.py               # DuckDuckGoSearchProvider
tests/
  search/
    test_manager.py
    test_providers/
      test_bing.py
      test_duckduckgo.py
```

### Key Interfaces
```python
class SearchProvider(ABC):
    name: str
    domain: str
    platforms: list[str]
    fallback_providers: list[str]

    @abstractmethod
    async def search(self, query: str, num_results: int) -> SearchResult: ...

class SearchManager:
    def register_provider(self, provider: SearchProvider) -> None: ...
    async def search(
        self,
        query: str,
        providers: list[str] | None = None,
        strategy: SearchStrategy = SearchStrategy.PARALLEL,
    ) -> MergedSearchResult: ...
    def rank(self, results: list[SearchResult], query: str) -> list[SearchResult]: ...
    def deduplicate(self, results: list[SearchResult]) -> list[SearchResult]: ...
```

### Key Algorithms
1. Parallel search: fire all providers concurrently, collect results
2. Merge: union of all provider results with provider metadata
3. Rank: TF-IDF based relevance scoring against original query
4. Dedup: URL-based deduplication (normalize URLs, remove duplicates)
5. Fallback: if primary provider fails, try fallback_providers list

### Dependencies
- `models/search.py` (SearchResult, SearchQuery, MergedSearchResult)
- `ports/http_client.py` (HttpClient Protocol) — for web-based providers

### Acceptance Criteria
- [ ] SearchManager: registers 2 providers
- [ ] SearchManager.search() with 2 providers returns merged results
- [ ] SearchManager.search() with specific provider list only queries those
- [ ] SearchManager.rank() sorts by relevance (query match in title/snippet)
- [ ] SearchManager.deduplicate() removes duplicate URLs
- [ ] BingSearchProvider: returns parsed results (mock HTTP responses)
- [ ] DuckDuckGoSearchProvider: returns parsed results (mock HTTP responses)
- [ ] SearchManager: first provider fails → falls back to second
- [ ] SearchManager.search() with empty provider list returns empty result (no crash)

### Testing Strategy
- All provider tests use mock HttpClient (return canned HTML/JSON)
- Test provider HTML parsing with real snapshot files
- Test manager merge/dedup/rank with known result sets
- Test fallback chain: primary fails → secondary succeeds

### Risks
- **Low.** Providers are isolated behind protocol. HTML parsing is fragile but testable.

### Rollback
Search framework is standalone. No other module depends on it.

---

## Stage 7: Providers

### Goal
Concrete implementations of all port protocols: DeepSeek LLM client, local file system adapter, HTTPX HTTP client, TF-IDF vector store, in-memory event bus, structlog logger.

### Files Created
```
agent/
  infrastructure/
    __init__.py
    llm/
      __init__.py
      deepseek.py                 # DeepSeekLLMClient
      mock.py                     # MockLLMClient (for testing)
    storage/
      __init__.py
      local_fs.py                 # LocalFileStorage
      memory_fs.py                # InMemoryFileStorage (for testing)
    http/
      __init__.py
      httpx_client.py             # HttpxHttpClient
    vector/
      __init__.py
      tfidf_store.py              # TfidfVectorStore
    bus/
      __init__.py
      memory_bus.py               # InMemoryEventBus
    logging/
      __init__.py
      structlog_adapter.py        # StructlogLogger
tests/
  infrastructure/
    test_llm/
      test_deepseek.py
    test_storage/
      test_local_fs.py
      test_memory_fs.py
    test_vector/
      test_tfidf.py
    test_bus/
      test_memory_bus.py
```

### Key Interfaces
```python
class DeepSeekLLMClient:
    """Implements LLMClient protocol. OpenAI-compatible API."""
    def __init__(self, endpoint: str, api_key: str, model: str, timeout_ms: int = 60_000): ...
    async def stream(self, messages: list, on_chunk: Callable, **kwargs) -> str: ...
    async def complete(self, messages: list, **kwargs) -> LLMResponse: ...

class TfidfVectorStore:
    """Implements VectorStore protocol. Offline TF-IDF + cosine similarity."""
    def build(self, documents: list[Document]) -> None: ...
    def search(self, query: str, top_k: int) -> list[VectorSearchResult]: ...
    def apply_feedback(self, doc_path: str, delta: float) -> None: ...
    def serialize(self) -> str: ...
    def deserialize(self, data: str) -> None: ...

class InMemoryEventBus:
    """Implements EventBus protocol."""
    async def emit(self, event: PipelineEvent) -> None: ...
    def subscribe(self, event_type: type, handler: Callable) -> None: ...
    def unsubscribe(self, event_type: type, handler: Callable) -> None: ...
```

### Key Algorithms
1. TF-IDF: tokenize → compute TF → compute IDF → build sparse vectors → cosine similarity
2. SSE parsing: read stream → split by "\n\n" → extract "data: " lines → parse JSON delta → accumulate content
3. LLM timeout: AbortController pattern via asyncio.wait_for()
4. Event bus: emit calls all subscribers concurrently via asyncio.gather()

### Dependencies
- `ports/` (all protocols)
- `models/` (LLMResponse, VectorSearchResult, Document, PipelineEvent)
- `httpx` (HTTP client)
- `structlog` (logging)
- No domain service dependencies

### Acceptance Criteria
- [ ] DeepSeekLLMClient.stream() yields incremental chunks (test with mock server)
- [ ] DeepSeekLLMClient.complete() returns full response within timeout
- [ ] DeepSeekLLMClient timeout raises LLMTimeoutError after configured ms
- [ ] LocalFileStorage: read/write/exists/list_dir/delete/mkdir all work on real fs
- [ ] InMemoryFileStorage: all operations work without real fs
- [ ] HttpxHttpClient: GET/POST work with real HTTP (test against httpbin or mock)
- [ ] TfidfVectorStore.build() from 10 documents, search() returns relevant results
- [ ] TfidfVectorStore serialization round-trip preserves vocabulary + IDF + documents
- [ ] TfidfVectorStore.apply_feedback() adjusts scores correctly
- [ ] InMemoryEventBus: emit → subscriber receives event
- [ ] InMemoryEventBus: multiple subscribers all receive event
- [ ] InMemoryEventBus: unsubscribe removes handler
- [ ] InMemoryEventBus: subscriber exception doesn't crash other subscribers
- [ ] StructlogLogger: structured log output is valid JSON

### Testing Strategy
- Mock HTTP server (httpx test helpers or aiohttp test server) for LLM tests
- InMemoryFileStorage is already tested in Stage 2
- Vector store: synthetic documents, verify cosine similarity rankings
- Event bus: subscribe, emit, verify handler called

### Risks
- **Medium.** TF-IDF for Chinese needs proper tokenization (CJK bigram extraction). Verify against reference output from TypeScript version.

### Rollback
Infrastructure implementations are swappable. If DeepSeek client fails, swap to MockLLMClient for development. Protocol guarantees interface compatibility.

---

## Stage 8: Evolution

### Goal
Memory evolution (decay, reinforcement, consolidation), ConceptEvolver (merge, split, decay), DriftController (policy, balance, compression), MutationQueue + StateMutationEngine.

### Files Created
```
agent/
  evolution/
    __init__.py
    scoring.py                    # Pure functions: compute_decay_score, reinforce, consolidate, merge_memories, apply_batch_decay
    memory_evolution.py           # MemoryEvolution: orchestrate decay + reinforcement cycle
    concept_evolver.py            # ConceptEvolver: merge, split, decay
  policy/
    __init__.py
    controller.py                 # DriftController
  core/
    __init__.py
    queue.py                      # MutationQueue
    engine.py                     # StateMutationEngine
tests/
  evolution/
    test_scoring.py
    test_memory_evolution.py
    test_concept_evolver.py
  policy/
    test_controller.py
  core/
    test_queue.py
    test_engine.py
```

### Key Interfaces
```python
# Pure functions (no class, no state)
def compute_decay_score(importance: float, usage_freq: int, cycles_since_access: int) -> float: ...
def compute_usefulness_score(access_count: int, positive_feedback: int, negative_feedback: int) -> float: ...
def reinforce(memory: ScoredMemory, signal: EvolutionSignal) -> ScoredMemory: ...
def consolidate(new_memory: ScoredMemory, existing: list[ScoredMemory]) -> ConsolidationResult: ...
def merge_memories(a: ScoredMemory, b: ScoredMemory) -> ScoredMemory: ...
def apply_batch_decay(memories: list[ScoredMemory]) -> EvolutionCycleResult: ...

class MemoryEvolution:
    def __init__(self, episodic: EpisodicMemory): ...
    def run_cycle(self) -> int: ...  # returns decayed count

class ConceptEvolver:
    def __init__(self, store: MemoryStore, mutation_queue: MutationQueue | None = None): ...
    async def evolve(self, usage_counts: dict[str, int] | None = None) -> EvolutionResult: ...
    async def apply_merges(self, candidates: list[MergeCandidate]) -> None: ...
    async def apply_split_marks(self, candidates: list[SplitCandidate]) -> None: ...

class DriftController:
    def __init__(self, policy: CognitivePolicy | None = None): ...
    def reinforce_domain(self, tag: str, amount: float = 0.03) -> None: ...
    def suppress_domain(self, tag: str, amount: float = 0.02) -> None: ...
    def adjust_strategy_weight(self, strategy: str, delta: float) -> None: ...
    def adapt_exploration_rate(self, concept_count: int) -> None: ...
    def enforce_balance(self) -> None: ...
    def detect_compression_signals(self, concepts: list[ConceptData], concept_count: int,
                                    unstable_rel_count: int = 0) -> list[CompressionSignal]: ...
    def compute_health(self, concept_confidences: list[float], concept_count: int,
                       unstable_rel_count: int) -> DriftMetrics: ...
    def serialize(self) -> str: ...

class MutationQueue:
    def add(self, mutation: StateMutation) -> None: ...
    def add_batch(self, mutations: list[StateMutation]) -> None: ...
    async def flush(self, engine: StateMutationEngine) -> FlushResult: ...
    def new_cycle(self) -> None: ...
    @property
    def size(self) -> int: ...

class StateMutationEngine:
    def __init__(self, store: MemoryStore, episodic: EpisodicMemory, profile: UserProfile): ...
    def validate(self, mutation: StateMutation) -> ValidationResult: ...
    async def apply(self, mutation: StateMutation) -> ApplyResult: ...
    async def apply_batch(self, mutations: list[StateMutation]) -> BatchResult: ...
```

### Key Algorithms
1. Decay: `effectiveRate = 0.03 × (1 - usageFreq × 0.6)`, `decayScore = importance × e^(-effectiveRate × cycles)`
2. Reinforcement: `importanceScore += clamp(amount, -0.05, +0.05)`
3. Consolidation: Jaccard similarity > 0.85 → merge (keep target, reinforce +0.02)
4. Concept merge: shared episodes ≥70% or strong edge (≥0.7)
5. Concept split: ≥2 conflicting relationship groups
6. Concept decay: ≥7 days unused → -0.05 confidence, floor 0.15
7. Mutation dedup: identical concept_updates merged (deltas summed, clamped ±0.05)
8. Policy balance: spread > 0.6 → dampen max -0.05, boost min +0.03
9. Compression signals: low-confidence ratio > threshold, redundant tag clusters ≥4, entropy > 15 concepts
10. Health: 0.3 × confidence + 0.4 × stability + 0.3 × signal penalty

### Dependencies
- `models/` (all evolution, policy, mutation models)
- `memory/episodic.py` (MemoryEvolution)
- `memory/store.py` (ConceptEvolver, StateMutationEngine)
- `memory/profile.py` (StateMutationEngine)

### Acceptance Criteria
- [ ] compute_decay_score: returns 1.0 for recently accessed, <0.25 after 14+ cycles unused
- [ ] reinforce: clamps to ±0.05 per call
- [ ] consolidate: merges when Jaccard > 0.85, skips otherwise
- [ ] MemoryEvolution.run_cycle: decays and marks entries for removal
- [ ] ConceptEvolver.evolve: detects merge candidates with ≥70% shared episodes
- [ ] ConceptEvolver.evolve: detects split candidates with conflicting relationships
- [ ] ConceptEvolver: applies decay to unused concepts
- [ ] DriftController.enforce_balance: dampens when spread > 0.6
- [ ] DriftController.adapt_exploration_rate: reduces with more concepts
- [ ] DriftController.detect_compression_signals: returns 4 signal types
- [ ] DriftController.compute_health: returns 0..1 score
- [ ] MutationQueue: deduplicates same-concept updates
- [ ] MutationQueue: sorts by priority before flush
- [ ] MutationQueue.flush: clears queue after successful application
- [ ] StateMutationEngine.validate: rejects invalid mutations
- [ ] StateMutationEngine.apply: enforces ±0.05 clamp
- [ ] StateMutationEngine.apply_batch: applies all valid, reports errors for invalid
- [ ] All mutations are idempotent (applying same mutation twice = same result)

### Testing Strategy
- Pure functions (scoring.py): unit test all edge cases
- MutationQueue: test dedup (3 concept_updates for same concept → 1 merged)
- StateMutationEngine: test all 7 mutation types with valid and invalid inputs
- DriftController: test policy normalization, balance enforcement, compression detection
- ConceptEvolver: integration test with MemoryStore containing real concept data
- MemoryEvolution: integration test with EpisodicMemory containing entries at various decay stages

### Risks
- **Medium.** MutationQueue → Engine → MemoryStore chain must handle async correctly.
- StateMutationEngine.apply_batch must be atomic: if one mutation fails, previous ones should not roll back (best-effort apply).

### Rollback
Evolution is isolated. Agent can run without evolution cycles (just skip the LearnStage in pipeline).

---

## Stage 9: API

### Goal
Full Agent class, Pipeline, all 12 PipelineStages, EventBus integration, observability (health, metrics, tracing), public API.

### Files Created
```
agent/
  agent.py                       # Agent class (public API)
  pipeline/
    __init__.py
    protocol.py                   # PipelineStage Protocol
    context.py                    # PipelineContext (frozen)
    pipeline.py                   # Pipeline (stage executor)
    stages/
      __init__.py
      sanitize.py                 # SanitizeStage
      route.py                    # RouteStage
      retrieve.py                 # RetrieveStage
      reason.py                   # ReasonStage
      plan.py                     # PlanStage
      execute.py                  # ExecuteStage
      prompt.py                   # PromptStage
      generate.py                  # GenerateStage
      sanitize_response.py        # ResponseSanitizeStage
      persist.py                  # PersistStage
      learn.py                    # LearnStage
      health.py                   # HealthStage
  observability/
    __init__.py
    health.py                     # HealthCheck service
    metrics.py                    # MetricsCollector
    tracer.py                     # ExecutionTracer
tests/
  pipeline/
    test_context.py
    test_pipeline.py
    test_stages/
      test_sanitize.py
      test_route.py
      test_retrieve.py
      test_reason.py
      test_prompt.py
      test_generate.py
      test_persist.py
  test_agent.py                   # Full agent integration test
  test_agent_e2e.py               # End-to-end with mock LLM
```

### Key Interfaces
```python
class Agent:
    def __init__(self, config: AgentConfig, *, llm: LLMClient | None = None,
                 storage: FileStorage | None = None, http: HttpClient | None = None,
                 vector: VectorStore | None = None, event_bus: EventBus | None = None): ...
    async def initialize(self) -> None: ...
    async def shutdown(self) -> None: ...
    async def process(self, user_input: str, session_id: str | None = None, *,
                      on_stream: Callable | None = None) -> AgentResponse: ...
    async def health_check(self) -> HealthReport: ...
    async def get_state(self) -> CognitiveState: ...
    async def search_episodic(self, query: str, top_k: int = 5) -> list[Episode]: ...
    async def search_wiki(self, query: str, top_k: int = 3) -> list[VectorSearchResult]: ...
    async def rebuild_vector_index(self) -> None: ...
    async def save_state(self) -> None: ...
    def register_tool(self, tool: Tool) -> None: ...
    def register_skill(self, skill: Skill) -> None: ...
    def register_search_provider(self, provider: SearchProvider) -> None: ...
    def register_pipeline_stage(self, stage: PipelineStage) -> None: ...

class PipelineStage(ABC):
    name: str
    priority: int
    @abstractmethod
    async def execute(self, context: PipelineContext) -> PipelineContext: ...

class PipelineContext(BaseModel, frozen=True):
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
    stage_timings: dict[str, float] = Field(default_factory=dict)

class Pipeline:
    def __init__(self, stages: list[PipelineStage], event_bus: EventBus): ...
    async def execute(self, context: PipelineContext) -> PipelineContext: ...
    def add_stage(self, stage: PipelineStage) -> None: ...
    def remove_stage(self, name: str) -> None: ...
```

### Key Algorithms
1. Pipeline execution: sort stages by priority → execute sequentially → catch errors → record timings
2. Sanitize: strip code blocks, JSON system-prompt injection, truncate >4000 chars
3. Route: keyword + regex scoring across 6 tool categories (from tool_router.ts algorithm)
4. Retrieve: vector search (TF-IDF) + episodic search + profile context
5. Reason: load concepts → build graph → build subgraph → reason (3 strategies)
6. Plan: parse intent → match capabilities → build execution plan
7. Execute: run plan steps via ExecutionEngine
8. Prompt: assemble system prompt (time + profile + wiki + episodic + reasoning + rules + tool results)
9. Generate: call LLM stream → SSE chunks → call onStream callback
10. Sanitize response: strip DSML/invoke/tool_calls blocks
11. Persist: MemoryWriter.analyze() + commit() + save state
12. Learn: RouterTelemetry, RagFeedback, FeedbackProcessor, evolution cycle (conditional)
13. Health: DriftController health check (every 15 interactions)

### Dependencies
- Everything from Stages 1-8 (first stage where all modules are wired together)
- This is the **composition root**

### Acceptance Criteria
- [ ] Agent.initialize() loads persisted state and builds vector index
- [ ] Agent.process("hello") returns AgentResponse with text, no tool calls
- [ ] Agent.process("what time is it") triggers tool execution (mock LLM returns decision)
- [ ] Agent.process() with on_stream receives incremental chunks
- [ ] Agent.process() concurrent calls are blocked by reentrancy guard (second call returns error)
- [ ] Agent.process() with failed LLM returns graceful error message (no exception to caller)
- [ ] Agent.health_check() returns HealthReport with status ("healthy"/"degraded"/"error")
- [ ] Agent.search_episodic() returns relevant memories
- [ ] Agent.shutdown() saves all state and closes connections
- [ ] Pipeline with all 12 stages executes in correct order
- [ ] PipelineContext is immutable — with_* methods return new instances
- [ ] Each stage returns updated PipelineContext or records error
- [ ] Pipeline handles stage failure gracefully (continues to next stage)
- [ ] SanitizeStage: strips code blocks, blocks system-prompt injection
- [ ] RouteStage: classifies query into correct tool category
- [ ] RetrieveStage: returns MemoryContext with wiki + episodic + profile
- [ ] GenerateStage: calls LLM stream, invokes onStream callback
- [ ] PersistStage: writes episode, extracts concepts, saves state
- [ ] LearnStage: records telemetry, RAG feedback, triggers evolution on interval
- [ ] MetricsCollector: records interaction count, tool execution count, LLM call count
- [ ] ExecutionTracer: records complete trace per interaction

### Testing Strategy
- **Unit tests:** Each stage tested in isolation with mock dependencies
- **Integration tests:** Pipeline with all stages, mock LLM, InMemoryFileStorage
- **E2E tests:** Agent.process() with mock LLM returning predetermined responses
- **Reentrancy test:** Two concurrent process() calls, second must be rejected
- **Error recovery test:** LLM failure → graceful error message
- **Evolution test:** Run 21 interactions, verify cycle triggered at 10 and 20

### Risks
- **High.** This is the composition root — all modules wired together for the first time.
- Pipeline stage ordering must be correct (dependencies flow forward only).
- Reentrancy guard must be tested carefully with asyncio.
- LLM streaming + event bus + onStream callback — three async paths, must not deadlock.

### Rollback
If pipeline wiring fails, individual stages can be tested and debugged in isolation. The Agent class can fall back to a simplified pipeline (only essential stages).

---

## Stage 10: Plugin SDK

### Goal
Plugin auto-discovery, plugin manifest format, plugin installation/uninstallation, documentation, examples.

### Files Created
```
agent/
  plugins/
    __init__.py
    discovery.py                  # PluginDiscovery (auto-import from package)
    manifest.py                   # PluginManifest model
    loader.py                     # PluginLoader (install/uninstall/validate)
examples/
  custom_tool/
    __init__.py
    plugin.json                   # Plugin manifest
    my_tool.py                    # Example custom Tool implementation
  custom_provider/
    __init__.py
    plugin.json
    wikipedia_provider.py         # Example custom SearchProvider
docs/
  PLUGIN_SDK.md                   # Plugin development guide
  EXAMPLES.md                     # Example plugins
tests/
  plugins/
    test_discovery.py
    test_loader.py
    test_manifest.py
```

### Key Interfaces
```python
class PluginManifest(BaseModel):
    name: str
    version: str
    description: str
    author: str
    capabilities: list[CapabilityRegistration]  # tools, skills, providers, stages

class CapabilityRegistration(BaseModel):
    type: Literal["tool", "skill", "search_provider", "pipeline_stage"]
    class_path: str                 # "my_package.my_module.MyTool"
    config: dict = Field(default_factory=dict)

class PluginDiscovery:
    """Scan a package directory for plugins (each subdir with plugin.json)."""
    def discover(self, plugins_dir: str) -> list[PluginManifest]: ...

class PluginLoader:
    """Load, validate, and install plugins into the Agent."""
    def __init__(self, agent: Agent): ...
    def validate(self, manifest: PluginManifest) -> ValidationResult: ...
    async def install(self, manifest: PluginManifest) -> None: ...
    async def uninstall(self, name: str) -> None: ...
    def list_installed(self) -> list[str]: ...
```

### Dependencies
- `agent/agent.py` (Agent — to register capabilities)
- `models/` (PluginManifest, CapabilityRegistration)

### Acceptance Criteria
- [ ] PluginDiscovery discovers a directory with 2 plugin subdirectories
- [ ] PluginDiscovery skips directories without plugin.json
- [ ] PluginManifest validates required fields (name, version, class_path)
- [ ] PluginLoader.install() registers a Tool from a plugin
- [ ] PluginLoader.uninstall() removes the registered tool
- [ ] PluginLoader.validate() rejects invalid manifest (missing fields, invalid class_path)
- [ ] Plugin auto-discovery: agent.register_tool() works with dynamically imported class
- [ ] Example custom tool plugin works end-to-end
- [ ] Example custom search provider plugin works end-to-end
- [ ] PLUGIN_SDK.md contains complete developer guide
- [ ] EXAMPLES.md contains 3+ working examples

### Testing Strategy
- Create test plugins directory with sample plugin.json files
- Test discovery, validation, installation, uninstallation
- Test that installed tools are callable via agent
- Test that uninstalled tools are removed from registry

### Risks
- **Low.** Plugin system is a thin wrapper around existing registry.register() calls. No new architecture.

### Rollback
Plugin system is additive. Removing it doesn't affect core agent functionality.

---

## Implementation Order

```
Stage 0  →  Set up project
Stage 1  →  Models, config, ports, exceptions
Stage 2  →  Memory services (depends on Stage 1)
Stage 3  →  Reasoning (depends on Stage 2 for MemoryStore)
Stage 4  →  Planner (depends on Stage 1 for models only)
Stage 5  →  Execution Engine (depends on Stage 4 for ExecutionPlan model)
Stage 6  →  Search Framework (depends on Stage 1 for models)
Stage 7  →  Providers (depends on Stage 1 for ports)
Stage 8  →  Evolution (depends on Stage 2 for memory services)
Stage 9  →  API (depends on ALL stages 1-8)
Stage 10 →  Plugin SDK (depends on Stage 9 for Agent class)
```

### Critical Path
```
Stage 0 → Stage 1 → Stage 2 → Stage 9
                         ↘ Stage 3 → Stage 9
                         ↘ Stage 8 → Stage 9
                  Stage 4 → Stage 5 → Stage 9
                  Stage 6 → Stage 9
                  Stage 7 → Stage 9
```

Stage 9 is the bottleneck — it depends on everything. Stages 2-8 can be parallelized by multiple developers.

### Recommended Developer Allocation (3 developers)

| Developer | Stages |
|-----------|--------|
| Dev A (Core) | 0, 1, 2, 8 (foundations + memory + evolution) |
| Dev B (Capability) | 4, 5, 6 (planner + execution + search) |
| Dev C (Integration) | 3, 7 (reasoning + providers) |
| All | 9, 10 (API + plugins — pair programming) |

---

## Final Notes

1. Every stage produces a runnable, testable project — `pytest` must pass with >80% coverage before moving to the next stage.

2. Stage 1-7 modules are designed to work in isolation: they depend only on Stage 1 models + ports, never on other domain services.

3. Stage 9 is the only stage where all modules are wired together. This intentional centralization in the composition root (Agent class) makes dependencies explicit and testable.

4. All external dependencies (LLM, file system, HTTP) are behind Protocols. This means Stages 2-6 can be fully tested without any real external services.

5. The TypeScript implementation has proven the algorithms work. The Python version should match the algorithmic behavior exactly, not the implementation structure.
