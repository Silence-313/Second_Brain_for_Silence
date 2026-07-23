"""RAG feedback — retrieval quality feedback loop with query clustering."""

import json
from typing import Any

from agent.models.retrieval import DocumentWeight, QueryCluster, RetrievalRecord

_DOWNWEIGHT_FACTOR = 0.15
_MIN_WEIGHT = 0.1
_CONFIRMATION_GATE = 3


class RagFeedback:
    """Retrieval quality feedback: document weight adjustment, query clustering."""

    def __init__(self) -> None:
        self._doc_weights: dict[str, DocumentWeight] = {}
        self._query_clusters: dict[str, QueryCluster] = {}
        self._records: list[RetrievalRecord] = []

    def record_retrieval(self, record: RetrievalRecord) -> None:
        self._records.append(record)
        self._update_doc_weights(record)
        self._cluster_query(record)

        if len(self._records) > 200:
            self._records = self._records[-200:]

    def get_doc_weight(self, path: str) -> DocumentWeight | None:
        return self._doc_weights.get(path)

    def get_negative_signals(self) -> list[str]:
        return [
            path
            for path, w in self._doc_weights.items()
            if w.downweight_factor > _DOWNWEIGHT_FACTOR / 2
        ]

    def apply_feedback(self, path: str, delta: float) -> None:
        weight = self._doc_weights.get(path)
        if weight is None:
            weight = DocumentWeight(path=path)

        new_relevance = max(0.0, min(1.0, weight.relevance_score + delta))
        self._doc_weights[path] = weight.model_copy(
            update={"relevance_score": round(new_relevance, 4)}
        )

    def get_cluster_success_rate(self, signature: str) -> float:
        cluster = self._query_clusters.get(signature)
        return cluster.success_rate if cluster else 0.5

    def serialize(self) -> str:
        data: dict[str, Any] = {
            "doc_weights": {
                path: w.model_dump(mode="json")
                for path, w in self._doc_weights.items()
            },
            "query_clusters": {
                sig: c.model_dump(mode="json")
                for sig, c in self._query_clusters.items()
            },
        }
        return json.dumps(data, ensure_ascii=False, default=str)

    def deserialize(self, json_str: str) -> None:
        try:
            data = json.loads(json_str)
            for path, raw in data.get("doc_weights", {}).items():
                self._doc_weights[path] = DocumentWeight.model_validate(raw)
            for sig, raw in data.get("query_clusters", {}).items():
                self._query_clusters[sig] = QueryCluster.model_validate(raw)
        except (json.JSONDecodeError, KeyError):
            pass

    def _update_doc_weights(self, record: RetrievalRecord) -> None:
        for path in record.used_docs:
            w = self._doc_weights.get(path)
            if w is None:
                w = DocumentWeight(path=path)
            impact = max(0.0, w.answer_impact_score + 0.05)
            self._doc_weights[path] = w.model_copy(
                update={
                    "relevance_score": min(1.0, w.relevance_score + 0.05),
                    "answer_impact_score": round(impact, 4),
                }
            )

        for path in record.retrieved_docs:
            if path in record.used_docs:
                continue
            w = self._doc_weights.get(path)
            if w is None:
                w = DocumentWeight(path=path)
            downweight = w.downweight_factor
            if len(self._records) >= _CONFIRMATION_GATE:
                downweight = min(
                    1.0 - _MIN_WEIGHT,
                    downweight + _DOWNWEIGHT_FACTOR / _CONFIRMATION_GATE,
                )
            self._doc_weights[path] = w.model_copy(
                update={
                    "relevance_score": max(_MIN_WEIGHT, w.relevance_score - 0.02),
                    "downweight_factor": round(downweight, 4),
                }
            )

    def _cluster_query(self, record: RetrievalRecord) -> None:
        signature = self._extract_signature(record.query)
        cluster = self._query_clusters.get(signature)
        if cluster is None:
            cluster = QueryCluster(signature=signature)

        new_count = cluster.count + 1
        quality = record.answer_quality
        new_success = cluster.success_rate + (quality - cluster.success_rate) / new_count

        self._query_clusters[signature] = cluster.model_copy(
            update={
                "count": new_count,
                "success_rate": round(new_success, 4),
            }
        )

    @staticmethod
    def _extract_signature(query: str) -> str:
        words = query.strip().lower().split()
        meaningful = [w for w in words if len(w) > 1][:5]
        return " ".join(sorted(meaningful)) if meaningful else query.strip()[:30]
