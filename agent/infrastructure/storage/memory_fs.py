"""In-memory file system adapter — for testing without real disk I/O."""


class InMemoryFileStorage:
    """Implements FileStorage protocol entirely in memory."""

    def __init__(self) -> None:
        self._files: dict[str, str] = {}

    async def read(self, path: str) -> str:
        if path not in self._files:
            raise FileNotFoundError(path)
        return self._files[path]

    async def write(self, path: str, content: str) -> None:
        self._files[path] = content

    async def exists(self, path: str) -> bool:
        return path in self._files

    async def list_dir(self, path: str) -> list[str]:
        prefix = path.rstrip("/") + "/"
        result: set[str] = set()
        for fpath in self._files:
            if fpath.startswith(prefix):
                relative = fpath[len(prefix) :]
                name = relative.split("/")[0]
                result.add(name)
        return sorted(result)

    async def delete(self, path: str) -> None:
        self._files.pop(path, None)

    async def mkdir(self, path: str) -> None:
        pass  # Directories are virtual, created implicitly on write

    @property
    def file_count(self) -> int:
        return len(self._files)
