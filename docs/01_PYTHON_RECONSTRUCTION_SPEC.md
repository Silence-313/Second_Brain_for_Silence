# Python Agent Reconstruction Specification

> **Purpose:** Complete blueprint for rebuilding the Agent Framework in Python without referencing the TypeScript implementation.
> **Scope:** Agent framework only. Obsidian UI, components, and plugin glue are excluded.
> **Target:** Python 3.12+ with no framework dependency beyond the Python standard library + HTTP client + Pydantic (for data models).

---

## 1. Executive Summary

The Agent is a **5-layer self-improving cognitive system** designed for personal knowledge management. It processes user queries through a pipeline of deterministic routing, semantic memory retrieval, concept-aware reasoning, proactive tool execution, LLM generation, and post-interaction learning.

**Core architectural strengths:** Cleanly separated memory/reasoning/evolution layers, SSOT-based state management with mutation safety clamps, unique self-improving concept evolution.

**Core architectural weakness:** The Tool System has no interface abstraction—tools are hardcoded in the central orchestrator. This is the primary target for redesign in Python.

**Key design principle:** All AI model calls are stateless—the Agent owns the state, not the model. The model is a reasoning engine that receives pre-assembled context and tools.

---

## 2. Agent File Inventory

### Category: Core Orchestration
| File | Purpose |
|------|---------|
| `agent_orchestrator.ts` | Central pipeline coordinator—12-stage request lifecycle |

### Category: Routing
| File | Purpose |
|------|---------|
| `tool_router.ts` | Keyword-scoring intent classifier (6 tool categories) |
| `router_telemetry.ts` | Per-tool success tracking, adaptive threshold evolution |

### Category: Memory (Layer 1)
| File | Purpose |
|------|---------|
| `memory/working_memory.ts` | Short-term conversation buffer (last N messages, in-memory) |
| `memory/episodic_memory.ts` | Event/goal/decision storage with evolution scoring fields |
| `memory/user_profile.ts` | Structured user attributes with confidence tracking |
| `memory/tool_memory.ts` | Tool usage frequency/success rate/context effectiveness |
| `memory/memory_writer.ts` | Post-interaction classification, merge dedup, concept extraction trigger |
| `memory/memory_store.ts` | Markdown persistence: YAML frontmatter, CRUD for episodes/concepts/reasoning/policy |

### Category: Concepts (Layer 2)
| File | Purpose |
|------|---------|
| `memory/concept_extractor.ts` | Heuristic concept extraction (headings/bigrams/trigrams/English compounds) |

### Category: Reasoning (Layer 3)
| File | Purpose |
|------|---------|
| `reasoning/concept_graph_builder.ts` | Full graph + 1-hop subgraph construction from concept data |
| `reasoning/concept_reasoner.ts` | 3-strategy reasoning engine (graph traversal/pattern matching/abstraction) |

### Category: Feedback (Layer 4)
| File | Purpose |
|------|---------|
| `reasoning/feedback_processor.ts` | Reasoning trace storage, concept weight reinforcement, strategy learning |
| `reasoning/concept_evolver.ts` | Concept merge/split/decay evolution cycles |

### Category: Policy (Layer 5)
| File | Purpose |
|------|---------|
| `policy/drift_controller.ts` | Global cognitive governor: preference balance, compression detection, health scoring |

### Category: Tool System
| File | Purpose |
|------|---------|
| `tools/tool_decision_policy.ts` | LLM-based autonomous tool/skill usage decision |

### Category: Skills
| File | Purpose |
|------|---------|
| `skills/skill_registry.ts` | Registry pattern for privileged system capabilities |
| `skills/get_current_location.ts` | Browser geolocation via Navigator API |
| `skills/read_local_file.ts` | Sandboxed file reading (6-layer security) |
| `skills/index.ts` | Default skill registry factory |

### Category: Core Architecture
| File | Purpose |
|------|---------|
| `core/cognitive_state.ts` | SSOT type definitions for all 5 layers |
| `core/state_mutation_engine.ts` | Authoritative mutation validation, clamping, batch application |
| `core/mutation_queue.ts` | Mutation buffer with dedup, sort, flush |

### Category: Retrieval
| File | Purpose |
|------|---------|
| `vector_wiki_store.ts` | TF-IDF vectorization, cosine similarity search, RAG feedback integration |
| `rag_feedback.ts` | Retrieval quality feedback, query clustering, document weight adjustment |

### Category: Evolution
| File | Purpose |
|------|---------|
| `system_evolution.ts` | Memory decay/reinforcement/consolidation scoring functions |

### Category: Exports
| File | Purpose |
|------|---------|
| `index.ts` | Barrel export of all agent modules |

**Count: 22 source files** (excluding tests)

---

## 3. Architecture Overview

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   AgentOrchestrator                          │
│              (Central Pipeline Coordinator)                  │
└──────┬──────┬──────┬──────┬──────┬──────┬──────┬───────────┘
       │      │      │      │      │      │      │
       ▼      ▼      ▼      ▼      ▼      ▼      ▼
    Router  Memory  Reason  Tools  Skills  LLM   Evolution
    (fast)  (RAG)   (graph) (switch) (reg)  (fetch) (cycles)
