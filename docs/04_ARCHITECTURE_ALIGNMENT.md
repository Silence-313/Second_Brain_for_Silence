# Architecture Alignment & Reconciliation

> **Status:** Authoritative — overrides 03_PYTHON_AGENT_DEVELOPMENT_PLAN.md in case of conflict.
> **Purpose:** Resolve every inconsistency across the three design documents before implementation begins.
> **Principle:** When documents disagree, this document is the final word.

---

## 1. Inconsistency Inventory

Seven inconsistencies were identified during cross-document review. Each is classified, analyzed, and resolved below.

---

### INC-01: Routing Subsystem Has No Implementation Stage

**Current Situation**

The Architecture document (02) defines `routing/` as a Layer 2 domain service containing `router.py` (ToolRouter) and `telemetry.py` (RouterTelemetry). The Development Plan (03) never assigns these files to any stage. Stage 9 builds `pipeline/stages/route.py` and `pipeline/stages/learn.py`, which import ToolRouter and RouterTelemetry — but those imports will fail because the modules don't exist.

**Root Cause**

The Development Plan's stage list was derived from the Reconstruction Spec's migration phases (Section 17), which lists routing in Phase 5 alongside retrieval. When the Dev Plan was written, Phase 5 (Routing & Retrieval) was inadvertently omitted from the stage sequence.

**Affected Documents**

| Document | Impact |
|----------|--------|
| 03_PYTHON_AGENT_DEVELOPMENT_PLAN.md | Missing stage — routing files never created |
| 02_PYTHON_AGENT_ARCHITECTURE.md | Correctly defines routing — not at fault |

**Classification:** Development Plan omission.

**Recommended Fix**

Insert a new stage **"Routing & Retrieval"** after Reasoning (Stage 3) and before Planner (Stage 4). This stage builds both `routing/` and `retrieval/` since they share the same dependency profile (pure computation on models, no external I/O).

**Files to create:**
```
agent/routing/__init__.py
agent/routing/router.py          # ToolRouter — keyword-scoring intent classifier
agent/routing/telemetry.py       # RouterTelemetry — adaptive threshold evolution
agent/retrieval/__init__.py
agent/retrieval/feedback.py      # RagFeedback — retrieval quality feedback loop
```

**Migration Impact:** Add one stage (4 files, ~8 hours). No existing stages are modified. Stage numbering shifts for all subsequent stages.

**Priority:** CRITICAL — Pipeline stages in Stage 9 cannot function without these modules.

---

### INC-02: Retrieval Subsystem (RagFeedback) Has No Implementation Stage

**Current Situation**

Same pattern as INC-01. The Architecture defines `retrieval/feedback.py` (RagFeedback) as a Layer 2 domain service. The Development Plan builds `infrastructure/vector/tfidf_store.py` in Stage 7 (Providers), but the domain-level RagFeedback service — which manages retrieval quality feedback, query clustering, and document weight adjustment — is never built. Stage 9's LearnStage references it.

**Root Cause**

Same omission as INC-01. The Reconstruction Spec lists RagFeedback in Phase 5 alongside routing. Both were dropped from the Dev Plan stage list.

**Affected Documents**

Same as INC-01.

**Classification:** Development Plan omission.

**Recommended Fix**

Resolved jointly with INC-01. The new "Routing & Retrieval" stage includes RagFeedback.

**Migration Impact:** Covered by INC-01 fix.

**Priority:** CRITICAL — LearnStage and RetrieveStage in Stage 9 depend on RagFeedback.

---

### INC-03: Tool System Has No Implementation Stage

**Current Situation**

The Architecture (Section 9.2) defines a full Tool system under Layer 3:

```
tools/protocol.py      — Tool abstract base class (Capability)
tools/registry.py      — ToolRegistry (auto-discover + register)
tools/decision.py      — ToolDecisionPolicy (LLM-based tool selection)
tools/builtins/
  web_search.py        — WebSearchTool
  todos.py             — GetTodosTool, AddTodosTool, TodoStatsTool
  time.py              — GetCurrentTimeTool
  wiki_crud.py         — ListWikiTool, ReadWikiTool, WriteWikiTool, DeleteWikiTool, SearchWikiTool
```

This is 9 files. The Reconstruction Spec (Section 9) documents 10 hardcoded tools and explicitly calls for a redesign with a Tool interface + ToolRegistry (Section 19). The Development Plan never assigns tool system construction to any stage.

Stage 5 (Execution Engine) accepts `ToolRegistry | None` with a None default. Stage 9 pipeline stages (`execute.py`, `decide_tools.py`) need the tool system. Without it, the agent cannot execute any tools.

**Root Cause**

The Reconstruction Spec's Phase 6 (Tool System redesign) was not translated into a Development Plan stage. This is the single largest omission.

**Affected Documents**

| Document | Impact |
|----------|--------|
| 03_PYTHON_AGENT_DEVELOPMENT_PLAN.md | Missing stage — 9 files never created |
| 02_PYTHON_AGENT_ARCHITECTURE.md | Correctly defines tool system — not at fault |
| 01_PYTHON_RECONSTRUCTION_SPEC.md | Correctly identifies Tool system as "CRITICAL FLAW" to redesign — not at fault |

