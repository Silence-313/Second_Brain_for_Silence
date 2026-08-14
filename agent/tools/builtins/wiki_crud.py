"""Built-in tool: wiki CRUD operations — list, read, write, delete, search."""

from typing import Any

from agent.models.tools import ToolResult
from agent.tools.protocol import Tool

_SAFE_EXTENSIONS = {".md", ".txt", ".json", ".yaml", ".yml", ".csv"}
_MAX_SIZE_KB = 100
_PROTECTED_PATHS = {"INDEX.md", "profile.md"}


class ListWikiTool(Tool):
    name = "list_wiki_files"
    description = "列出知识库中的文件"
    permissions = "safe"
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "子目录路径，默认根目录"},
        },
    }

    def __init__(self, storage: Any = None, base_path: str = "") -> None:
        self._storage = storage
        self._base_path = base_path

    async def execute(self, args: dict[str, Any]) -> ToolResult:
        if self._storage is None:
            return ToolResult(success=False, error="Storage not configured")

        path = args.get("path", "")
        full = f"{self._base_path}/{path}".rstrip("/")
        try:
            files = await self._storage.list_dir(full)
            return ToolResult(success=True, data={"files": files, "count": len(files)})
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class ReadWikiTool(Tool):
    name = "read_wiki_file"
    description = "读取知识库文件内容"
    permissions = "safe"
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件路径"},
        },
        "required": ["path"],
    }

    def __init__(self, storage: Any = None, base_path: str = "") -> None:
        self._storage = storage
        self._base_path = base_path

    async def execute(self, args: dict[str, Any]) -> ToolResult:
        if self._storage is None:
            return ToolResult(success=False, error="Storage not configured")

        path = args["path"]
        self._validate_path(path)
        full = f"{self._base_path}/{path}"

        try:
            content = await self._storage.read(full)
            return ToolResult(
                success=True,
                data={"path": path, "content": content, "size_chars": len(content)},
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    @staticmethod
    def _validate_path(path: str) -> None:
        if ".." in path:
            raise ValueError("Path traversal not allowed")
        if path.startswith("/"):
            raise ValueError("Absolute paths not allowed")


class WriteWikiTool(Tool):
    name = "write_wiki_file"
    description = "写入知识库文件"
    permissions = "safe"
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件路径"},
            "content": {"type": "string", "description": "文件内容"},
        },
        "required": ["path", "content"],
    }

    def __init__(self, storage: Any = None, base_path: str = "") -> None:
        self._storage = storage
        self._base_path = base_path

    async def execute(self, args: dict[str, Any]) -> ToolResult:
        if self._storage is None:
            return ToolResult(success=False, error="Storage not configured")

        path = args["path"]
        content = args["content"]

        if ".." in path:
            return ToolResult(success=False, error="Path traversal not allowed")

        ext = path[path.rfind(".") :] if "." in path else ""
        if ext not in _SAFE_EXTENSIONS:
            return ToolResult(success=False, error=f"Extension not allowed: {ext}")

        if len(content) > _MAX_SIZE_KB * 1024:
            return ToolResult(success=False, error=f"Content exceeds {_MAX_SIZE_KB}KB limit")

        full = f"{self._base_path}/{path}"
        try:
            await self._storage.write(full, content)
            return ToolResult(success=True, data={"path": path, "size_chars": len(content)})
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class DeleteWikiTool(Tool):
    name = "delete_wiki_file"
    description = "删除知识库文件"
    permissions = "safe"
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件路径"},
        },
        "required": ["path"],
    }

    def __init__(self, storage: Any = None, base_path: str = "") -> None:
        self._storage = storage
        self._base_path = base_path

    async def execute(self, args: dict[str, Any]) -> ToolResult:
        if self._storage is None:
            return ToolResult(success=False, error="Storage not configured")

        path = args["path"]

        import os

        if os.path.basename(path) in _PROTECTED_PATHS:
            return ToolResult(success=False, error=f"Protected file: {path}")

        if ".." in path:
            return ToolResult(success=False, error="Path traversal not allowed")

        full = f"{self._base_path}/{path}"
        try:
            await self._storage.delete(full)
            return ToolResult(success=True, data={"path": path, "deleted": True})
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class SearchWikiTool(Tool):
    name = "search_wiki"
    description = "全文搜索知识库内容"
    permissions = "safe"
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "搜索关键词"},
        },
        "required": ["query"],
    }

    def __init__(self, storage: Any = None, base_path: str = "") -> None:
        self._storage = storage
        self._base_path = base_path

    async def execute(self, args: dict[str, Any]) -> ToolResult:
        if self._storage is None:
            return ToolResult(success=False, error="Storage not configured")

        query = args["query"].lower()
        matches: list[dict[str, Any]] = []

        try:
            files = await self._storage.list_dir(self._base_path)
        except Exception:
            files = []

        for fname in files:
            if not fname.endswith(tuple(_SAFE_EXTENSIONS)):
                continue
            try:
                content = await self._storage.read(f"{self._base_path}/{fname}")
                if query in content.lower():
                    lines = content.split("\n")
                    snippets = [line for line in lines if query in line.lower()]
                    matches.append(
                        {
                            "path": fname,
                            "snippets": snippets[:5],
                            "match_count": len(snippets),
                        }
                    )
            except Exception:
                continue

        matches.sort(key=lambda m: m["match_count"], reverse=True)
        return ToolResult(success=True, data={"results": matches[:10], "count": len(matches)})
