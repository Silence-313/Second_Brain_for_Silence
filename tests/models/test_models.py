"""Tests for all Stage 1 Pydantic data models."""

import pytest

from agent.models.concepts import (
    Concept,
    ConceptGraph,
    ConceptGraphEdge,
    ConceptGraphNode,
    ExtractedConcept,
)
from agent.models.events import (
    AgentInitialized,
    ErrorOccurred,
    InputSanitized,
    PipelineEvent,
    ToolExecuted,
)
from agent.models.evolution import (
    ConsolidationResult,
    EvolutionResult,
    MergeCandidate,
    ScoredMemory,
)
from agent.models.memory import (
    Episode,
    MemoryWriteDecision,
    ToolUsageRecord,
    UserProfileData,
    WorkingMemoryEntry,
)
from agent.models.mutations import (
    MUTATION_PRIORITY,
    ConceptDecayMutation,
    ConceptMergeMutation,
    ConceptUpdateMutation,
    MemoryWriteMutation,
    PolicyUpdateMutation,
    ReasoningTraceMutation,
    RelationshipMarkMutation,
    StateMutation,
)
from agent.models.policy import CognitivePolicy, DriftMetrics
from agent.models.reasoning import ReasoningResult, ReasoningTrace
from agent.models.retrieval import DocumentWeight, RetrievalRecord, VectorSearchResult
from agent.models.routing import RouterResult, RoutingRecord, ToolMetrics
from agent.models.search import MergedSearchResult, SearchResult
from agent.models.skills import SkillExecutionRecord, SkillResult
from agent.models.state import CognitiveState, MemoryState, PolicyState
from agent.models.tools import ToolCallRecord, ToolResult

# ── Memory models ──


class TestWorkingMemoryEntry:
    def test_create(self) -> None:
        e = WorkingMemoryEntry(role="user", content="hello")
        assert e.role == "user"
        assert e.content == "hello"

    def test_serialize(self) -> None:
        e = WorkingMemoryEntry(role="user", content="hello")
        j = e.model_dump_json()
        e2 = WorkingMemoryEntry.model_validate_json(j)
        assert e2.content == "hello"


class TestEpisode:
    def test_create_defaults(self) -> None:
        ep = Episode(id="ep-1", type="event", summary="test")
        assert ep.id == "ep-1"
        assert ep.importance == 0.5
        assert ep.decay_score == 1.0
        assert not ep.marked_for_removal

    def test_serialize_roundtrip(self) -> None:
        ep = Episode(
            id="ep-1", type="goal", summary="learn python", importance=0.8, tags=["code", "python"]
        )
        j = ep.model_dump_json()
        ep2 = Episode.model_validate_json(j)
        assert ep2.id == "ep-1"
        assert ep2.tags == ["code", "python"]
        assert ep2.importance == 0.8

    def test_frozen(self) -> None:
        from pydantic import ValidationError

        ep = Episode(id="ep-1", type="event", summary="test")
        with pytest.raises(ValidationError):
            ep.summary = "changed"  # type: ignore[misc]


class TestUserProfileData:
    def test_create_defaults(self) -> None:
        p = UserProfileData()
        assert p.name == ""
        assert p.response_style == "concise"

    def test_with_data(self) -> None:
        p = UserProfileData(
            name="Alice", role="engineer", interests=["coding", "ai"], expertise=["python"]
        )
        assert len(p.interests) == 2
        assert len(p.expertise) == 1

    def test_confidence_scores(self) -> None:
        p = UserProfileData(name="Bob", confidence_scores={"name": 0.9, "role": 0.7})
        assert p.confidence_scores["name"] == 0.9


class TestToolUsageRecord:
    def test_create(self) -> None:
        r = ToolUsageRecord(tool_name="web_search")
        assert r.tool_name == "web_search"
        assert r.call_count == 0
        assert r.success_count == 0


class TestMemoryWriteDecision:
    def test_create(self) -> None:
        d = MemoryWriteDecision(type="episodic", importance=0.7, action="append", reason="test")
        assert d.type == "episodic"
        assert d.importance == 0.7


# ── Concepts models ──


class TestConcept:
    def test_create(self) -> None:
        c = Concept(id="c1", name="Machine Learning", slug="machine-learning")
        assert c.confidence == 0.5
        assert c.tags == []


class TestExtractedConcept:
    def test_create(self) -> None:
        ec = ExtractedConcept(
            name="ML", slug="ml", confidence=0.6, source_terms=["machine", "learning"]
        )
        assert ec.confidence == 0.6
        assert len(ec.source_terms) == 2