```

### 3.2 5-Layer Cognitive Stack

| Layer | Name | Directory | Storage |
|-------|------|-----------|---------|
| L1 | Memory | `memory/` | JSON + Markdown files |
| L2 | Concepts | `memory/` | Markdown files with YAML frontmatter |
| L3 | Reasoning | `reasoning/` | In-memory (no persistence) |
| L4 | Feedback | `reasoning/` | Markdown files |
| L5 | Policy | `policy/` | JSON file |

### 3.3 Communication Pattern

All modules communicate through the Orchestrator. There is no direct module-to-module communication except:
- `memory_writer` → `system_evolution` (scoring functions)
- `mutation_queue` → `state_mutation_engine` → `memory_store` (mutation pipeline)
- `feedback_processor` → `drift_controller` (policy queries)

### 3.4 Core Design Decisions

1. **Dual-write persistence:** JSON is the source of truth (fast serialization), Markdown is the mirror (human-readable). Writes are best-effort to Markdown.
2. **No native function calling:** The LLM API never receives `tools`—all tool execution is proactive, before the LLM call.
3. **Safety-first mutations:** All state changes go through MutationQueue → StateMutationEngine with ±0.05 clamp gates.
4. **Soft deletion only:** Memories and concepts are marked for removal, never physically deleted.
5. **Policy-aware reasoning:** Concept seed selection is biased by learned domain preferences and strategy weights.

---

## 4. Runtime Lifecycle

### Stage 0: Preprocessing
- **Purpose:** Sanitize input, prevent injection
- **Input:** Raw user text
- **Output:** Sanitized text (≤4000 chars, code blocks stripped, system-prompt injection blocked)
- **Module:** AgentOrchestrator.sanitizeInput()

### Stage 1: Working Memory Push
- **Purpose:** Record user message in short-term buffer
- **Input:** Sanitized user text
- **Output:** WorkingMemory updated (last 20 messages)
- **Module:** WorkingMemory.push()

### Stage 2: Intent Routing
- **Purpose:** Fast deterministic classification of user intent
- **Input:** Sanitized user text
- **Output:** RouterResult { tool: string, confidence: 0..1, reason: string }
- **Module:** tool_router.routeTool() + RouterTelemetry
- **Algorithm:** Keyword + regex scoring across 6 tool categories, highest weighted match wins, adaptive threshold from telemetry

### Stage 3: Memory Retrieval
- **Purpose:** Gather context for the LLM
- **Input:** User query + RouterResult
- **Output:** { wikiResults[], episodicContext, profileContext, toolStats, conceptReasoning }
- **Sub-stages:**
  1. VectorWikiStore.search(query, topK=3) — TF-IDF cosine similarity
  2. EpisodicMemory.search(query, topK=5) — keyword + recency + usefulness scoring
  3. EpisodicMemory.formatForContext(5) — if tool is memory_search or confidence < 0.7
  4. UserProfile.formatForContext() — structured user traits
  5. ToolMemory.getStats(route.tool) — success rate for routed tool
  6. buildConceptReasoning(query) — concept graph + 3-strategy reasoning (see Section 7)

### Stage 3.5: Tool & Skill Decision
- **Purpose:** LLM decides whether to proactively execute tools/skills
- **Input:** User query + wiki context + concept context + episodic context + available tools/skills list
- **Output:** ToolDecisionResult { use_tool, tool_name, use_skill, skill_name, confidence, reason, query_rewrite }
- **Module:** ToolDecisionPolicy.decide()
- **Mechanism:** Separate LLM call with strict JSON output format, temperature=0.1, max_tokens=256
- **Fallback:** If JSON parse fails, uses conservative heuristics (web_search for URLs, get_todos for date mentions)

### Stage 3.5b: Proactive Tool Execution
- **Purpose:** Execute tool before main LLM call, inject results into context
- **Condition:** ToolDecisionResult.use_tool === true
- **Execution:** Orchestrator builds tool-specific args from query_rewrite, calls executeToolLocal()
- **Supported tools:** web_search, get_todos, add_todos, get_todo_stats, get_current_time, search_wiki, list_wiki_files, read_wiki_file, write_wiki_file, delete_wiki_file
- **Skill execution:** If use_skill, executes via SkillRegistry.execute()

### Stage 4: Prompt Construction
- **Purpose:** Assemble the system prompt with all gathered context
- **Input:** Memory context + tool results + skill results
- **Output:** System prompt string (≤8000 chars, with truncation guard)
- **Sections:** Time context → User profile → Wiki context → Episodic context → Concept reasoning → Rules → Tool/Skill results
- **Rules include:** No markdown tables, prefer concept reasoning over raw notes, cite sources, don't fabricate

### Stage 5: Message Assembly
- **Purpose:** Build the message array for the LLM API
- **Input:** System prompt + chat history (last 10) + user text
- **Output:** Messages array [{role: "system"}, ...{role: "user"}]

### Stage 6: LLM Call
- **Purpose:** Generate response via streaming API
- **Input:** Messages array (no tools array—DeepSeek doesn't support native function calling)
- **Output:** Full response text (streamed via SSE → chunk-by-chunk callback)
- **Module:** AgentOrchestrator.streamLLMWithTimeout()
- **Timeout:** 60s via AbortController
- **Throttle:** 50ms between DOM paint batches

### Stage 6.5: Response Sanitization
- **Purpose:** Strip leaked tool call text from response (safety net)
- **Input:** Raw LLM response
- **Output:** Cleaned response (DSML/invoke/tool_calls blocks removed)
- **Module:** AgentOrchestrator.stripToolCallText()

### Stage 7: Working Memory Push
- **Purpose:** Record assistant response in short-term buffer
- **Input:** Cleaned response text
- **Module:** WorkingMemory.push()

### Stage 8: Memory Writing
- **Purpose:** Classify and persist interaction as memories
- **Input:** Full interaction record {userMessage, assistantResponse, toolUsed, toolResult, routerConfidence, timestamp}
- **Output:** MemoryWriteDecisions + persisted entries
- **Module:** MemoryWriter.analyze() + commit()
- **Sub-stages:**
  1. Profile analysis (regex patterns for "my name is", "I work on", etc.)
  2. Episodic analysis (goal/decision/milestone keyword detection)
  3. Semantic analysis (fact detection)
  4. Tool usage record
  5. Consolidation check (merge similar memories, reinforce existing)
  6. Concept extraction (heuristic, from episode content)
  7. Markdown persistence (best-effort mirror)

### Stage 9: Router Telemetry
- **Purpose:** Record routing decision + outcome for adaptive learning
- **Input:** RoutingRecord {query, selectedTool, confidence, executionSuccess, latencyMs, timestamp}
- **Module:** RouterTelemetry.recordRouting()

### Stage 10: RAG Feedback
- **Purpose:** Record retrieval quality, adjust document weights
- **Input:** RetrievalRecord {query, retrievedDocs[], usedDocs[], answerQuality, timestamp}
- **Module:** RagFeedback.recordRetrieval()
- **Mechanism:** Used docs get +0.05 weight, unused get -0.02, vector scores updated via VectorWikiStore.applyFeedback()

### Stage 10.5: Cognitive Feedback
- **Purpose:** Learn from reasoning quality
- **Input:** ReasoningResult from Stage 3 concept reasoning
- **Module:** FeedbackProcessor.process()
- **Actions:** Store reasoning trace as markdown, reinforce concept weights (±0.05), track insight frequency, detect unstable relationships

### Stage 10.5b: Mutation Flush
- **Purpose:** Apply all queued state changes atomically
- **Input:** Queued StateMutations from memory writing + feedback
- **Module:** MutationQueue.flush(StateMutationEngine)
- **Actions:** Deduplicate, sort by priority, validate, clamp, apply batch

### Stage 10.6: Health Check (every 15 interactions)
- **Purpose:** Detect compression signals, compute cognitive health
- **Module:** DriftController.computeHealth() → DriftController.detectCompressionSignals()

### Stage 11: Evolution Cycle
- **Every 10 interactions:** Memory decay + consolidation
  - EpisodicMemory.applyDecay() — exponential decay with usage damping
  - MemoryWriter.runMemoryMaintenance() — reinforcement, merge
- **Every 20 interactions:** Concept evolution
  - ConceptEvolver.evolve() — merge candidates (≥70% shared episodes), split detection, decay (7+ days unused)
  - High-confidence merges (≥85% similarity) auto-applied

### Stage 12: Persistence
- **Purpose:** Save all memory state to disk
- **Dual-write:** JSON files (source of truth) + Markdown mirror (human-readable)
- **Files:** episodic.json, profile.json, tool_stats.json, vector_index.json, router_telemetry.json, rag_feedback.json
- **Markdown:** episodes/*.md, concepts/*.md, profile.md, INDEX.md

---

## 5. Module Responsibilities

### 5.1 AgentOrchestrator

**Purpose:** Central pipeline coordinator. Owns the complete request lifecycle.

**Responsibilities:**
- Initialize all subsystems (memory stores, vector index, cognitive policy)
- Execute the 12-stage pipeline for each user request
- Reentrancy guard (prevents concurrent process() calls)
- LLM error handling (5+ consecutive errors → degraded status)
- Input sanitization (prompt injection prevention)
- Response post-processing (tool call text stripping)
- Periodic health checks and evolution cycle triggers
- Memory state persistence

**Owned State:**
- All subsystem instances (vector store, 6 memory stores, graph builder, reasoner, feedback processor, evolver, drift controller, mutation queue/engine, tool decision policy, skill registry, router telemetry, RAG feedback)
- Interaction counter
- Consecutive error counter
- Reentrancy guard flag

**Dependencies:** 18 direct imports

**Public API:**
- `initialize()` — async bootstrap
- `process(userText, chatHistory, onStream?, onActivity?)` → {response, toolCalls[]}
- `healthCheck()` → AgentHealth
- `rebuildVectorIndex()` — rebuild TF-IDF from vault files
- `saveMemoryState()` — persist to disk
- `getStateSnapshot()` → CognitiveState
- `searchEpisodic(query)`, `searchWiki(query)` — public query access
- `getProfile()` → UserProfileData

### 5.2 ToolRouter

**Purpose:** Fast deterministic intent classification without LLM cost.

**Algorithm:** For each of 6 tool categories, compute a match score from keyword hits + regex pattern matches. Each category has a weight. The category with the highest weighted score above its adaptive threshold wins.

**Tool categories:**
1. `add_todos` (weight 1.0) — task creation intent
2. `get_todos` (weight 0.9) — task query intent
3. `get_current_time` (weight 0.85) — time/date inquiry
4. `web_search` (weight 0.7) — search/information intent
5. `wiki_search` (weight 0.75) — personal knowledge query
6. `memory_search` (weight 0.6) — "do you remember" patterns

**Adaptive threshold:** Each tool's minimum confidence threshold is adjusted by RouterTelemetry based on historical success rates. Higher success → lower threshold (easier to select). Lower success → higher threshold.

### 5.3 RouterTelemetry

**Purpose:** Self-tuning routing through per-tool success tracking.

**State:** Per-tool metrics: successRate, avgConfidence, contextMatchScore, selectionCount, adaptiveThreshold, policyWeight, recentDecisions[].

**Adaptive threshold formula:**
```
newThreshold = max(0.1, min(0.6, BASE_THRESHOLD + (1 - successRate) * 0.4))
```
This means: high-success tools have near-0.1 threshold (easily selected), low-success tools have near-0.6 threshold (rarely selected).

**Policy weight evolution:** Based on success rate deltas over time. Tools with improving success rates gain weight.

### 5.4 WorkingMemory

**Purpose:** Short-term conversation buffer. Last 20 messages. In-memory only, never persisted.

**Operations:** push(), getAll(), getLast(n), getByRole(), getRecentContext(maxTokens), clear()

### 5.5 EpisodicMemory

**Purpose:** Persistent event/goal/decision storage with evolution scoring.

**Entry structure:** id, timestamp, type (event|goal|decision|milestone|question), summary, detail, importance, tags, relatedFiles, importanceScore, usageFrequency, lastAccessTime, decayScore, usefulnessScore, markedForRemoval.

**Capacity:** 200 entries. Pruning removes lowest composite-score entries (marked first, then by importance × recency).

**Query:** search(query, topK) — keyword + tag + type matching with recency boost and usefulness bonus.

**Evolution:**
- `markAccessed(id)` — reset decay on access
- `reinforce(id, amount)` — boost importanceScore (±0.05 clamp)
- `applyDecay(cycles)` — exponential decay: `decay = importanceScore × e^(-effectiveRate × cycles)`, where effectiveRate = 0.03 × (1 - usageFrequency × 0.6)
- Mark for removal: decayScore < 0.25 AND 0 usage AND 14+ cycles → markedForRemoval = true

### 5.6 UserProfile

**Purpose:** Structured user attributes with confidence tracking.

**Fields:** name, preferredName, role, timezone, language, interests[], expertise[], workHabits[], activeProjects[], commonTools[], responseStyle, preferredFormat, currentFocus[], longTermGoals[], confidenceScores{}.

**Operations:** get(key), set(key, value, confidence), addToArray(field, value), removeFromArray(field, value).

**Context format:** Only outputs non-empty fields as "## 用户画像" markdown block for system prompt injection.

### 5.7 ToolMemory

**Purpose:** Track tool usage performance across calls.

**Operations:** recordCall(toolName, result, query, contextType), getSuccessRate(toolName), getEffectiveness(toolName), getFrequency(toolName), suggestAlternate(toolName, query), getStats(toolName), getAllStats().

**Pattern tracking:** Extracts first 3 meaningful words from query as "pattern", tracks per-pattern frequency, suggests alternate tools with higher effectiveness for similar patterns.

### 5.8 MemoryWriter

**Purpose:** Post-interaction classification and persistence coordination.

**Analysis pipeline:**
1. Profile: regex patterns for identity statements ("I am X", "I work on Y"), interests, projects
2. Episodic: keyword detection for goals, decisions, milestones, questions
3. Semantic: fact detection for knowledge worth remembering
4. Tool: unconditional tool usage record

**Commit pipeline:**
1. For episodic: consolidation check (Jaccard similarity > 0.5 with existing → reinforce instead of duplicate)
2. Write to EpisodicMemory
3. Optionally write through MarkdownMemoryStore (best-effort)
4. Trigger ConceptExtractor on the episode content
5. Create episode↔concept [[wikilink]] links

### 5.9 MarkdownMemoryStore

**Purpose:** Human-readable vault-native persistence layer.

**Storage structure:**
```
agent-memory/
  episodes/         — one .md per episode (YAML frontmatter + body)
  concepts/         — one .md per concept (YAML frontmatter)
  reasoning/        — reasoning traces
  policy/           — cognitive_policy.json
  profile.md        — user profile
  INDEX.md          — auto-generated directory
