"""Tests for StateMutationEngine."""

from agent.core.engine import StateMutationEngine
from agent.models.mutations import (
    ConceptDecayMutation,
    ConceptMergeMutation,
    ConceptUpdateMutation,
    MemoryWriteMutation,
    PolicyUpdateMutation,
    ReasoningTraceMutation,
    RelationshipMarkMutation,
)


class TestStateMutationEngine:
    def test_validate_concept_update(self) -> None:
        engine = StateMutationEngine()
        m = ConceptUpdateMutation(concept_name="ml", field="confidence", delta=0.03)
        assert engine.validate(m)

    def test_validate_concept_update_rejects_empty_name(self) -> None:
        engine = StateMutationEngine()
        m = ConceptUpdateMutation(concept_name="", field="confidence", delta=0.03)
        assert not engine.validate(m)

    def test_validate_concept_update_empty_name(self) -> None:
        engine = StateMutationEngine()
        m = ConceptUpdateMutation(concept_name="", field="confidence", delta=0.03)
        assert not engine.validate(m)

    def test_validate_concept_merge(self) -> None:
        engine = StateMutationEngine()
        m = ConceptMergeMutation(source_slug="ml", target_slug="dl")
        assert engine.validate(m)

    def test_validate_concept_decay(self) -> None:
        engine = StateMutationEngine()
        m = ConceptDecayMutation(concept_slug="ml", delta=-0.03)
        assert engine.validate(m)

    def test_validate_memory_write(self) -> None:
        engine = StateMutationEngine()
        m = MemoryWriteMutation(entry_id="ep-1", entry_type="episodic")
        assert engine.validate(m)

    def test_validate_policy_update(self) -> None:
        engine = StateMutationEngine()
        m = PolicyUpdateMutation(field="exploration_rate", value=0.3)
        assert engine.validate(m)

    def test_validate_reasoning_trace(self) -> None:
        engine = StateMutationEngine()
        m = ReasoningTraceMutation(trace_id="t1", query="test")
        assert engine.validate(m)

    def test_validate_relationship_mark(self) -> None:
        engine = StateMutationEngine()
        m = RelationshipMarkMutation(concept_a="ml", concept_b="dl", weight=0.7)
        assert engine.validate(m)

    def test_apply_invalid_returns_false(self) -> None:
        engine = StateMutationEngine()
        m = ConceptUpdateMutation(concept_name="", field="f", delta=0.01)
        assert not engine.validate(m)
