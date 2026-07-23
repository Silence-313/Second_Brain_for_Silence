"""Local file system adapter — implements FileStorage protocol."""

import os


class LocalFileStorage:
    """Implements FileStorage protocol on the local file system."""

    async def read(self, path: str) -> str:
        with open(path, encoding="utf-8") as f:
            return f.read()

    async def write(self, path: str, content: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    async def exists(self, path: str) -> bool:
        return os.path.exists(path)

    async def list_dir(self, path: str) -> list[str]:
        if not os.path.isdir(path):
            return []
        return os.listdir(path)

    async def delete(self, path: str) -> None:
        if os.path.isfile(path):
            os.remove(path)

    async def mkdir(self, path: str) -> None:
        os.makedirs(path, exist_ok=True)