**Classification:** Development Plan omission.

**Recommended Fix**

Insert a new stage **"Capability System"** after Planner (renumbered Stage 5) and before Execution Engine (renumbered Stage 6). This stage builds all three capability subsystems: Tools, Skills, and Search protocols + registries. Built-in tool implementations and search providers are built here as well since they are concrete implementations of the protocols defined in the same stage.

**Files to create:**
```
agent/tools/__init__.py
agent/tools/protocol.py           # Tool abstract base class
agent/tools/registry.py           # ToolRegistry
agent/tools/decision.py           # ToolDecisionPolicy
agent/tools/builtins/__init__.py
agent/tools/builtins/web_search.py
agent/tools/builtins/todos.py
agent/tools/builtins/time.py
agent/tools/builtins/wiki_crud.py

agent/skills/__init__.py
agent/skills/protocol.py          # Skill abstract base class
agent/skills/registry.py          # SkillRegistry
agent/skills/builtins/__init__.py
agent/skills/builtins/location.py
agent/skills/builtins/file_reader.py

agent/search/__init__.py
agent/search/protocol.py          # SearchProvider abstract base class
agent/search/manager.py           # SearchManager
agent/search/providers/__init__.py
agent/search/providers/bing.py
agent/search/providers/duckduckgo.py
```

**Migration Impact:** This replaces the old Stage 6 (Search Framework). The old Stage 6 only built search — the new stage builds tools + skills + search together. The search providers (bing, duckduckgo) that were in old Stage 6 are absorbed here. The remaining search providers (bilibili, github, arxiv, local, obsidian) from the Architecture are deferred to the Plugin SDK stage as optional extensions.

26 files, ~24 hours. This is the largest single stage in the plan.

**Priority:** CRITICAL — Without tools, skills, and search, the agent cannot interact with the world.

---

### INC-04: Skill System Has No Implementation Stage

**Current Situation**

Same pattern as INC-03. The Architecture (Section 9.3) defines a Skill system with protocol, registry, and 2 built-in skills (location, file_reader). The Development Plan never assigns skill system construction to any stage.

**Root Cause**

The Reconstruction Spec's Phase 7 (Skills) was not translated into a Development Plan stage.

**Affected Documents**

Same as INC-03.

**Classification:** Development Plan omission.

**Recommended Fix**

Resolved jointly with INC-03. The new "Capability System" stage includes the Skill system.

**Migration Impact:** Covered by INC-03 fix.

**Priority:** CRITICAL.

---

### INC-05: Stage Ordering Violates Dependency Inversion

**Current Situation**

The original Development Plan order was:

```
Stage 4: Planner
Stage 5: Execution Engine   ← depends on Tool/Skill/Search protocols
Stage 6: Search Framework   ← builds Search protocol (too late)
Stage 7: Providers          ← builds infrastructure (after execution needs it)
```

Stage 5 (Execution Engine) accepts `ToolRegistry | None`, `SkillRegistry | None`, `SearchManager | None`. But those registries and their protocols don't exist yet. The `None` default is a test-time workaround, not a valid build order. In a real build, Execution Engine must be built AFTER the capability protocols it orchestrates.

Additionally, ToolDecisionPolicy needs an `LLMClient` to function. The `LLMClient` protocol is defined in Stage 1 (ports), which is correct — the dependency is on the abstraction, not the implementation. But this means the ToolDecisionPolicy can only be unit-tested with a MockLLMClient until Stage 8 (Infrastructure) provides the real DeepSeek adapter. This is acceptable and is the intended behavior of the ports & adapters pattern.

**Root Cause**

The Development Plan ordered stages by perceived complexity rather than by dependency graph. The capability interfaces (protocols + registries) must exist before the engine that orchestrates them.

**Affected Documents**

| Document | Impact |
|----------|--------|
| 03_PYTHON_AGENT_DEVELOPMENT_PLAN.md | Stages 5, 6 ordered incorrectly |

**Classification:** Development Plan ordering error.

**Recommended Fix**

Reorder stages so that capability protocols and registries are built BEFORE Execution Engine:

```
Stage 4: Routing & Retrieval   (NEW — pure domain services)
Stage 5: Planner               (was Stage 4)
Stage 6: Capability System     (NEW — tools/skills/search: protocols + registries + builtins)
Stage 7: Execution Engine      (was Stage 5 — now has all protocols available)
```

**Migration Impact:** Renumbering only. No file changes.

**Priority:** HIGH — Execution Engine tests with `None` registries would pass but real usage would fail.

---

### INC-06: `core/` Package Not in Architecture Package Layout

**Current Situation**

The Development Plan Stage 8 creates:

```
agent/core/
  __init__.py
  queue.py          # MutationQueue
  engine.py         # StateMutationEngine
```

The Architecture document's package structure (Section 3) has no `core/` directory. The Architecture moved all type definitions into `models/` (e.g., `models/mutations.py` for `StateMutation` discriminated union types), but did not specify where the runtime classes — MutationQueue and StateMutationEngine — should live.

