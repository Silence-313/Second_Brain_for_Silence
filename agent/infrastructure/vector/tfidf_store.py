"""TF-IDF vector store — offline vectorization and cosine similarity search."""

import json
import math
import re
from collections import Counter

from agent.models.retrieval import DocumentWeight, VectorSearchResult

_CJK_RE = re.compile(r"[一-鿿㐀-䶿]")
_TOKEN_RE = re.compile(r"[a-zA-Z]{3,}|[a-zA-Z]+_[a-zA-Z]+|[0-9]+")

_STOP_WORDS: set[str] = {
    "the",
    "a",
    "an",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "to",
    "of",
    "in",
    "for",
    "on",
    "with",
    "at",
    "by",
    "from",
    "as",
    "and",
    "or",
    "not",
    "but",
    "if",
    "then",
    "else",
    "when",
    "where",
    "how",
    "what",
    "which",
    "who",
    "whom",
    "this",
    "that",
    "these",
    "those",
    "it",
    "its",
    "he",
    "she",
    "的",
    "了",
    "在",
    "是",
    "我",
    "有",
    "和",
    "就",
    "不",
    "人",
    "都",
    "一",
    "上",
    "也",
    "很",
    "到",
    "说",
    "要",
    "去",
    "你",
    "会",
    "着",
    "没有",
    "看",
    "好",
    "自己",
    "这",
    "那",
    "什么",
}


class TfidfVectorStore:
    """Implements VectorStore protocol. Offline TF-IDF + cosine similarity."""

    def __init__(self) -> None:
        self._documents: list[dict[str, str]] = []
        self._vocabulary: dict[str, int] = {}
        self._idf: list[float] = []
        self._doc_vectors: list[list[float]] = []
        self._feedback: dict[str, DocumentWeight] = {}

    def build(self, documents: list[dict[str, str]]) -> None:
        self._documents = documents
        self._vocabulary.clear()

        tokenized = [self._tokenize(d["content"]) for d in documents]

        doc_freq: Counter[str] = Counter()
        for tokens in tokenized:
            for token in set(tokens):
                doc_freq[token] += 1

        sorted_terms = sorted(doc_freq, key=doc_freq.get, reverse=True)  # type: ignore[arg-type]
        self._vocabulary = {term: i for i, term in enumerate(sorted_terms)}

        n = len(documents)
        self._idf = [math.log(n / (1 + doc_freq[term])) for term in sorted_terms]

        self._doc_vectors = []
        for tokens in tokenized:
            tf = Counter(tokens)
            vector = [tf.get(term, 0) * self._idf[i] for i, term in enumerate(sorted_terms)]
            self._doc_vectors.append(vector)

    async def search(self, query: str, top_k: int = 3) -> list[VectorSearchResult]:
        if not self._vocabulary or not self._doc_vectors:
            return []

        query_tokens = self._tokenize(query)
        query_tf = Counter(query_tokens)
        query_vector = [
            query_tf.get(term, 0) * self._idf[i] for i, term in enumerate(self._vocabulary)
        ]

        scored: list[tuple[int, float]] = []
        for i, doc_vec in enumerate(self._doc_vectors):
            cosine = self._cosine_similarity(query_vector, doc_vec)

            path = self._documents[i].get("path", f"doc-{i}")
            fb = self._feedback.get(path)
            if fb:
                cosine *= (1 - fb.downweight_factor) * (1 + fb.answer_impact_score * 0.2)

            scored.append((i, round(cosine, 4)))

        scored.sort(key=lambda x: x[1], reverse=True)

        results: list[VectorSearchResult] = []
        for idx, score in scored[:top_k]:
            doc = self._documents[idx]
            path = doc.get("path", f"doc-{idx}")
            fb = self._feedback.get(path)

            results.append(
                VectorSearchResult(
                    content=doc["content"][:500],
                    source_path=path,
                    score=score,
                    relevance_score=fb.relevance_score if fb else 0.5,
                    answer_impact_score=fb.answer_impact_score if fb else 0.0,
                    downweight_factor=fb.downweight_factor if fb else 0.0,
                )
            )

        return results

    def apply_feedback(self, doc_path: str, delta: float) -> None:
        fb = self._feedback.get(doc_path)
        if fb is None:
            fb = DocumentWeight(path=doc_path)
        self._feedback[doc_path] = fb.model_copy(
            update={"relevance_score": max(0.1, min(1.0, fb.relevance_score + delta))}
        )

    def serialize(self) -> str:
        data = {
            "documents": self._documents,
            "vocabulary": self._vocabulary,
            "idf": self._idf,
            "feedback": {
                path: {
                    "relevance_score": fb.relevance_score,
                    "answer_impact_score": fb.answer_impact_score,
                    "downweight_factor": fb.downweight_factor,
                }
                for path, fb in self._feedback.items()
            },
        }
        return json.dumps(data, ensure_ascii=False)

    def deserialize(self, data: str) -> None:
        try:
            obj = json.loads(data)
            self._documents = obj.get("documents", [])
            self._vocabulary = obj.get("vocabulary", {})
            self._idf = obj.get("idf", [])
            for path, fb_data in obj.get("feedback", {}).items():
                self._feedback[path] = DocumentWeight(
                    path=path,
                    relevance_score=fb_data.get("relevance_score", 0.5),
                    answer_impact_score=fb_data.get("answer_impact_score", 0.0),
                    downweight_factor=fb_data.get("downweight_factor", 0.0),
                )
            self._doc_vectors = []
            if self._vocabulary:
                for doc in self._documents:
                    tokens = self._tokenize(doc["content"])
                    tf = Counter(tokens)
                    vec = [
                        tf.get(term, 0) * self._idf[i] for i, term in enumerate(self._vocabulary)
                    ]
                    self._doc_vectors.append(vec)
        except (json.JSONDecodeError, KeyError):
            pass

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        tokens: list[str] = []

        cjk_chars = "".join(_CJK_RE.findall(text))
        for i in range(len(cjk_chars) - 1):
            bg = cjk_chars[i : i + 2]
            if bg not in _STOP_WORDS:
                tokens.append(bg)

        en_tokens = _TOKEN_RE.findall(text.lower())
        tokens.extend(t for t in en_tokens if t not in _STOP_WORDS)

        return tokens

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        if not a or not b:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b, strict=True))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