class TestConceptGraph:
    def test_empty(self) -> None:
        g = ConceptGraph()
        assert len(g.nodes) == 0
        assert len(g.edges) == 0

    def test_with_nodes(self) -> None:
        node = ConceptGraphNode(id="n1", name="ML", slug="ml")
        g = ConceptGraph(nodes={"ml": node}, edges=[])
        assert g.nodes["ml"].name == "ML"

    def test_edge(self) -> None:
        edge = ConceptGraphEdge(from_slug="ml", to_slug="dl", weight=0.8, type="related")
        assert edge.weight == 0.8
        assert edge.type == "related"


# ── State models ──


class TestCognitiveState:
    def test_default(self) -> None:
        cs = CognitiveState()
        assert cs.version == 0
        assert cs.memory.episodic_count == 0
        assert cs.policy.exploration_rate == 0.2

    def test_serialize(self) -> None:
        cs = CognitiveState(version=1)
        j = cs.model_dump_json()
        cs2 = CognitiveState.model_validate_json(j)
        assert cs2.version == 1


class TestMemoryState:
    def test_default(self) -> None:
        ms = MemoryState()
        assert ms.episodic_count == 0


class TestPolicyState:
    def test_default(self) -> None:
        ps = PolicyState()
        assert ps.exploration_rate == 0.2


# ── Routing models ──


class TestRouterResult:
    def test_create(self) -> None:
        r = RouterResult(tool="web_search", confidence=0.8, reason="test")
        assert r.tool == "web_search"
        assert r.confidence == 0.8


class TestRoutingRecord:
    def test_create(self) -> None:
        r = RoutingRecord(query="hello", selected_tool="memory_search", confidence=0.5)
        assert r.query == "hello"


class TestToolMetrics:
    def test_create(self) -> None:
        tm = ToolMetrics(tool_name="test")
        assert tm.success_rate == 0.5
        assert tm.adaptive_threshold == 0.2


# ── Reasoning models ──


class TestReasoningResult:
    def test_create_defaults(self) -> None:
        r = ReasoningResult()
        assert r.key_concepts == []
        assert r.confidence == 0.5

    def test_with_data(self) -> None:
        r = ReasoningResult(
            key_concepts=["ML", "DL"], confidence=0.8, inferred_insights=["ML is related to DL"]
        )
        assert len(r.key_concepts) == 2


class TestReasoningTrace:
    def test_create(self) -> None:
        t = ReasoningTrace(id="t1", query="what is ML", key_concepts=["ML"], insights=["test"])
        assert t.id == "t1"
        assert len(t.insights) == 1


# ── Evolution models ──


class TestScoredMemory:
    def test_create(self) -> None:
        sm = ScoredMemory(id="ep-1", importance_score=0.7, content="test")
        assert sm.importance_score == 0.7


class TestConsolidationResult:
    def test_create(self) -> None:
        cr = ConsolidationResult(merged=True, target_id="ep-2", similarity=0.9)
        assert cr.merged
        assert cr.similarity == 0.9


class TestMergeCandidate:
    def test_create(self) -> None:
        mc = MergeCandidate(source_slug="ml", target_slug="dl", similarity=0.8)
        assert mc.source_slug == "ml"


class TestEvolutionResult:
    def test_default(self) -> None:
        er = EvolutionResult()
        assert er.merges_applied == 0
        assert er.errors == []


# ── Policy models ──


class TestCognitivePolicy:
    def test_default(self) -> None:
        cp = CognitivePolicy()
        assert cp.exploration_rate == 0.2
        assert cp.compression_threshold == 0.6
        assert "graph_traversal" in cp.reasoning_strategy_weights

    def test_serialize(self) -> None:
        cp = CognitivePolicy(version=3)
        j = cp.model_dump_json()
        cp2 = CognitivePolicy.model_validate_json(j)
        assert cp2.version == 3


class TestDriftMetrics:
    def test_create(self) -> None:
        dm = DriftMetrics(health_score=0.85, confidence_avg=0.7, stability=0.9)
        assert dm.health_score == 0.85


# ── Mutation models ──


