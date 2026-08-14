"""Tests for MutationQueue."""

from agent.core.queue import MutationQueue
from agent.models.mutations import ConceptUpdateMutation, PolicyUpdateMutation


class TestMutationQueue:
    def test_add(self) -> None:
        mq = MutationQueue()
        mq.add(ConceptUpdateMutation(concept_name="ml", field="confidence", delta=0.03))
        assert mq.size == 1

    def test_add_batch(self) -> None:
        mq = MutationQueue()
        mq.add_batch(
            [
                ConceptUpdateMutation(concept_name="a", field="f", delta=0.01),
                ConceptUpdateMutation(concept_name="b", field="f", delta=0.02),
            ]
        )
        assert mq.size == 2

    def test_deduplicate_concept_updates(self) -> None:
        mq = MutationQueue()
        mq.add(ConceptUpdateMutation(concept_name="ml", field="confidence", delta=0.03))
        mq.add(ConceptUpdateMutation(concept_name="ml", field="confidence", delta=0.02))
        resolved = mq.resolve()
        assert len(resolved) == 1
        assert resolved[0].delta == 0.05  # type: ignore[union-attr]

    def test_deduplicate_clamp(self) -> None:
        mq = MutationQueue()
        mq.add(ConceptUpdateMutation(concept_name="ml", field="confidence", delta=0.05))
        mq.add(ConceptUpdateMutation(concept_name="ml", field="confidence", delta=0.05))
        resolved = mq.resolve()
        assert resolved[0].delta == 0.05  # type: ignore[union-attr]

    def test_sort_by_priority(self) -> None:
        mq = MutationQueue()
        mq.add(ConceptUpdateMutation(concept_name="x", field="f", delta=0.01))
        mq.add(PolicyUpdateMutation(field="exploration_rate", value=0.3))
        resolved = mq.resolve()
        assert resolved[0].type == "policy_update"  # type: ignore[union-attr]

    def test_new_cycle(self) -> None:
        mq = MutationQueue()
        mq.add(ConceptUpdateMutation(concept_name="x", field="f", delta=0.01))
        mq.new_cycle()
        assert mq.size == 0