The Reconstruction Spec (Section 18) DOES have `core/`:
```
core/
  state.py           # Pydantic models → moved to models/state.py in Architecture
  mutation.py        # StateMutation types + StateMutationEngine → types in models/, engine needs home
  queue.py           # MutationQueue → needs home
```

**Root Cause**

The Architecture's decision to extract pure data models into a `models/` package was correct, but it only moved the types and left the runtime engine classes without a designated location.

**Affected Documents**

| Document | Impact |
|----------|--------|
| 02_PYTHON_AGENT_ARCHITECTURE.md | Missing `core/` directory in package layout |
| 03_PYTHON_AGENT_DEVELOPMENT_PLAN.md | References `core/` which conflicts with Architecture |
| 01_PYTHON_RECONSTRUCTION_SPEC.md | Has `core/` — original source of truth |

**Classification:** Architecture documentation gap. The Architecture correctly separated data models from runtime logic but didn't complete the separation by providing a home for the runtime classes.

**Recommended Fix**

Keep `agent/core/` directory as defined in the Development Plan and Reconstruction Spec. Add it to the Architecture package structure. Clarify the split:

| Location | Content |
|----------|---------|
| `models/mutations.py` | `StateMutation` discriminated union type, 7 variant Pydantic models |
| `core/engine.py` | `StateMutationEngine` — validate, clamp, apply mutations |
| `core/queue.py` | `MutationQueue` — buffer, dedup, sort, flush |

The Architecture document's Layer 1 (Domain Model) correctly contains the types. The `core/` package houses the mutation runtime, which is a domain service (Layer 2), not a model — it belongs alongside `memory/`, `reasoning/`, and `evolution/`.

**Migration Impact:** Add `core/` to Architecture package layout. No code changes needed.

**Priority:** MEDIUM — The Dev Plan already creates these files; only the Architecture doc needs updating.

---

### INC-07: EventBus Protocol Defined in Two Locations

**Current Situation**

The Architecture defines EventBus in two places:

1. `ports/event_bus.py` — EventBus Protocol (Layer 0, Port Interfaces)
2. `bus/protocol.py` — EventBus Protocol at package level (Layer 4)

The `bus/` package also contains `memory_bus.py` (implementation). The port protocol at `ports/event_bus.py` is sufficient — `bus/protocol.py` is a duplicate.

The Development Plan Stage 7 puts `memory_bus.py` under `infrastructure/bus/`, further confusing the location.

**Root Cause**

The EventBus was initially designed as a port (like LLMClient, FileStorage) but then also given its own top-level package `bus/` in Layer 4. This reflects an ambiguity about whether EventBus is infrastructure (like a message queue) or orchestration (like pipeline wiring). In practice, the InMemoryEventBus is a simple in-process pub/sub mechanism — it's infrastructure.

**Affected Documents**

| Document | Impact |
|----------|--------|
| 02_PYTHON_AGENT_ARCHITECTURE.md | Duplicate protocol, ambiguous layer placement |
| 03_PYTHON_AGENT_DEVELOPMENT_PLAN.md | Location mismatch with Architecture |

**Classification:** Architecture documentation inconsistency.

**Recommended Fix**

Consolidate into a single location. The cleanest resolution:

| File | Location | Purpose |
|------|----------|---------|
| `ports/event_bus.py` | Layer 0 | `EventBus` Protocol (the contract) |
| `bus/memory_bus.py` | Layer 4 | `InMemoryEventBus` implementation |
| `bus/__init__.py` | Layer 4 | Package init |

Remove `bus/protocol.py` — it duplicates `ports/event_bus.py`. The `bus/` package is the implementation package for the EventBus port, analogous to `infrastructure/llm/` being the implementation for the LLMClient port. The difference in top-level placement (`bus/` vs `infrastructure/bus/`) is acceptable because the EventBus is used by the pipeline (Layer 4), not by domain services — it's an orchestration concern, not infrastructure.

Update Dev Plan Stage 7: move `infrastructure/bus/` → `bus/`.

**Migration Impact:** Delete `bus/protocol.py` reference from Architecture. Move Dev Plan's `infrastructure/bus/` to `bus/`. 2 files re-homed.

**Priority:** LOW — Semantic cleanup. Does not affect functionality.

---

## 2. Corrected Package Layout

This is the authoritative package layout incorporating all fixes:

