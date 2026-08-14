"""Tests for RagFeedback."""

from agent.models.retrieval import RetrievalRecord
from agent.retrieval.feedback import RagFeedback


class TestRagFeedback:
    def test_record_retrieval(self) -> None:
        rag = RagFeedback()
        rag.record_retrieval(
            RetrievalRecord(
                query="test",
                retrieved_docs=["a.md", "b.md"],
                used_docs=["a.md"],
                answer_quality=0.8,
            )
        )
        w = rag.get_doc_weight("a.md")
        assert w is not None

    def test_apply_feedback(self) -> None:
        rag = RagFeedback()
        rag.apply_feedback("doc.md", 0.05)
        w = rag.get_doc_weight("doc.md")
        assert w is not None
        assert w.relevance_score > 0.5

    def test_serialize_deserialize(self) -> None:
        rag = RagFeedback()
        rag.record_retrieval(
            RetrievalRecord(
                query="q", retrieved_docs=["a.md"], used_docs=["a.md"], answer_quality=0.7
            )
        )
        json_str = rag.serialize()
        rag2 = RagFeedback()
        rag2.deserialize(json_str)
        assert rag2.get_doc_weight("a.md") is not None

    def test_get_negative_signals(self) -> None:
        rag = RagFeedback()
        for i in range(5):
            rag.record_retrieval(
                RetrievalRecord(
                    query=f"q{i}", retrieved_docs=["doc.md"], used_docs=[], answer_quality=0.3
                )
            )
        signals = rag.get_negative_signals()
        assert isinstance(signals, list)

    def test_get_cluster_success_rate(self) -> None:
        rag = RagFeedback()
        rag.record_retrieval(
            RetrievalRecord(
                query="what is python",
                retrieved_docs=["a.md"],
                used_docs=["a.md"],
                answer_quality=0.8,
            )
        )
        rate = rag.get_cluster_success_rate("is python what")
        assert 0 <= rate <= 1