```

**Operations:** loadEpisodicEntries(), writeEpisode(), syncEpisodicEntries(), loadConcepts(), writeConcept(), updateConceptWeights(), markConceptRelationships(), loadProfile(), saveProfile(), loadPolicy(), saveToolDecision(), saveReasoningTrace().

**YAML frontmatter fields per episode:** id, timestamp, type, summary, importance, tags, related_files, importance_score, usage_frequency, last_access_time, decay_score, usefulness_score, marked_for_removal.

### 5.10 ConceptExtractor

**Purpose:** Heuristic concept extraction from episode content. No LLM dependency.

**Extraction strategies:**
1. **Headings** (confidence +0.35): Extract `#`, `##`, `###` headings, filter structural labels
2. **Chinese bigrams** (confidence ×0.3): Frequency-based extraction from CJK text, min count=2
3. **Chinese trigrams** (confidence ×0.5): Longer terms, more specific, noise-filtered
4. **English compounds** (confidence ×0.4): CamelCase, snake_case, kebab-case, 2-word phrases

**Post-processing:** Rank by score → filter min confidence 0.25 → deduplicate similar concepts (≥60% word overlap or subset) → cap at 6 concepts.

**Existing concept matching:** If an extracted concept name is similar to an existing concept, boost +0.2.

### 5.11 ConceptGraphBuilder

**Purpose:** Build in-memory concept graph from loaded concept data.

**Edge types:**
1. **related** (weight 0.8): Explicit `related[]` links in concept YAML frontmatter
2. **shared-episode** (weight 0.3+): Two concepts share episode sources. Weight = shared_count / max(2, min(sources))
3. **tag-overlap** (weight 0.3+): Two concepts share tags. Weight = shared_tags / max_tags

**Subgraph construction:** Given seed concept slugs, build 1-hop subgraph (seed nodes + direct neighbors + all edges among them). Identify central concepts (highest degree in subgraph).

### 5.12 ConceptReasoner

**Purpose:** Pure graph-based reasoning. No LLM. No I/O.

**Three independent strategies:**
1. **Graph Traversal:** Follow edges from seed concepts, identify nodes with high degree/centrality, find bridging concepts that connect otherwise separate clusters
2. **Pattern Matching:** Detect repeated co-occurrence patterns between concepts and query terms. Concepts frequently co-mentioned with query terms are key concepts
3. **Abstraction:** Group tightly-connected concepts into clusters, surface higher-level themes, detect contradictions (concepts with conflicting tags or negative relationship edges)

**Output:** ReasoningResult { keyConcepts[], relationships[], inferredInsights[], contradictions[], bridgingConcepts[], conceptClusters[][], confidence 0..1 }

**Merge:** Union of key concepts, insights, contradictions from all three strategies. Confidence = weighted average.

### 5.13 FeedbackProcessor

**Purpose:** Self-improving cognitive feedback loop after each reasoning cycle.

**Actions:**
1. Store reasoning trace as markdown in `agent-memory/reasoning/`
2. Reinforce concept weights based on reasoning quality (used concepts +0.02 confidence, insightful concepts +0.03)
3. Track insight frequency for cumulative learning
4. Detect unstable relationships (contradictions that recur)
5. Strategy outcome tracking (which reasoning strategy produced the best results)
6. Periodic policy updates (every 10 cycles)

**Usage tracking:** Maintains Maps of conceptUsageCount and insightFrequency across cycles. These feed into ConceptEvolver as usage signals.

### 5.14 ConceptEvolver

**Purpose:** Lightweight concept evolution engine. Runs every ~20 interactions.

**Merge detection:** Two concepts are merge candidates if:
- Shared episodes ratio ≥ 70%, OR
- Strong edge (weight ≥ 0.7) between them in the graph
- At least 2 co-occurrences

**Split detection:** A concept has conflicting relationships if its `related[]` concepts belong to different clusters with minimal overlap.

**Decay:** Concepts not used (not in usageCounts) for ≥7 days get -0.05 confidence. Floor: 0.15.

**Application:** High-confidence merges (≥85% similarity) auto-applied. Splits are soft-annotated only. Decay applied in batch.

### 5.15 DriftController

**Purpose:** Global cognitive stability governor. Pure policy computation, no I/O.

**Policy fields:** conceptPreferences (domain→weight), reasoningStrategyWeights (graphTraversal/patternMatching/abstraction), conceptStabilityPreference, explorationRate, compressionThreshold.

**Operations:**
- `reinforceDomain(tag, amount)` — boost domain preference
- `suppressDomain(tag, amount)` — reduce domain preference
- `adjustStrategyWeight(strategy, delta)` — ±0.05 clamped
- `adaptExplorationRate(conceptCount)` — more concepts → less exploration
- `enforceBalance()` — if spread > 0.6, dampen max + boost min
- `detectCompressionSignals()` — 4 signal types
- `computeHealth()` — composite score from confidence + stability + signals

**Clamp ranges:** conceptPreferences [0.1, 1.0], strategyWeights [0.1, 1.0], explorationRate [0.05, 0.5], compressionThreshold [0.4, 0.9].

### 5.16 ToolDecisionPolicy

**Purpose:** LLM-based autonomous tool usage decision. Independent of keyword router.

**Decision prompt:** Contains available tools (with descriptions), available skills, decision rules (skill > tool > none), current context (wiki + concept + episodic), user query, strict JSON output format.

**Decision flow:**
1. Build prompt from context
2. Call LLM with temperature=0.1, max_tokens=256
3. Parse JSON response (3-layer tolerance: direct parse → regex extraction → conservative fallback)
4. Return ToolDecisionResult with fallbackUsed flag

**Fallback heuristics:**
- URLs or "search" keywords → web_search
- Date mentions → get_todos
- Todo keywords → add_todos
- Otherwise → no tool

### 5.17 SkillRegistry

**Purpose:** Central registry for privileged system capabilities.

**Interface:**
```
Skill {
  name: string
  description: string
  permissions: "safe" | "privileged"
  execute: async (args: dict, context: SkillContext) => SkillResult
}
```

**Registered skills (2):**
1. `get_current_location` — Browser Geolocation API, 10s timeout, 5min cache
2. `read_local_file` — 6-layer security: path traversal, absolute paths, extension whitelist (.md/.txt/.json), system path blocked, file size limit (500KB), ENOENT handling

**Operations:** register(), has(), get(), getSkillNames(), getAll(), execute(), getExecutionLog(), clearLog().

**Permissions:** "safe" = no user approval needed, "privileged" = requires user permission before execution.

### 5.18 VectorWikiStore

**Purpose:** TF-IDF vectorization + cosine similarity semantic search. Works entirely offline.

**Algorithm:**
1. Tokenize document → remove stop words → compute term frequency per doc
2. Compute IDF per term: `log(N / df)` where N = total docs, df = document frequency
3. Build sparse TF-IDF vectors per document
4. On search: compute cosine similarity between query vector and all doc vectors
5. Apply RAG feedback weights: score *= (1 - downweightFactor) * (1 + answerImpactScore * 0.2)
6. Return top-K results sorted by adjusted score

**Feedback integration:**
- `applyFeedback(path, delta)` — adjust document weights
- `getNegativeSignals()` — return docs with downweightFactor > 0.1
- Serialize/deserialize for persistence

### 5.19 RagFeedback

**Purpose:** Retrieval quality feedback loop.

**Operations:**
- `recordRetrieval(record)` — record which docs were retrieved vs actually used
- Updates document weights: used docs +0.05 relevance, unused -0.02
- Query clustering: group similar queries by keyword signature, track per-cluster success rate
- Downweight: after 3+ negative signals, apply cumulative `DOWNWEIGHT_FACTOR=0.15` (never below 0.1)
- 3-confirmation gate: no action without 3+ signals

### 5.20 StateMutationEngine

**Purpose:** Authoritative validator and applier for all cognitive state changes.

**Mutation types (7):**
1. `concept_update` — confidence/importance delta (±0.05 clamped)
2. `concept_merge` — source → target merge
3. `concept_decay` — confidence reduction
4. `memory_write` — episodic entry write
5. `policy_update` — domain/strategy weight update
6. `reasoning_trace` — reasoning trace storage
7. `relationship_mark` — concept relationship annotation