```
agent/
├── __init__.py                     # __version__ = "0.1.0-dev"
├── py.typed                        # PEP 561 marker
├── agent.py                        # Agent: public API entry point (Stage 10)
├── config.py                       # AgentConfig (Pydantic BaseSettings) (Stage 1)
├── exceptions.py                   # AgentException hierarchy (Stage 1)
│
├── models/                         # Layer 1: Pure Pydantic data models
│   ├── __init__.py
│   ├── state.py                    # CognitiveState, MemoryState, etc.
│   ├── memory.py                   # Episode, WorkingMemoryEntry, UserProfileData
│   ├── concepts.py                 # Concept, ExtractedConcept, ConceptGraphNode
│   ├── tools.py                    # ToolDefinition, ToolResult, ToolCallRecord
│   ├── skills.py                   # SkillDefinition, SkillResult
│   ├── routing.py                  # RouterResult, RoutingRecord, ToolMetrics
│   ├── reasoning.py                # ReasoningResult, ReasoningTrace
│   ├── evolution.py                # ScoredMemory, EvolutionSignal, MergeCandidate
│   ├── policy.py                   # CognitivePolicy, CompressionSignal, DriftMetrics
│   ├── mutations.py                # StateMutation discriminated union (7 variants)
│   ├── retrieval.py                # VectorSearchResult, RetrievalRecord
│   ├── search.py                   # SearchResult, SearchQuery, MergedSearchResult
│   └── events.py                   # PipelineEvent discriminated union (18 variants)
│
├── ports/                          # Layer 0: Protocol interfaces
│   ├── __init__.py
│   ├── llm.py                      # LLMClient Protocol
│   ├── storage.py                  # FileStorage Protocol
│   ├── http_client.py              # HttpClient Protocol
│   ├── vector_store.py             # VectorStore Protocol
│   ├── event_bus.py                # EventBus Protocol
│   └── logger.py                   # Logger Protocol
│
├── memory/                         # Layer 2: Memory services
│   ├── __init__.py
│   ├── working.py                  # WorkingMemory
│   ├── episodic.py                 # EpisodicMemory
│   ├── profile.py                  # UserProfile
│   ├── tool_stats.py               # ToolMemory
│   ├── store.py                    # MemoryStore (YAML frontmatter I/O)
│   └── writer.py                   # MemoryWriter
│
├── concepts/                       # Layer 2: Concept services
│   ├── __init__.py
│   └── extractor.py                # ConceptExtractor
│
├── reasoning/                      # Layer 2: Reasoning services
│   ├── __init__.py
│   ├── graph.py                    # ConceptGraphBuilder
│   ├── reasoner.py                 # ConceptReasoner (3 strategies)
│   └── feedback.py                 # FeedbackProcessor
│
├── routing/                        # Layer 2: Routing services
│   ├── __init__.py
│   ├── router.py                   # ToolRouter
│   └── telemetry.py                # RouterTelemetry
│
├── retrieval/                      # Layer 2: Retrieval services
│   ├── __init__.py
│   └── feedback.py                 # RagFeedback
│
├── core/                           # Layer 2: Mutation runtime
│   ├── __init__.py
│   ├── queue.py                    # MutationQueue
│   └── engine.py                   # StateMutationEngine
│
├── policy/                         # Layer 2: Policy services
│   ├── __init__.py
│   └── controller.py               # DriftController
│
├── evolution/                      # Layer 2: Evolution services
│   ├── __init__.py
│   ├── scoring.py                  # Pure functions (decay, reinforce, consolidate)
│   ├── memory_evolution.py         # MemoryEvolution
│   └── concept_evolver.py          # ConceptEvolver
│
├── tools/                          # Layer 3: Tool system
│   ├── __init__.py
│   ├── protocol.py                 # Tool abstract base class
│   ├── registry.py                 # ToolRegistry
│   ├── decision.py                 # ToolDecisionPolicy
│   └── builtins/
│       ├── __init__.py
│       ├── web_search.py           # WebSearchTool
│       ├── todos.py                # GetTodosTool, AddTodosTool, TodoStatsTool
│       ├── time.py                 # GetCurrentTimeTool
│       └── wiki_crud.py            # ListWikiTool, ReadWikiTool, WriteWikiTool, DeleteWikiTool, SearchWikiTool
│
├── skills/                         # Layer 3: Skill system
│   ├── __init__.py
│   ├── protocol.py                 # Skill abstract base class
│   ├── registry.py                 # SkillRegistry
│   └── builtins/
│       ├── __init__.py
│       ├── location.py             # GetLocationSkill
│       └── file_reader.py          # ReadFileSkill
│
├── search/                         # Layer 3: Search framework
│   ├── __init__.py
│   ├── protocol.py                 # SearchProvider abstract base class
│   ├── manager.py                  # SearchManager
│   └── providers/
│       ├── __init__.py
│       ├── bing.py                 # BingSearchProvider
│       └── duckduckgo.py           # DuckDuckGoSearchProvider
│
├── planner/                        # Layer 3: Planner
│   ├── __init__.py
│   ├── intent.py                   # IntentParser
│   ├── plan.py                     # ExecutionPlan, PlanStep models
│   └── planner.py                  # Planner
│
├── execution/                      # Layer 3: Execution Engine
│   ├── __init__.py
│   ├── engine.py                   # ExecutionEngine
│   ├── fallback.py                 # FallbackStrategy
│   └── verifier.py                 # ResultVerifier
│
├── infrastructure/                 # Layer 0: Adapter implementations
│   ├── __init__.py
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── deepseek.py             # DeepSeekLLMClient
│   │   └── mock.py                 # MockLLMClient
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── local_fs.py             # LocalFileStorage
│   │   └── memory_fs.py            # InMemoryFileStorage
│   ├── http/
│   │   ├── __init__.py
│   │   └── httpx_client.py         # HttpxHttpClient
│   ├── vector/
│   │   ├── __init__.py
│   │   └── tfidf_store.py          # TfidfVectorStore
│   └── logging/
│       ├── __init__.py
│       └── structlog_adapter.py    # StructlogLogger
│
├── bus/                            # Layer 4: Event bus implementation
│   ├── __init__.py
│   └── memory_bus.py               # InMemoryEventBus
│
├── pipeline/                       # Layer 4: Pipeline
│   ├── __init__.py
│   ├── protocol.py                 # PipelineStage Protocol
│   ├── context.py                  # PipelineContext
│   ├── pipeline.py                 # Pipeline
│   └── stages/
│       ├── __init__.py
│       ├── sanitize.py             # SanitizeStage
│       ├── route.py                # RouteStage
│       ├── retrieve.py             # RetrieveStage
│       ├── reason.py               # ReasonStage
│       ├── plan.py                 # PlanStage
│       ├── execute.py              # ExecuteStage
│       ├── prompt.py               # PromptStage
│       ├── generate.py             # GenerateStage
│       ├── sanitize_response.py    # ResponseSanitizeStage
│       ├── persist.py              # PersistStage
│       ├── learn.py                # LearnStage
│       └── health.py               # HealthStage
│
├── observability/                  # Cross-cutting
│   ├── __init__.py
│   ├── health.py                   # HealthCheck service
│   ├── metrics.py                  # MetricsCollector
│   └── tracer.py                   # ExecutionTracer
│
└── plugins/                        # Plugin SDK
    ├── __init__.py
    ├── discovery.py
    ├── manifest.py
    └── loader.py
```

