"""Tests for TfidfVectorStore."""

import pytest

from agent.infrastructure.vector.tfidf_store import TfidfVectorStore


class TestTfidfVectorStore:
    @pytest.mark.asyncio
    async def test_build_and_search(self) -> None:
        store = TfidfVectorStore()
        docs = [
            {
                "path": "doc1.md",
                "content": "Python is a great programming language for AI and machine learning",
            },
            {
                "path": "doc2.md",
                "content": "Rust is a systems programming language focused on safety",
            },
            {
                "path": "doc3.md",
                "content": "深度学习是人工智能的一个重要分支，Python是常用的编程语言",
            },
        ]
        store.build(docs)
        results = await store.search("Python programming", top_k=2)
        assert len(results) <= 2
        if results:
            assert results[0].score >= 0

    @pytest.mark.asyncio
    async def test_empty_search(self) -> None:
        store = TfidfVectorStore()
        results = await store.search("anything", top_k=3)
        assert results == []

    @pytest.mark.asyncio
    async def test_serialize_deserialize(self) -> None:
        store = TfidfVectorStore()
        docs = [
            {"path": "d1.md", "content": "machine learning and deep learning"},
            {"path": "d2.md", "content": "python programming language"},
        ]
        store.build(docs)
        data = store.serialize()

        store2 = TfidfVectorStore()
        store2.deserialize(data)
        results = await store2.search("machine learning", top_k=2)
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_apply_feedback(self) -> None:
        store = TfidfVectorStore()
        docs = [{"path": "d1.md", "content": "test content"}]
        store.build(docs)
        store.apply_feedback("d1.md", 0.1)
        results = await store.search("test", top_k=1)
        assert len(results) > 0