**Validation:** Each mutation type has a validate() check. Invalid mutations are rejected with error message. Clamp enforced at engine level.

**Priority order:** policy_update(1) → concept_merge(2) → concept_update(3) → concept_decay(4) → memory_write(5) → reasoning_trace(6) → relationship_mark(7).

### 5.21 MutationQueue

**Purpose:** Buffers mutations within a single interaction cycle, flushes batch to engine.

**Operations:**
- `add(mutation)` / `addBatch(mutations)`
- `resolve()` — deduplicate (merge identical concept_updates), sort by priority
- `flush(engine)` — resolve + apply batch + clear queue
- `newCycle()` — start fresh cycle with new cycle ID
- `snapshot()` — audit trail

**Deduplication:** Multiple concept_update mutations for the same conceptName are merged (deltas accumulated, clamped to ±0.05). Multiple policy_update mutations are merged.

---

## 6. Data Model Reference

### 6.1 RouterResult
```
{
  tool: str            # selected tool name
  confidence: float    # 0..1 match confidence
  reason: str          # human-readable reason
}
```

### 6.2 VectorSearchResult
```
{
  content: str         # document content snippet
  sourcePath: str      # file path in vault
  score: float         # cosine similarity 0..1
  relevanceScore: float     # RAG feedback relevance
  answerImpactScore: float  # RAG feedback impact
  downweightFactor: float   # cumulative downweight
}
```

### 6.3 EpisodicEntry
```
{
  id: str              # "ep-{timestamp}-{random}"
  timestamp: int       # unix ms
  type: enum           # event|goal|decision|milestone|question
  summary: str         # short description
  detail: str          # full context
  importance: float    # 0..1
  tags: list[str]
  relatedFiles: list[str]
  importanceScore: float    # evolution field
  usageFrequency: int       # evolution field
  lastAccessTime: int       # evolution field
  decayScore: float         # evolution field
  usefulnessScore: float    # evolution field
  markedForRemoval: bool    # evolution field
}
```

### 6.4 UserProfileData
```
{
  name, preferredName, role, timezone, language: str
  interests, expertise, workHabits, activeProjects, commonTools: list[str]
  responseStyle: "concise"|"detailed"|"casual"
  preferredFormat: "bullet"|"paragraph"|"mixed"
  currentFocus, longTermGoals: list[str]
  lastUpdated: int
  confidenceScores: dict[str, float]  # attr → confidence
}
```

### 6.5 ToolUsageRecord
```
{
  toolName: str
  callCount, successCount, failureCount: int
  topQueryPatterns: list[str]
  patternCounts: dict[str, int]
  avgResponseQuality, avgLatencyMs: float
  firstUsed, lastUsed: int
  contextEffectiveness: dict[str, {count, avgQuality}]
}
```

### 6.6 ToolDecision
```
{
  use_tool: bool
  tool_name: str | None
  use_skill: bool
  skill_name: str | None
  confidence: float
  reason: str
  query_rewrite: str | None
}
```

### 6.7 ReasoningResult
```
{
  keyConcepts: list[str]
  relationships: list[str]     # "A → relates_to → B"
  inferredInsights: list[str]
  contradictions: list[str]
  bridgingConcepts: list[str]
  conceptClusters: list[list[str]]
  confidence: float
}
```

### 6.8 CognitivePolicy
```
{
  conceptPreferences: dict[str, float]
  reasoningStrategyWeights: {graphTraversal, patternMatching, abstraction}
  conceptStabilityPreference: float
  explorationRate: float
  compressionThreshold: float
  lastUpdated: int
  version: int
}
```

### 6.9 StateMutation (Union Type)
7 variants: concept_update, concept_merge, concept_decay, memory_write, policy_update, reasoning_trace, relationship_mark. Each has a `type` discriminator and a `payload` with type-specific fields.

### 6.10 CognitiveState (SSOT Snapshot)
```
{
  memory: {episodicCount, episodicActive, workingMemorySize, profileFields, profileInitialized}
  concepts: {conceptCount, avgConfidence, totalEdges, domainsTracked}
  reasoning: {lastReasoningConfidence, keyConceptsUsed, lastQuery, reasoningCyclesRun}
  feedback: {tracesStored, conceptsReinforced, insightsReinforced, contradictionsDetected, policyUpdates}
  policy: {domainPreferences, strategyWeights, explorationRate, compressionThreshold, version}
  version: int
  lastUpdated: int
}
```

### 6.11 ConceptGraph
```
{
  nodes: dict[str, ConceptGraphNode]  # slug → node
  edges: list[ConceptGraphEdge]
}

ConceptGraphNode: {id, name, slug, confidence, sourceEpisodes[], related[], tags[], degree}
ConceptGraphEdge: {from, to, weight, type: "related"|"shared-episode"|"tag-overlap"}
```

### 6.12 ExtractedConcept
```
{
  name: str           # "Memory System"
  slug: str           # "memory-system"
  confidence: float   # 0..1
  sourceTerms: list[str]
}
```

### 6.13 ScoredMemory (Evolution)
```
{
  id, importanceScore, usageFrequency, lastAccessTime, decayScore, usefulnessScore
  markedForRemoval, content, tags
}
```

---

## 7. Memory System

### 7.1 Working Memory
- **Type:** Short-term, in-memory only
- **Capacity:** 20 messages
- **Update:** push() on every user and assistant message
- **Query:** getLast(n), getByRole(role), getRecentContext(maxTokens)
- **Retention:** FIFO, oldest messages dropped when capacity exceeded
- **Persistence:** None — lost on restart

### 7.2 Episodic Memory
- **Type:** Long-term, persisted
- **Capacity:** 200 entries
- **Update:** MemoryWriter.analyze() → commit() after each interaction
- **Query:** search(query, topK) with keyword + tag + recency + usefulness scoring
- **Retention:** Pruning removes lowest composite-score entries first (marked > low importance+old)
- **Decay:** Exponential decay with usage damping. `decayScore = importanceScore × exp(-0.03 × (1 - usageFreq × 0.6) × cycles)`
- **Consolidation:** New entries compared against existing. Jaccard similarity > 0.85 → merge (reinforce existing, skip new)
- **Persistence:** JSON primary (`episodic.json`), Markdown mirror (`episodes/*.md`)

### 7.3 Semantic Memory (Concepts)
- **Type:** Long-term, persisted
- **Update:** ConceptExtractor runs on each new episode
- **Query:** Loaded in bulk for concept reasoning (buildConceptReasoning)
- **Retention:** Evolution-driven: merge (similar concepts), split (conflicting), decay (unused)
- **Persistence:** Markdown files in `concepts/*.md` with YAML frontmatter

### 7.4 Profile Memory
- **Type:** Long-term, persisted
- **Update:** MemoryWriter.analyzeProfile() regex-based extraction
- **Query:** formatForContext() injected into system prompt
- **Persistence:** JSON primary (`profile.json`), Markdown mirror (`profile.md`)

### 7.5 Tool Memory
- **Type:** Long-term, persisted
- **Update:** recordCall() on every tool execution
- **Query:** getSuccessRate, getEffectiveness, suggestAlternate
- **Persistence:** JSON (`tool_stats.json`)

### 7.6 State Memory (Cognitive Policy)
- **Type:** Long-term, persisted
- **Update:** FeedbackProcessor + DriftController periodically
- **Persistence:** JSON (`cognitive_policy.json`)

---

## 8. Reasoning System

### Concept Extraction Pipeline
```
Episode content (markdown)
  → extractFromHeadings()     — # headings → +0.35 confidence
  → extractFromBigrams()      — Chinese bigrams → ×0.3 weight
  → extractFromTrigrams()     — Chinese trigrams → ×0.5 weight
  → extractFromEnglishTerms() — CamelCase, snake_case, 2-word phrases → ×0.4 weight
  → matchExisting()           — boost +0.2 if matches known concept
  → rankAndFilter()           — min confidence 0.25, max 6 concepts
  → deduplicate()             — remove subset/similar concepts
  → ExtractedConcept[]
```

### Concept Graph Construction
```
markdownStore.loadConcepts() → ConceptData[]
  → buildFull() → ConceptGraph {nodes: Map<slug, Node>, edges: Edge[]}
    → Create nodes from concept data
    → Edge type 1: explicit related[] links (weight 0.8)
    → Edge type 2: shared episodes (weight = shared/max(2, min_sources))
    → Edge type 3: tag overlap (weight = shared_tags/max_tags)
    → Compute degree per node

  → buildSubgraph(fullGraph, seedSlugs) → ConceptSubgraph
    → 1-hop expansion from seed concepts
    → Collect all edges among seed + neighbor nodes
    → Identify central concepts (highest subgraph degree)
```

### Reasoning Engine
```
query + subgraph + fullGraph
  → Strategy 1 (Graph Traversal):
    - High-degree nodes → key concepts
    - Nodes connecting separate clusters → bridging concepts
    - Edge labels → relationships
  → Strategy 2 (Pattern Matching):
    - Query terms co-occurring with concepts → key concepts
    - Frequent co-occurrence without explicit edges → inferred insights
    - Contradictory co-occurrence → contradictions
  → Strategy 3 (Abstraction):
    - Tightly-connected node groups → concept clusters
    - Cluster themes → inferred insights
    - Conflicting cluster membership → contradictions
  → Merge results (union of key concepts + insights + contradictions)
  → Weighted confidence: 0.4 × traversal + 0.3 × pattern + 0.3 × abstraction
```