**Total file count: ~120 source files** (excluding tests and `__init__.py` boilerplate).

---

## 3. Corrected Implementation Order

Each stage produces a runnable, testable project. `pytest` must pass with >80% coverage before advancing.

```
Stage 0  →  Project Initialization
Stage 1  →  Core: Models, Ports, Config, Exceptions
Stage 2  →  Memory + Concepts
Stage 3  →  Reasoning
Stage 4  →  Routing & Retrieval          ← NEW
Stage 5  →  Planner
Stage 6  →  Capability System            ← NEW (replaces old Stage 6)
Stage 7  →  Execution Engine
Stage 8  →  Infrastructure Providers
Stage 9  →  Evolution + Policy + Core
Stage 10 →  API: Agent, Pipeline, Observability
Stage 11 →  Plugin SDK
```

### Stage 0: Project Initialization

**Goal:** Empty Python project with build system, linting, type checking, test harness.

**Files:** `pyproject.toml`, `.python-version`, `.gitignore`, `.pre-commit-config.yaml`, `.github/workflows/ci.yml`, `agent/__init__.py`, `agent/py.typed`, `tests/__init__.py`, `tests/conftest.py`

**Dependencies:** None — this is the foundation.

**Depends on:** Nothing.

**Estimate:** 5 files, 2 hours. Risk: Low.

---

### Stage 1: Core — Models, Ports, Config, Exceptions

**Goal:** All Pydantic data models, port protocols, configuration, and exception hierarchy. Zero business logic.

**Files:** 20 files
- `agent/config.py`, `agent/exceptions.py`
- `agent/models/` — 13 files (all Pydantic models, frozen)
- `agent/ports/` — 6 files (all Protocols)

**Key constraint:** No file in `models/` imports from outside `models/`. No file in `ports/` imports from outside `ports/` or `models/`. Pure data and contracts.

**Depends on:** Stage 0.

**Estimate:** 20 files, 8 hours. Risk: Low.

---

### Stage 2: Memory + Concepts

**Goal:** All memory services and concept extraction. No LLM, no tools, no pipeline.

**Files:** 10 files
- `agent/memory/` — 6 files (working, episodic, profile, tool_stats, store, writer)
- `agent/concepts/` — 1 file (extractor)
- Tests for all services

**Graceful degradation:**
- `MutationQueue` not yet built → accept `None`, skip mutation queuing
- `FileStorage` is a protocol → inject `InMemoryFileStorage` in tests
- `VectorStore` is a protocol → referenced but not called yet

**Depends on:** Stage 1.

**Estimate:** 10 files, 16 hours. Risk: Medium.

---

### Stage 3: Reasoning

**Goal:** ConceptGraphBuilder, ConceptReasoner (3 strategies), FeedbackProcessor.

**Files:** 4 files
- `agent/reasoning/graph.py`, `reasoner.py`, `feedback.py`
- Tests

**Graceful degradation:**
- `DriftController` not yet built → create with `DEFAULT_POLICY`, override in Stage 9
- `MutationQueue` not yet built → accept `None`

**Depends on:** Stage 1 (models), Stage 2 (MemoryStore for FeedbackProcessor).

**Estimate:** 4 files, 12 hours. Risk: Low.

---

### Stage 4: Routing & Retrieval ← NEW

**Goal:** ToolRouter, RouterTelemetry, RagFeedback. Pure computation domain services.

**Files:** 4 files
- `agent/routing/router.py` — keyword-scoring intent classifier (6 tool categories)
- `agent/routing/telemetry.py` — adaptive threshold evolution
- `agent/retrieval/feedback.py` — retrieval quality feedback, query clustering, document weight adjustment
- Tests

