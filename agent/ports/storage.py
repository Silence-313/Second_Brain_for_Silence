"""File storage protocol — abstract interface for file system operations."""

from typing import Protocol


class FileStorage(Protocol):
    """Abstract file system. Implementations: LocalFileStorage, InMemoryFileStorage."""

    async def read(self, path: str) -> str:
        """Read file contents as string."""
        ...

    async def write(self, path: str, content: str) -> None:
        """Write string content to file. Creates parent directories."""
        ...

    async def exists(self, path: str) -> bool:
        """Check if path exists."""
        ...

    async def list_dir(self, path: str) -> list[str]:
        """List directory contents (file names only)."""
        ...

    async def delete(self, path: str) -> None:
        """Delete a file or empty directory."""
        ...

    async def mkdir(self, path: str) -> None:
        """Create directory and all parent directories."""
        ...