### How Reasoning Affects Generation
```
ReasoningResult
  → formatReasoningContext()
    → "### 相关概念" (key concepts)
    → "### 概念关系" (relationships, max 8)
    → "### 推理洞察" (insights, max 5)
    → "### 桥接概念" (bridging concepts)
    → "### 潜在矛盾" (contradictions, max 3)
  → Injected into system prompt
  → LLM instructed to: "优先根据概念推理上下文中的洞察和关系来组织回答"
```

---

## 9. Tool System

### Current Architecture (CRITICAL FLAW)

Tools are defined as a static `AGENT_TOOLS` array in the orchestrator. Execution is a switch/case block (`executeToolLocal()`). Adding a tool requires modifying 5 locations:
1. AGENT_TOOLS array definition
2. executeToolLocal switch/case
3. availableTools list for ToolDecisionPolicy context
4. Tool description in buildDecisionPrompt (tool_decision_policy.ts)
5. Proactive args parsing in process()

### Tool Definitions (OpenAI function-calling schema format, though never sent to API)
Each tool has: name, description, parameters (JSON Schema).

### Tool Execution Flow
```
1. routeTool() → fast keyword-based tool selection
2. ToolDecisionPolicy.decide() → LLM-based tool selection (separate call)
3. If tool selected → build args from query_rewrite → executeToolLocal()
4. executeToolLocal() switch/case:
   - get_current_time → Date object → JSON
   - get_todos → filter by date/status/priority/search → JSON
   - get_todo_stats → aggregate stats → JSON
   - add_todos → validate date format → call config.addTodo → JSON
   - web_search → Bing HTML scrape → DuckDuckGo fallback → JSON
   - list_wiki_files → vault.getFiles() filtered by wiki folder → JSON
   - read_wiki_file → path traversal check → vault.read() → JSON
   - write_wiki_file → path check + .md only + 100KB limit → vault.create/modify → rebuild index
   - delete_wiki_file → path check + protect critical files → vault.trash() → rebuild index
   - search_wiki → full text search across wiki files → JSON
5. Result injected into system prompt
```

### Current Limitations
- No Tool interface/abstract class
- No registry pattern
- No provider abstraction (web search is HTML scraping)
- No retry on failure
- No result ranking/merging
- No parallel execution
- Hardcoded in orchestrator (1500+ lines)

---

## 10. Skill System

### Skill Interface
```
Skill {
  name: str              # unique identifier
  description: str       # human-readable
  permissions: enum      # "safe" | "privileged"
  execute: async Callable[[dict, SkillContext], SkillResult]
}
```

### Skill Lifecycle
```
1. Registration: registry.register(skill) — at initialization
2. Decision: ToolDecisionPolicy decides if skill is needed
3. Execution: registry.execute(name, args, context)
   - Validates skill exists
   - Logs execution record (name, args, result, latency, timestamp)
   - Returns SkillResult {success, data, error?}
4. Result injection: Success result inserted into system prompt
```

### Relationship: Skills vs Tools
- **Skills** = privileged system capabilities (file I/O, location, OS access). Require permission validation.
- **Tools** = external world interactions (web search, todos). No special permissions.
- Skills have a proper interface + registry. Tools do not. This is an architectural inconsistency.

---

## 11. Search System

### Current Implementation
Search is a single `web_search` tool, hardcoded as a switch/case branch in the orchestrator.

### Search Flow
```
1. ToolDecisionPolicy selects web_search
2. executeToolLocal("web_search", {query, num_results})
3. Strategy 1: Bing HTML scrape
   - URL: https://www.bing.com/search?q={query}&setlang=zh-cn
   - Parse: regex <li class="b_algo"> blocks
   - Extract: title (<h2><a>), URL (href), snippet (<p>)
   - Return: JSON with results[]
4. Strategy 2 (fallback): DuckDuckGo HTML
   - URL: https://html.duckduckgo.com/html/?q={query}
   - Parse: regex result__a + result__snippet patterns
   - Return: JSON with results[]
5. Strategy 3 (fallback): Empty results with message
```

### Limitations
- No provider abstraction — each search source would be another switch/case branch
- No result merging/dedup across providers
- No ranking across providers
- HTML scraping is fragile (depends on page structure)
- No API-based providers (would need separate implementation)

---

## 12. Evolution System

### Memory Evolution (every 10 interactions)

**Decay:**
```
effectiveRate = 0.03 × (1 - usageFrequency × 0.6)
decayScore = importanceScore × e^(-effectiveRate × cyclesSinceLastAccess)
If decayScore < 0.25 AND usageFrequency == 0 AND cycles >= 14:
  markedForRemoval = true
```

**Reinforcement (5 signal types):**
- `access`: markAccessed() → decayScore = 1.0, markedForRemoval = false
- `reuse`: reinforce(id, 0.03) → importanceScore += 0.03
- `positive_feedback`: reinforce(id, 0.05) → importanceScore += 0.05
- `negative_feedback`: reinforce(id, -0.02) → importanceScore -= 0.02
- `correction`: reinforce(id, -0.05) → importanceScore -= 0.05

**Consolidation (merge):**
```
Jaccard similarity between new entry content and existing entries:
  If similarity > 0.85 → merge: reinforce(target, 0.02), skip new
  Uses bigram overlap for Chinese text, word overlap for English
```

### Concept Evolution (every 20 interactions)

**Merge candidates:**
```
For each pair of concepts:
  sharedEpisodes = intersection(sourceEpisodes)
  If |sharedEpisodes| >= 2 AND |sharedEpisodes| / min(|a.sources|, |b.sources|) >= 0.7:
    MergeCandidate with similarity score
  OR if there's a strong edge (weight >= 0.7) between them
```

**Split detection:**
```
For each concept:
  Group related[] concepts by tag clusters
  If >= 2 conflicting groups (minimal overlap):
    SplitCandidate
```

**Decay:**
```
For each concept not in usageCounts and not accessed in 7+ days:
  Reduce confidence by 0.05
  Clamp floor: 0.15
```

### Drift Control
```
enforceBalance():
  max_pref - min_pref > 0.6:
    max -= 0.05
    min += 0.03

adaptExplorationRate(conceptCount):
  > 20 concepts: rate = max(0.05, 0.3 - count × 0.01)
  < 5 concepts:  rate = 0.4
  else:          rate = 0.2

detectCompressionSignals():
  Low-confidence: low_conf_ratio > compression_threshold
  Redundant cluster: tag group >= 4 concepts with low episode diversity
  High-entropy: > 15 concepts with avg_conf < 0.5
  Unstable relationships: >= 3
```

### Mutation System
```
All state changes go through:
  MutationQueue.add(mutation)
    → deduplicate (merge same-concept updates)
    → sort by priority (policy > concept_merge > concept_update > ...)
    → flush(engine)
      → engine.validate() each mutation
      → engine.apply() each mutation (with ±0.05 clamp)
      → return {applied, rejected, errors}
```

---

## 13. Storage Architecture

### Persistence Strategy
- **Primary:** JSON files in wiki/agent/memory/ directory
- **Mirror:** Markdown files in wiki/agent/memory/ subdirectories
- **Write policy:** JSON always written (source of truth), Markdown best-effort (may fail silently)

### File Inventory
```
{wikiFolder}/agent/memory/
  episodic.json          — EpisodicMemory serialized entries
  profile.json           — UserProfile serialized data
  tool_stats.json        — ToolMemory serialized records
  vector_index.json      — VectorWikiStore serialized TF-IDF index
  router_telemetry.json  — RouterTelemetry serialized metrics
  rag_feedback.json      — RagFeedback serialized state
  episodes/              — One .md per episodic entry (YAML frontmatter)
  concepts/              — One .md per concept (YAML frontmatter)
  reasoning/             — Reasoning trace markdown files
  policy/
    cognitive_policy.json — DriftController serialized policy
  profile.md             — User profile in markdown
  INDEX.md               — Auto-generated directory
```

### Serialization
- JSON: All stores implement `serialize(): str` and `deserialize(json: str): void`
- Markdown: YAML frontmatter generated by MarkdownMemoryStore helpers
- Vector index: Serialized as JSON with vocabulary, IDF values, and document vectors

### Recovery
- On initialize(): load all JSON files → fallback to Markdown if JSON empty → use defaults if both empty
- Vector index: rebuilt from scratch if serialized version is missing or corrupt
- Backward compatibility: deserialize applies defaults for missing evolution fields

---

## 14. Hidden Logic

### Implicit Assumptions
1. The vault (file system) is always available
2. The LLM API endpoint is OpenAI-compatible (`/chat/completions`)
3. DeepSeek does NOT support native function calling (tools disabled)
4. Chinese is the primary language (stop words, bigram extraction, regex patterns)
5. Timezone is UTC+8 (Asia/Shanghai default)
6. System prompt is truncated at 8000 characters (model context window guard)

### Hardcoded Rules
1. `AGENT_TOOLS` array — tool definitions hardcoded in orchestrator
2. `availableTools` list — manually maintained, must match AGENT_TOOLS
3. `buildDecisionPrompt()` — tool descriptions hardcoded in tool_decision_policy.ts
4. Profile extraction patterns — regex-based, not configurable
5. Memory importance thresholds — hardcoded in MemoryWriter
6. Evolution cycle intervals — 10 and 20, hardcoded
7. Health check interval — 15, hardcoded
8. LLM timeout — 60s, hardcoded
9. Sanitization max input — 4000 chars, hardcoded
10. System prompt max chars — 8000, hardcoded

