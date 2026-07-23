"""Vector store protocol — abstract interface for vector search and retrieval."""

from typing import Protocol

from agent.models.retrieval import VectorSearchResult


class Document(Protocol):
    """A document to be indexed."""

    @property
    def path(self) -> str: ...
    @property
    def content(self) -> str: ...


class VectorStore(Protocol):
    """Abstract vector store. Implementation: TfidfVectorStore."""

    async def build(self, documents: list[Document]) -> None:
        """Build/replace the vector index from documents."""
        ...

    async def search(self, query: str, top_k: int = 3) -> list[VectorSearchResult]:
        """Search for documents relevant to query."""
        ...

    async def apply_feedback(self, doc_path: str, delta: float) -> None:
        """Apply relevance feedback to a document's weight."""
        ...

    def serialize(self) -> str:
        """Serialize the index to JSON string."""
        ...

    def deserialize(self, data: str) -> None:
        """Load the index from JSON string."""
        ...