**Key algorithms:**
- Router: weighted keyword + regex scoring, adaptive threshold from telemetry
- Telemetry: `threshold = clamp(0.2 + (1 - successRate) × 0.4, 0.1, 0.6)`
- RagFeedback: used docs +0.05, unused -0.02, 3-confirmation gate, 0.15 downweight factor

**Depends on:** Stage 1 (models only). No filesystem, no LLM, no external I/O.

**Estimate:** 4 files, 8 hours. Risk: Low.

---

### Stage 5: Planner

**Goal:** IntentParser, ExecutionPlanner, Planner.

**Files:** 4 files
- `agent/planner/intent.py`, `plan.py`, `planner.py`
- Tests

**Depends on:** Stage 1 (models). Also accepts ToolInfo/SkillInfo/SearchProviderInfo types from models — doesn't need the actual registries.

**Estimate:** 4 files, 10 hours. Risk: Medium (new module, no TypeScript equivalent for IntentParser).

---

### Stage 6: Capability System ← NEW (replaces old Stage 6)

**Goal:** All capability layer: Tool protocol + registry + decision + builtins, Skill protocol + registry + builtins, Search protocol + manager + providers.

**Files:** 22 files
- `agent/tools/` — 8 files (protocol, registry, decision, 4 builtins)
- `agent/skills/` — 5 files (protocol, registry, 2 builtins)
- `agent/search/` — 6 files (protocol, manager, 2 providers)
- Tests

**Key design:** Every capability implements a common protocol with `name`, `description`, `execute(args, context)`, `validate_args(args)`. Registries support auto-discovery and registration.

**ToolDecisionPolicy** depends on `LLMClient` protocol (injected, not imported). Tests use `MockLLMClient`. This is correct per dependency inversion.

**Search providers (Bing, DuckDuckGo):** HTML scraping implementations behind the SearchProvider protocol. Initial version only; API-based providers added later.

**Remaining providers from Architecture (bilibili, github, arxiv, local, obsidian):** Deferred to Plugin SDK stage. They are optional extensions, not core requirements.

**Depends on:** Stage 1 (models + ports). Does NOT depend on memory, reasoning, routing, or planner modules.

**Estimate:** 22 files, 24 hours. Risk: Medium (ToolDecisionPolicy LLM integration needs mock testing).

---

### Stage 7: Execution Engine

**Goal:** ExecutionEngine, FallbackStrategy, ResultVerifier.

**Files:** 4 files
- `agent/execution/engine.py`, `fallback.py`, `verifier.py`
- Tests

**Key change from old plan:** All capability protocols and registries now exist (built in Stage 6). ExecutionEngine no longer needs `None` defaults for ToolRegistry, SkillRegistry, SearchManager — they're real dependencies.

**Depends on:** Stage 1 (models, ports/event_bus), Stage 6 (tools/skills/search protocols).

**Estimate:** 4 files, 16 hours. Risk: Medium (concurrent execution with asyncio.gather).

---

### Stage 8: Infrastructure Providers

**Goal:** Concrete implementations of all port protocols.

**Files:** 11 files
- `agent/infrastructure/llm/` — deepseek.py, mock.py
- `agent/infrastructure/storage/` — local_fs.py, memory_fs.py
- `agent/infrastructure/http/` — httpx_client.py
- `agent/infrastructure/vector/` — tfidf_store.py
- `agent/infrastructure/logging/` — structlog_adapter.py
- `agent/bus/` — memory_bus.py
- Tests

**Note on `bus/` location:** `bus/memory_bus.py` is the implementation of `ports/event_bus.py`. It lives at the top level (not under `infrastructure/`) because the EventBus is an orchestration concern (Layer 4), consumed by the pipeline, not by domain services.

**Depends on:** Stage 1 (ports). No domain service dependencies.

**Estimate:** 11 files, 12 hours. Risk: Medium (TF-IDF Chinese tokenization needs validation).

---

### Stage 9: Evolution + Policy + Core

**Goal:** Memory evolution, ConceptEvolver, DriftController, MutationQueue, StateMutationEngine.

**Files:** 10 files
- `agent/evolution/` — scoring.py, memory_evolution.py, concept_evolver.py
- `agent/policy/` — controller.py
- `agent/core/` — queue.py, engine.py
- Tests

**Mutation system is the SSOT gatekeeper:** All state changes flow through MutationQueue → StateMutationEngine. ±0.05 clamp on all learning updates. 7 mutation types with priority ordering.

**Depends on:** Stage 1 (models), Stage 2 (memory services — EpisodicMemory, MemoryStore, UserProfile).

**Estimate:** 10 files, 16 hours. Risk: Medium (mutation atomicity, async correctness).

---

### Stage 10: API — Agent, Pipeline, Observability

**Goal:** Full Agent class, Pipeline, 12 PipelineStages, EventBus integration, observability.

**Files:** 18 files
- `agent/agent.py` — public API
- `agent/pipeline/` — protocol, context, pipeline, 12 stages
- `agent/observability/` — health, metrics, tracer
- Tests (unit + integration + e2e)