### Magic Numbers
- `±0.05` — clamp delta for all learning updates
- `3` — minimum confirmations before policy changes
- `0.3` — low confidence threshold for memory isolation
- `0.85` — consolidation similarity threshold
- `0.7` — merge similarity threshold for concepts
- `0.25` — decay threshold for marking removal
- `14` — cycles before marking for removal
- `7` — days before concept decay
- `0.15` — concept confidence floor
- `0.1` — minimum tool adaptive threshold
- `0.6` — maximum tool adaptive threshold
- `0.03` — base strength in force-directed graph layout
- `0.6` — usage damping factor in decay formula

### Fallback Logic
1. ToolDecisionPolicy: JSON parse failure → regex extraction → conservative heuristic fallback
2. Web search: Bing → DuckDuckGo → empty results
3. Memory deserialization: JSON parse failure → empty state
4. Markdown write: any failure → silent skip (best-effort)
5. Concept reasoning: any exception → empty reasoning result
6. Evolution: any exception → skip cycle (best-effort)
7. LLM call: timeout/error → consecutive error counter, graceful degradation message

### Default Behavior
1. Empty profile → formatForContext() returns "" (not injected)
2. No concepts → concept reasoning returns empty string
3. No wiki files → vector search returns empty
4. No router telemetry → base thresholds used
5. No policy file → DEFAULT_POLICY used

---

## 15. Algorithm Reference

### 15.1 Router Scoring
```
function routeTool(query, telemetry):
  best_tool = null
  best_score = 0

  for each (tool, pattern) in TOOL_PATTERNS:
    score = 0
    for each keyword in pattern.keywords:
      if query contains keyword:
        score += 1
        if keyword in pattern.exclusives:
          score += 3  # high-confidence signal

    for each regex in pattern.patterns:
      if regex matches query:
        score += 2

    score *= pattern.weight

    # Apply telemetry adjustment
    threshold = telemetry.getAdaptiveThreshold(tool)  # default 0.2
    if score >= threshold and score > best_score:
      best_score = score
      best_tool = tool

  if best_tool == null:
    return ("memory_search", 0.3, "no match")

  confidence = min(1.0, best_score / (pattern.weight * 5))
  return (best_tool, confidence, reason)

TOOL_PATTERNS = {
  "add_todos":      {weight: 1.0,  keywords: ["添加待办","安排","计划"...], patterns: [/添加.*待办/, ...]},
  "get_todos":      {weight: 0.9,  keywords: ["待办","任务列表","进度"...], patterns: [/查看.*待办/, ...]},
  "get_current_time": {weight: 0.85, keywords: ["几点","日期","时间"...], patterns: [/现在.*几点/, ...]},
  "web_search":     {weight: 0.7,  keywords: ["搜索","查一下","最新"...], patterns: [/搜索.*一下/, ...]},
  "wiki_search":    {weight: 0.75, keywords: ["笔记","知识库","我记得"...], patterns: [/笔记.*有/, ...]},
  "memory_search":  {weight: 0.6,  keywords: ["记得","回忆","之前"...], patterns: [/你还记得/, ...]},
}
```

### 15.2 Memory Retrieval
```
function retrieveMemory(query, route):
  wikiResults = vectorStore.search(query, limit=3)  // TF-IDF cosine
  if wikiResults: apply RAG feedback weights

  episodicContext = ""
  if route.tool == "memory_search" or route.confidence < 0.7:
    episodicEntries = episodicMemory.search(query, topK=5)
    episodicContext = episodicMemory.formatForContext(maxEntries=5)

  profileContext = userProfile.formatForContext()

  conceptReasoning = buildConceptReasoning(query)
    // see Section 15.3

  return {wikiResults, episodicContext, profileContext, conceptReasoning}
```

### 15.3 Concept Reasoning
```
function buildConceptReasoning(query):
  concepts = markdownStore.loadConcepts()
  if len(concepts) < 2: return ""

  fullGraph = graphBuilder.buildFull(concepts)

  // Policy-aware seed selection
  policy = driftController.currentPolicy
  for each concept:
    score = query term match in (name + slug + tags)
          + policy preference bias for concept domain tags
          + stability preference for high-confidence concepts
          + exploration bonus for low-episode concepts
  seeds = top 5 scored concepts
  if no matches: seeds = top 3 most-referenced concepts

  subgraph = graphBuilder.buildSubgraph(fullGraph, seeds)  // 1-hop

  reasoning = reasoner.reason(query, subgraph, fullGraph)
    // 3 strategies: traversal, pattern, abstraction

  return formatReasoningContext(reasoning)
```

### 15.4 System Prompt Assembly
```
function buildSystemPrompt(memory):
  timeContext = format current time in Chinese

  sections = [timeContext]

  if profileContext:
    sections.append(profileContext)

  if wikiResults:
    wikiSection = format wiki results as "- [sourcePath] (score%)\n  content"
    sections.append(wikiSection)

  if episodicContext:
    sections.append(episodicContext)

  if conceptReasoning:
    sections.append(conceptReasoning)

  rules = [
    "优先根据概念推理组织回答",
    "说明概念之间的关联",
    "基于知识库内容回答",
    "注明来源",
    "知识库没有时可以基于常识但要说明",
    "使用可用工具获取实时数据",
    "不编造不存在的内容",
    "绝对禁止 Markdown 表格",
    "用列表代替表格",
    "用 **键**: 值 代替键值对",
  ]

  prompt = sections.join("\n") + rules

  if prompt.length > 8000:
    truncate wiki/episodic from middle, keep rules at end

  return prompt
```

### 15.5 Memory Writer Analysis
```
function analyze(interaction):
  decisions = []

  // 1. Profile analysis
  profileDecisions = analyzeProfile(interaction)
    // regex patterns:
    // "我是/I am/I'm" → name
    // "我(在)?做/从事" → role
    // "我喜欢/我对.*感兴趣" → interests
    // "我(在)?用" → commonTools
    // "我的.*项目" → activeProjects
  decisions.extend(profileDecisions)

  // 2. Episodic analysis
  if contains keywords ("目标","计划","决定","里程碑"):
    decisions.append({type: "episodic", importance: 0.6-0.9, action: "append"})

  // 3. Semantic analysis
  if contains factual statements and is substantial:
    decisions.append({type: "semantic", importance: 0.4, action: "append"})

  // 4. Tool usage (always)
  decisions.append({type: "tool", importance: 0.3, action: "append"})

  return decisions

function commit(decisions, interaction):
  for each decision:
    if episodic and action == "append":
      existing = episodicMemory.getActiveEntries()
      scoredExisting = map to ScoredMemory
      newScored = decision as ScoredMemory
      consolidation = consolidate(newScored, scoredExisting)
      if consolidation.merged:
        episodicMemory.reinforce(targetId, 0.02)
      else:
        newEntry = episodicMemory.add({type, summary, detail, importance, tags})
        if mutationQueue:
          mutationQueue.add(type="memory_write", payload={entry: newEntry})
        else:
          markdownStore.writeEpisode(newEntry)  // best-effort

        // Extract concepts from new episode
        concepts = conceptExtractor.extract(episodeContent, existingConcepts)
        for each concept:
          if confidence >= 0.4:
            markdownStore.upsertConcept(concept)
            create episode↔concept wikilinks

    if profile and action != "ignore":
      userProfile.set(targetField, detectedValue, confidence)
```

### 15.6 TF-IDF Vectorization
```
class VectorWikiStore:
  function build(documents):
    vocabulary = {}
    for each doc:
      tokens = tokenize(doc.content)  // remove stop words, CJK bigrams
      for each token:
        if token not in vocabulary:
          vocabulary[token] = len(vocabulary)

    idf = [0] * len(vocabulary)
    docFreq = [0] * len(vocabulary)
    for each doc:
      uniqueTokens = set(tokenize(doc.content))
      for each token in uniqueTokens:
        docFreq[vocabulary[token]] += 1

    for i in range(len(vocabulary)):
      idf[i] = log(len(documents) / (1 + docFreq[i]))

    for each doc:
      tf = computeTF(doc)
      vector = []
      for i, token in enumerate(vocabulary):
        vector.append(tf.get(token, 0) * idf[i])

  function search(query, topK):
    queryTokens = tokenize(query)
    queryTF = computeTermFrequency(queryTokens)
    queryVector = [queryTF.get(token, 0) * idf[idx] for token, idx in vocabulary]

    scored = []
    for each docVector in documents:
      cosine = dot(queryVector, docVector) / (norm(queryVector) * norm(docVector))
      // Apply RAG feedback adjustment
      feedback = docFeedback.get(doc.path)
      if feedback:
        cosine *= (1 - feedback.downweightFactor) * (1 + feedback.answerImpactScore * 0.2)
      scored.append({content, sourcePath, score: cosine})

    scored.sort(by=score, descending=True)
    return scored[:topK]
```

### 15.7 Evolution: Memory Decay
```
function applyDecay(episodicEntries, cyclesSinceLastAccess):
  decayed = 0
  for each entry:
    if entry.markedForRemoval: skip
    hoursSinceAccess = (now - entry.lastAccessTime) / (1000 * 60 * 60)
    effectiveRate = 0.03 * (1 - entry.usageFrequency * 0.6)
    entry.decayScore = round(entry.importanceScore * exp(-effectiveRate * hoursSinceAccess), 4)
    if entry.decayScore < 0.25 AND entry.usageFrequency == 0 AND hoursSinceAccess >= 14:
      entry.markedForRemoval = true
      decayed += 1
  return decayed
```