class TestStateMutation:
    def test_concept_update(self) -> None:
        m = ConceptUpdateMutation(concept_name="ml", field="confidence", delta=0.03)
        assert m.type == "concept_update"
        assert m.delta == 0.03

    def test_concept_update_clamp(self) -> None:
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ConceptUpdateMutation(concept_name="ml", field="confidence", delta=0.1)

    def test_concept_merge(self) -> None:
        m = ConceptMergeMutation(source_slug="ml", target_slug="dl")
        assert m.type == "concept_merge"

    def test_concept_decay(self) -> None:
        m = ConceptDecayMutation(concept_slug="ml", delta=-0.03)
        assert m.type == "concept_decay"

    def test_memory_write(self) -> None:
        m = MemoryWriteMutation(entry_id="ep-1", entry_type="episodic", payload={"summary": "test"})
        assert m.type == "memory_write"

    def test_policy_update(self) -> None:
        m = PolicyUpdateMutation(field="exploration_rate", value=0.3)
        assert m.type == "policy_update"

    def test_reasoning_trace(self) -> None:
        m = ReasoningTraceMutation(trace_id="t1", query="test")
        assert m.type == "reasoning_trace"

    def test_relationship_mark(self) -> None:
        m = RelationshipMarkMutation(concept_a="ml", concept_b="dl", weight=0.7)
        assert m.type == "relationship_mark"

    def test_discriminated_union(self) -> None:
        from pydantic import TypeAdapter

        m = ConceptUpdateMutation(concept_name="test", field="conf", delta=0.02)
        j = m.model_dump_json()
        adapter = TypeAdapter(StateMutation)
        parsed = adapter.validate_json(j)
        assert parsed.type == "concept_update"

    def test_priority_order(self) -> None:
        assert MUTATION_PRIORITY["policy_update"] == 1
        assert MUTATION_PRIORITY["relationship_mark"] == 7


# ── Retrieval models ──


class TestVectorSearchResult:
    def test_create(self) -> None:
        r = VectorSearchResult(content="test", source_path="/doc.md", score=0.8)
        assert r.score == 0.8


class TestRetrievalRecord:
    def test_create(self) -> None:
        r = RetrievalRecord(query="test", retrieved_docs=["a.md", "b.md"], used_docs=["a.md"])
        assert len(r.retrieved_docs) == 2
        assert len(r.used_docs) == 1


class TestDocumentWeight:
    def test_create(self) -> None:
        dw = DocumentWeight(path="/doc.md")
        assert dw.downweight_factor == 0.0


# ── Search models ──


class TestSearchResult:
    def test_create(self) -> None:
        sr = SearchResult(title="Test", url="https://example.com", snippet="desc")
        assert sr.title == "Test"


class TestMergedSearchResult:
    def test_create(self) -> None:
        msr = MergedSearchResult(query="test", total_results=3)
        assert msr.total_results == 3


# ── Tools/Skills models ──


class TestToolResult:
    def test_success(self) -> None:
        r = ToolResult(success=True, data={"key": "value"})
        assert r.success
        assert r.data == {"key": "value"}

    def test_failure(self) -> None:
        r = ToolResult(success=False, error="not found")
        assert not r.success
        assert r.error == "not found"


class TestToolCallRecord:
    def test_create(self) -> None:
        r = ToolCallRecord(tool_name="search")
        assert r.tool_name == "search"


class TestSkillResult:
    def test_success(self) -> None:
        r = SkillResult(success=True, data="done")
        assert r.success


class TestSkillExecutionRecord:
    def test_create(self) -> None:
        r = SkillExecutionRecord(skill_name="read_file")
        assert r.skill_name == "read_file"


# ── Event models ──


class TestPipelineEvents:
    def test_input_sanitized(self) -> None:
        e = InputSanitized(original_length=100, sanitized_length=80)
        assert e.type == "input_sanitized"

    def test_tool_executed(self) -> None:
        e = ToolExecuted(tool_name="web_search", success=True)
        assert e.tool_name == "web_search"

    def test_agent_initialized(self) -> None:
        e = AgentInitialized(version="0.1.0")
        assert e.version == "0.1.0"

    def test_error_occurred(self) -> None:
        e = ErrorOccurred(stage="generate", error="timeout")
        assert e.stage == "generate"

    def test_discriminated_union(self) -> None:
        from pydantic import TypeAdapter

        e = ToolExecuted(tool_name="test", success=True)
        j = e.model_dump_json()
        adapter = TypeAdapter(PipelineEvent)
        parsed = adapter.validate_json(j)
        assert isinstance(parsed, ToolExecuted)
        assert parsed.tool_name == "test"


class TestConstraintValidation:
    def test_float_bounds_rejected(self) -> None:
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ConceptUpdateMutation(concept_name="x", field="f", delta=0.1)

    def test_confidence_range_rejected(self) -> None:
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            Episode(id="ep-1", type="event", summary="t", importance=1.5)