**This is the composition root.** All modules from Stages 1-9 are wired together here. Pipeline stages are independent and testable in isolation.

**Depends on:** ALL stages 1-9. This is the only stage with universal dependencies.

**Estimate:** 18 files, 20 hours. Risk: HIGH (first time all modules are wired together; reentrancy guard; async coordination between streaming, events, and callbacks).

---

### Stage 11: Plugin SDK

**Goal:** Plugin auto-discovery, manifest format, installation, examples, documentation.

**Files:** 7 files + examples + docs
- `agent/plugins/` — discovery.py, manifest.py, loader.py
- `examples/` — custom_tool/, custom_provider/
- `docs/` — PLUGIN_SDK.md, EXAMPLES.md

**Depends on:** Stage 10 (Agent class for capability registration).

**Estimate:** 7 files, 8 hours. Risk: Low.

---

## 4. Corrected Dependency Graph

```
Stage 0 ──→ Stage 1 ──→ Stage 2 ──→ Stage 3 ──→ Stage 9 ──→ Stage 10 ──→ Stage 11
                │          │            │            │            ↑
                │          │            │            │            │
                │          │            └──→ Stage 9 (via MemoryStore)
                │          │                        ↑
                │          │                        │
                │          └──→ Stage 4 ────────────┤
                │          └──→ Stage 5 ────────────┤
                │          └──→ Stage 6 ──→ Stage 7 ┤
                │          └──→ Stage 8 ────────────┘
                │
                └──→ everything depends on Stage 1 (models + ports)
```

### Dependency Matrix

| Stage | Depends On | Provides To |
|-------|-----------|-------------|
| 0 | — | 1 |
| 1 | 0 | 2, 3, 4, 5, 6, 7, 8, 9, 10 |
| 2 | 1 | 3, 9, 10 |
| 3 | 1, 2 | 10 |
| 4 | 1 | 10 |
| 5 | 1 | 10 |
| 6 | 1 | 7, 10 |
| 7 | 1, 6 | 10 |
| 8 | 1 | 10 |
| 9 | 1, 2 | 10 |
| 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9 | 11 |
| 11 | 10 | — |

### Critical Path

```
Stage 0 → 1 → 2 → 3 → 9 → 10 → 11     (7 stages, sequential)
```

### Parallelizable Stages (after Stage 1)

Stages 2, 4, 5, 6, and 8 all depend ONLY on Stage 1. They can be built in parallel by multiple developers:

```
Stage 1 complete
    ├── Dev A: Stage 2 (Memory + Concepts) ──→ Stage 3 (Reasoning) ──→ Stage 9 (Evolution)
    ├── Dev B: Stage 4 (Routing) → Stage 5 (Planner)
    ├── Dev C: Stage 6 (Capability System) ──→ Stage 7 (Execution Engine)
    └── Dev D: Stage 8 (Infrastructure)

All converge → Stage 10 (API) → Stage 11 (Plugin SDK)
```

---

## 5. Corrected File & Effort Estimates

| Stage | Name | Files | Hours | Risk | Status |
|-------|------|-------|-------|------|--------|
| 0 | Project Init | 5 | 2 | Low | Unchanged |
| 1 | Core | 20 | 8 | Low | Unchanged |
| 2 | Memory + Concepts | 10 | 16 | Medium | Unchanged |
| 3 | Reasoning | 4 | 12 | Low | Unchanged |
| **4** | **Routing & Retrieval** | **4** | **8** | **Low** | **NEW** |
| 5 | Planner | 4 | 10 | Medium | Renumbered |
| **6** | **Capability System** | **22** | **24** | **Medium** | **NEW** |
| 7 | Execution Engine | 4 | 16 | Medium | Renumbered |
| 8 | Infrastructure | 11 | 12 | Medium | Renumbered |
| 9 | Evolution + Policy + Core | 10 | 16 | Medium | Renumbered |
| 10 | API | 18 | 20 | High | Renumbered |
| 11 | Plugin SDK | 7 | 8 | Low | Renumbered |
| **Total** | | **119** | **152** | | |

Old plan: 93 files, 130 hours, 10 stages (0-10).
New plan: 119 files, 152 hours, 12 stages (0-11).

The increase (+26 files, +22 hours) accounts for the 4 previously missing subsystems.

---

## 6. Module Ownership

Each domain package has a single owner stage. No file is created in more than one stage.

| Package | Owner Stage | Files |
|---------|-------------|-------|
| `agent/models/` | Stage 1 | 13 |
| `agent/ports/` | Stage 1 | 6 |
| `agent/memory/` | Stage 2 | 6 |
| `agent/concepts/` | Stage 2 | 1 |
| `agent/reasoning/` | Stage 3 | 3 |
| `agent/routing/` | Stage 4 | 2 |
| `agent/retrieval/` | Stage 4 | 1 |
| `agent/planner/` | Stage 5 | 3 |
| `agent/tools/` | Stage 6 | 8 |
| `agent/skills/` | Stage 6 | 5 |
| `agent/search/` | Stage 6 | 3 |
| `agent/execution/` | Stage 7 | 3 |
| `agent/infrastructure/` | Stage 8 | 9 |
| `agent/bus/` | Stage 8 | 1 |
| `agent/evolution/` | Stage 9 | 3 |
| `agent/policy/` | Stage 9 | 1 |
| `agent/core/` | Stage 9 | 2 |
| `agent/pipeline/` | Stage 10 | 15 |
| `agent/observability/` | Stage 10 | 3 |
| `agent/agent.py` + top-level | Stage 10 | 2 |
| `agent/plugins/` | Stage 11 | 3 |