### 15.8 Evolution: Concept Merge Detection
```
function detectMerges(concepts):
  candidates = []
  for i in range(len(concepts)):
    for j in range(i+1, len(concepts)):
      a, b = concepts[i], concepts[j]
      shared = intersect(a.sourceEpisodes, b.sourceEpisodes)
      if len(shared) >= 2:
        ratio = len(shared) / max(1, min(len(a.sourceEpisodes), len(b.sourceEpisodes)))
        if ratio >= 0.7:
          candidates.append({source: a, target: b, similarity: ratio, sharedEpisodes: shared})

      // Also check for strong edges
      edge = findEdge(a.slug, b.slug)
      if edge and edge.weight >= 0.7:
        candidates.append({source: a, target: b, similarity: edge.weight, ...})

  return candidates
```

### 15.9 Drift Control: Compression Signals
```
function detectCompressionSignals(concepts, conceptCount, unstableRelCount):
  signals = []

  // 1. Low-confidence concept accumulation
  lowConf = filter(concepts, c => c.confidence < 0.3)
  if len(lowConf) / max(1, len(concepts)) > policy.compressionThreshold:
    signals.append({type: "low-confidence", severity: lowConfRatio, ...})

  // 2. Redundant clusters
  tagGroups = groupBy(concepts, tags)
  for tag, group in tagGroups:
    if len(group) >= 4:
      allEpisodes = union of group.sourceEpisodes
      redundancyRatio = len(allEpisodes) / max(1, len(group) * 2)
      if redundancyRatio < 0.5:
        signals.append({type: "redundant-cluster", ...})

  // 3. High entropy
  if conceptCount > 15 and avgConfidence < 0.5:
    signals.append({type: "high-entropy", ...})

  // 4. Unstable relationships
  if unstableRelCount >= 3:
    signals.append({type: "unstable-pattern", ...})

  return signals
```

### 15.10 Concept Extraction: Chinese Bigrams
```
function extractFromBigrams(content, candidates):
  cjkOnly = content filtered to CJK characters only [一-鿿]
  if len(cjkOnly) < 4: return

  bigramFreq = {}
  for i in range(len(cjkOnly) - 1):
    bg = cjkOnly[i:i+2]
    if bg not in stopWords:
      bigramFreq[bg] = bigramFreq.get(bg, 0) + 1

  maxFreq = max(1, max(bigramFreq.values()))
  for bg, freq in bigramFreq:
    if freq < 2: continue
    freqScore = (freq / maxFreq) * 0.3
    addOrUpdate(candidates, normalizeName(bg), freqScore)

  // Trigrams: same pattern, weight 0.5, min freq 2, noise-filtered

  function isNoiseTrigram(tg):
    noisePatterns = [/^[的是在了和就]/, /[的了着过]$/, /^[不太也没很都]/, /^[这可那哪怎]/]
    return any(pattern matches tg)
```

### 15.11 Router Telemetry: Adaptive Threshold
```
function getAdaptiveThreshold(toolName):
  metrics = this.metrics.get(toolName)
  if not metrics:
    return BASE_THRESHOLD  // 0.2

  // Low success → higher threshold (harder to select)
  // High success → lower threshold (easier to select)
  return clamp(BASE_THRESHOLD + (1 - metrics.successRate) * 0.4, 0.1, 0.6)

function updatePolicyWeights():
  for each tool metrics:
    // Improving tools gain weight
    if metrics.recentDecisions[-3:].all succeed:
      metrics.policyWeight = clamp(metrics.policyWeight + 0.02, 0.1, 1.0)
    // Declining tools lose weight (but need 3+ confirmations)
    if metrics.recentDecisions[-3:].all fail and metrics.selectionCount >= 3:
      metrics.policyWeight = clamp(metrics.policyWeight - 0.03, 0.1, 1.0)
```

---

## 16. Python Reconstruction Mapping

| TypeScript Module | Python Package | Python Module | Python Class | Recommendation |
|------------------|----------------|---------------|--------------|----------------|
| `agent_orchestrator.ts` | `agent.orchestration` | `pipeline.py` | `AgentPipeline` | **REDESIGN** — Split into composable pipeline stages |
| `tool_router.ts` | `agent.routing` | `router.py` | `ToolRouter` | KEEP — Clean design |
| `router_telemetry.ts` | `agent.routing` | `telemetry.py` | `RouterTelemetry` | KEEP |
| `vector_wiki_store.ts` | `agent.retrieval` | `tfidf_store.py` | `TfidfVectorStore` | KEEP |
| `rag_feedback.ts` | `agent.retrieval` | `feedback.py` | `RagFeedback` | KEEP |
| `system_evolution.ts` | `agent.evolution` | `scoring.py` | `(pure functions)` | KEEP |
| `memory/working_memory.ts` | `agent.memory` | `working.py` | `WorkingMemory` | KEEP |
| `memory/episodic_memory.ts` | `agent.memory` | `episodic.py` | `EpisodicMemory` | KEEP |
| `memory/user_profile.ts` | `agent.memory` | `profile.py` | `UserProfile` | KEEP |
| `memory/tool_memory.ts` | `agent.memory` | `tool_stats.py` | `ToolMemory` | KEEP |
| `memory/memory_writer.ts` | `agent.memory` | `writer.py` | `MemoryWriter` | **IMPROVE** — Reduce dependency count |
| `memory/memory_store.ts` | `agent.memory` | `store.py` | `MemoryStore` | KEEP — Use Pydantic for YAML |
| `memory/concept_extractor.ts` | `agent.concepts` | `extractor.py` | `ConceptExtractor` | KEEP |
| `reasoning/concept_graph_builder.ts` | `agent.reasoning` | `graph.py` | `ConceptGraphBuilder` | KEEP |
| `reasoning/concept_reasoner.ts` | `agent.reasoning` | `reasoner.py` | `ConceptReasoner` | KEEP |
| `reasoning/feedback_processor.ts` | `agent.reasoning` | `feedback.py` | `FeedbackProcessor` | KEEP |
| `reasoning/concept_evolver.ts` | `agent.evolution` | `concept_evolver.py` | `ConceptEvolver` | KEEP |
| `policy/drift_controller.ts` | `agent.policy` | `controller.py` | `DriftController` | KEEP |
| `tools/tool_decision_policy.ts` | `agent.tools` | `decision.py` | `ToolDecisionPolicy` | **IMPROVE** — Make tool descriptions data-driven |
| `skills/skill_registry.ts` | `agent.skills` | `registry.py` | `SkillRegistry` | KEEP — Model for Tool refactor |
| `skills/get_current_location.ts` | `agent.skills` | `location.py` | `GetLocationSkill` | KEEP |
| `skills/read_local_file.ts` | `agent.skills` | `file_reader.py` | `ReadFileSkill` | KEEP |
| `core/cognitive_state.ts` | `agent.core` | `state.py` | `CognitiveState` (Pydantic) | KEEP — Use Pydantic BaseModel |
| `core/state_mutation_engine.ts` | `agent.core` | `mutation.py` | `StateMutationEngine` | KEEP |
| `core/mutation_queue.ts` | `agent.core` | `queue.py` | `MutationQueue` | KEEP |

### Modules to REDESIGN:
1. **agent_orchestrator.ts → agent.orchestration.pipeline.py** — Split the 1500-line monolith into composable pipeline stages. Each stage is a class implementing a `PipelineStage` interface with `async execute(context: PipelineContext) -> PipelineContext`.

### Modules to IMPROVE:
1. **memory_writer** — Reduce from 6 dependencies to ~3 by introducing a "MemoryStoreFacade" that aggregates the individual stores.
2. **tool_decision_policy** — Make tool descriptions data-driven (loaded from ToolRegistry) rather than hardcoded in `buildDecisionPrompt()`.

### Modules to KEEP as-is:
16 out of 24 modules are architecturally sound and should be ported directly.

---

## 17. Migration Strategy

### Dependency Order (must build in this sequence)

```
Phase 1: Foundation (no dependencies)
  1. agent.core.state          — Pydantic data models (CognitiveState, mutations)
  2. agent.core.mutation        — StateMutationEngine (validation logic)
  3. agent.core.queue           — MutationQueue (buffer logic)
  4. agent.policy.controller    — DriftController (pure computation)

Phase 2: Memory (depends on Phase 1)
  5. agent.memory.working       — WorkingMemory
  6. agent.memory.episodic      — EpisodicMemory
  7. agent.memory.profile       — UserProfile
  8. agent.memory.tool_stats    — ToolMemory
  9. agent.memory.store         — MemoryStore (file I/O)
  10. agent.memory.writer       — MemoryWriter (depends on 5-9)

Phase 3: Concepts & Evolution (depends on Phase 2)
  11. agent.evolution.scoring   — Pure scoring functions
  12. agent.concepts.extractor  — ConceptExtractor
  13. agent.evolution.concept_evolver — ConceptEvolver (depends on 9, 12, 17)

Phase 4: Reasoning (depends on Phase 2)
  14. agent.reasoning.graph     — ConceptGraphBuilder (depends on 9)
  15. agent.reasoning.reasoner  — ConceptReasoner (depends on 14)
  16. agent.reasoning.feedback  — FeedbackProcessor (depends on 9, 3, 7)

Phase 5: Routing & Retrieval (depends on Phase 2)
  17. agent.routing.telemetry   — RouterTelemetry
  18. agent.routing.router      — ToolRouter (depends on 17)
  19. agent.retrieval.tfidf     — TfidfVectorStore
  20. agent.retrieval.feedback  — RagFeedback

Phase 6: Tool System — REDESIGN (depends on nothing in agent)
  21. agent.tools.interface     — Tool abstract base class
  22. agent.tools.registry      — ToolRegistry
  23. agent.tools.decision      — ToolDecisionPolicy (refactored to use registry)

Phase 7: Skills (depends on Phase 6 for interface pattern)
  24. agent.skills.registry     — SkillRegistry
  25. agent.skills.*            — Individual skills

Phase 8: Orchestration (depends on ALL above)
  26. agent.orchestration.pipeline — AgentPipeline (composed from all stages)

Phase 9: Search Framework — NEW (depends on Phase 6)
  27. agent.search.interface    — SearchProvider abstract base class
  28. agent.search.manager      — SearchManager (merge, rank, dedup)
  29. agent.search.providers.*  — Web, Bilibili, GitHub, ArXiv, Local, Obsidian

Phase 10: Storage
  30. agent.storage.manager     — Centralized persistence (depends on all stores)
```