---

## 7. Layer Dependency Rules (Unchanged from Architecture)

```
Layer 0 (infrastructure/, bus/)    → depends on ports/ + models/ + external libs
Layer 1 (models/, ports/)          → depends on pydantic + stdlib only
Layer 2 (memory/, reasoning/, etc.) → depends on models/ + ports/ (protocols only, never implementations)
Layer 3 (tools/, skills/, etc.)    → depends on models/ + ports/ + Layer 2 services
Layer 4 (pipeline/)                → depends on models/ + ports/ + Layer 2 + Layer 3
Layer 5 (agent.py)                 → depends on everything (composition root)
```

**Forbidden imports:**
- Layer 2 must never import from Layer 3, Layer 4, or `infrastructure/`
- Layer 1 must never import from any other layer
- `ports/` must never import from `infrastructure/`
- `models/` must never import from outside `models/`

---

## 8. Resolution Summary

| ID | Issue | Classification | Resolution |
|----|-------|---------------|------------|
| INC-01 | Routing missing from Dev Plan | Dev Plan omission | New Stage 4: Routing & Retrieval |
| INC-02 | Retrieval missing from Dev Plan | Dev Plan omission | Merged into Stage 4 |
| INC-03 | Tool system missing from Dev Plan | Dev Plan omission | New Stage 6: Capability System |
| INC-04 | Skill system missing from Dev Plan | Dev Plan omission | Merged into Stage 6 |
| INC-05 | Stage ordering (Execution before protocols) | Dev Plan ordering | Stage 6 placed before Stage 7 |
| INC-06 | `core/` not in Architecture layout | Architecture gap | Add `core/` to Architecture; clarify model vs runtime split |
| INC-07 | EventBus protocol in two locations | Architecture inconsistency | Consolidate: protocol in `ports/`, impl in `bus/` |

---

## 9. Document Update Checklist

Changes required in each source document:

### 03_PYTHON_AGENT_DEVELOPMENT_PLAN.md (overridden by this document)
- [ ] Replace stage list with corrected 12-stage sequence
- [ ] Add Stage 4 (Routing & Retrieval) specification
- [ ] Add Stage 6 (Capability System) specification
- [ ] Update all stage numbers for Stages 4-10 → 5-11 + new stages
- [ ] Update file count: 93 → 119
- [ ] Update hour estimate: 130 → 152
- [ ] Update dependency graph and critical path
- [ ] Update branch strategy (add `stage/4-routing-retrieval`, `stage/6-capability-system`)
- [ ] Update commit message list
- [ ] Remove `infrastructure/bus/` → reference `bus/` instead

### 02_PYTHON_AGENT_ARCHITECTURE.md
- [ ] Add `core/` package to package structure (Section 3)
- [ ] Remove `bus/protocol.py` — protocol is in `ports/event_bus.py`
- [ ] Add `routing/` to corrected package layout (already present, verify)
- [ ] Add `retrieval/` to corrected package layout (already present, verify)
- [ ] Update layer descriptions: `core/` is Layer 2

### 01_PYTHON_RECONSTRUCTION_SPEC.md
- [ ] No changes required — this document describes TypeScript behavior, not Python architecture

---

## 10. Final Implementation Sequence

This is the authoritative build order. No code shall be written in an order that violates this sequence.

```
Stage 0  — 2026-07-01: Project Initialization (5 files)
Stage 1  — 2026-07-02: Core: Models, Ports, Config, Exceptions (20 files)
Stage 2  — 2026-07-05: Memory + Concepts (10 files) ─────────────┐
Stage 3  — 2026-07-08: Reasoning (4 files)                        │
Stage 4  — 2026-07-05: Routing & Retrieval (4 files) ─┐           │
Stage 5  — 2026-07-07: Planner (4 files)               │           │
Stage 6  — 2026-07-05: Capability System (22 files) ───┤           │
Stage 7  — 2026-07-10: Execution Engine (4 files)      │           │
Stage 8  — 2026-07-05: Infrastructure Providers (11 files)        │
Stage 9  — 2026-07-12: Evolution + Policy + Core (10 files) ←─────┘
Stage 10 — 2026-07-15: API: Agent, Pipeline, Observability (18 files)
Stage 11 — 2026-07-18: Plugin SDK (7 files)
```

Dates assume single developer, sequential execution. With 3 developers working in parallel after Stage 1, Stages 2-9 can complete within ~10 days, and Stage 10 by day 13.

---

*This document is authoritative. Any conflict with 03_PYTHON_AGENT_DEVELOPMENT_PLAN.md is resolved in favor of this document.*