### Priority: Build Phase 1-5 first (proven design), then Phase 6 (Tool Registry redesign), then Phase 8 (pipeline composition).

---

## 18. Python Package Blueprint

```
agent/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── state.py              # Pydantic models: CognitiveState, all sub-states
│   ├── mutation.py           # StateMutation union type, StateMutationEngine
│   └── queue.py              # MutationQueue
│
├── memory/
│   ├── __init__.py
│   ├── working.py            # WorkingMemory
│   ├── episodic.py           # EpisodicMemory + EpisodicEntry
│   ├── profile.py            # UserProfile + UserProfileData
│   ├── tool_stats.py         # ToolMemory + ToolUsageRecord
│   ├── store.py              # MemoryStore (file I/O with YAML frontmatter)
│   └── writer.py             # MemoryWriter
│
├── concepts/
│   ├── __init__.py
│   └── extractor.py          # ConceptExtractor
│
├── reasoning/
│   ├── __init__.py
│   ├── graph.py              # ConceptGraphBuilder
│   └── reasoner.py           # ConceptReasoner
│
├── evolution/
│   ├── __init__.py
│   ├── scoring.py            # Pure functions: computeDecayScore, reinforce, consolidate
│   ├── concept_evolver.py    # ConceptEvolver
│   └── feedback.py           # FeedbackProcessor
│
├── policy/
│   ├── __init__.py
│   └── controller.py         # DriftController + CognitivePolicy
│
├── routing/
│   ├── __init__.py
│   ├── router.py             # ToolRouter
│   └── telemetry.py          # RouterTelemetry
│
├── retrieval/
│   ├── __init__.py
│   ├── tfidf_store.py        # TfidfVectorStore
│   └── feedback.py           # RagFeedback
│
├── tools/                     # REDESIGNED
│   ├── __init__.py
│   ├── interface.py          # Tool abstract base class
│   ├── registry.py           # ToolRegistry (auto-discover + register)
│   ├── decision.py           # ToolDecisionPolicy (refactored)
│   └── builtins/             # Built-in tool implementations
│       ├── __init__.py
│       ├── web_search.py
│       ├── todos.py
│       ├── time.py
│       └── wiki_crud.py
│
├── skills/
│   ├── __init__.py
│   ├── registry.py           # SkillRegistry
│   ├── base.py               # Skill abstract base class
│   ├── location.py           # GetLocationSkill
│   └── file_reader.py        # ReadFileSkill
│
├── search/                    # NEW
│   ├── __init__.py
│   ├── interface.py          # SearchProvider abstract base class
│   ├── manager.py            # SearchManager (orchestrate, merge, rank, dedup)
│   └── providers/
│       ├── __init__.py
│       ├── web.py            # Bing + DuckDuckGo
│       ├── bilibili.py       # Bilibili search API
│       ├── github.py         # GitHub search
│       ├── arxiv.py          # ArXiv API
│       ├── local.py          # Local file search
│       └── obsidian.py       # Obsidian vault search
│
├── orchestration/
│   ├── __init__.py
│   ├── pipeline.py           # AgentPipeline (composable stages)
│   ├── context.py            # PipelineContext (carries state between stages)
│   └── stages/               # Individual pipeline stages
│       ├── __init__.py
│       ├── sanitize.py
│       ├── route.py
│       ├── retrieve.py
│       ├── reason.py
│       ├── decide_tools.py
│       ├── execute_tools.py
│       ├── build_prompt.py
│       ├── call_llm.py
│       ├── persist.py
│       └── evolve.py
│
├── storage/
│   ├── __init__.py
│   └── manager.py            # Centralized persistence manager
│
├── llm/
│   ├── __init__.py
│   ├── client.py             # LLM client (streaming + non-streaming)
│   └── prompts.py            # Prompt templates (data-driven)
│
└── config.py                 # All constants, thresholds, magic numbers
```

### Dependency Rules
- `core/` depends on nothing internal (only Pydantic/stdlib)
- `policy/` depends on nothing internal
- `memory/` depends on `core/`
- `concepts/` depends on `memory/`
- `reasoning/` depends on `concepts/` + `memory/`
- `evolution/` depends on `reasoning/` + `policy/` + `core/`
- `routing/` depends on nothing internal
- `retrieval/` depends on nothing internal (pure computation)
- `tools/` depends on `llm/` (for ToolDecisionPolicy)
- `skills/` depends on nothing internal
- `search/` depends on `tools/interface.py`
- `orchestration/` depends on ALL above (composition root)
- `storage/` depends on `memory/` + `policy/`
- `llm/` depends on nothing internal

---

## 19. Reconstruction Risks

### Modules That Should NOT Be Copied Directly

1. **agent_orchestrator.ts** — The 1500-line God Object should be split into pipeline stages. Direct port would perpetuate the monolith.

2. **executeToolLocal() switch/case** — The hardcoded tool execution must be replaced by ToolRegistry + Tool interface. Direct port would make adding tools require modifying core code forever.

3. **Web search HTML scraping** — The Bing/DuckDuckGo regex-based HTML parsing is fragile. Should use APIs or at minimum be isolated behind a SearchProvider interface so the implementation can be swapped without affecting anything else.

4. **YAML frontmatter serialization** — The TypeScript implementation uses manual string manipulation for YAML. Python should use `pyyaml` or Pydantic's built-in YAML support.

5. **Dual-write JSON + Markdown** — The dual persistence creates eventual consistency risk. Consider single-source-of-truth (SQLite or JSON) with optional Markdown export.

### Design Flaws to Fix

1. **Tool system** — Add Tool interface + ToolRegistry (modeled after Skill system)
2. **Hardcoded constants** — Extract all magic numbers to `config.py`
3. **Monolithic orchestrator** — Decompose into composable pipeline stages
4. **Synchronous evolution** — Run evolution in background, don't block interaction loop
5. **Every-request memory retrieval** — Add selective retrieval: skip for simple greetings

### Complexity to Reduce

1. **Memory writer's 6 dependencies** — Introduce a facade
2. **Dual persistence (JSON + Markdown)** — Simplify to one primary store
3. **AGENT_TOOLS + availableTools + buildDecisionPrompt tool descriptions** — Single source of truth via ToolRegistry

### Architecture to Remain Unchanged

1. **Core SSOT + Mutation system** — Well-designed, port directly
2. **5-layer cognitive stack** — Proven design, keep the layer separation
3. **Concept reasoning (3 strategies)** — Unique and well-implemented
4. **Drift controller** — Clean policy computation
5. **Skill registry pattern** — Extend this pattern to Tools

### Python-Specific Improvements

1. Use `Pydantic BaseModel` for all data models (type safety, serialization, validation)
2. Use `asyncio` for all I/O (LLM calls, file operations, web requests)
3. Use `structlog` for structured logging (audit trail, debugging)
4. Use `pyyaml` for YAML frontmatter (instead of manual string manipulation)
5. Use `httpx` for HTTP client (async, timeout support, streaming)
6. Use `numpy` for TF-IDF vector operations (performance)
7. Use `networkx` for concept graph operations (alternative to custom graph implementation)

---

## 20. Final Recommendations

### Immediate Priorities
1. Port the Core SSOT + Mutation system first (foundation for everything)
2. Port Memory + Reasoning + Evolution (proven design, port directly)
3. **Redesign the Tool system** before porting (add Tool interface + ToolRegistry)
4. Build the new Search Framework (provider abstraction)
5. Compose the pipeline from individual stages (replacing the monolith)

### Architecture Quality (post-redesign target)
- Tool system: 2/10 → 8/10 (Tool interface + Registry)
- Orchestrator: 3/10 → 8/10 (composable pipeline stages)
- Search: 3/10 → 8/10 (provider abstraction)
- Overall: 6.2/10 → **8.0/10**

### Key Design Principle for Python Reconstruction
**The Agent owns the state, not the model.** The LLM is a stateless reasoning engine. All context (memory, concepts, policy, tool results) is assembled by the Agent pipeline and presented to the LLM. The LLM never directly accesses storage, tools, or external systems.

---

*Generated from complete analysis of 22 TypeScript source files in src/agent/. Every behavioral description, algorithm, and data model is derived from the actual implementation, not speculation.*
