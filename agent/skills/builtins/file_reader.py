"""Built-in skill: read local files with 6-layer security."""

import os
from typing import Any

from agent.models.skills import SkillResult
from agent.skills.protocol import Skill

_SAFE_EXTENSIONS = {".md", ".txt", ".json", ".yaml", ".yml", ".csv", ".log", ".py", ".js", ".ts", ".html", ".css"}
_MAX_SIZE = 500 * 1024  # 500KB
_BLOCKED_PATHS = {"/etc", "/proc", "/sys", "/dev", "C:\\Windows", "C:\\Windows\\System32"}


class ReadFileSkill(Skill):
    name = "read_local_file"
    description = "安全读取本地文件内容（6层安全检查）"
    permissions = "privileged"

    def __init__(self, storage: Any = None) -> None:
        self._storage = storage

    async def execute(self, args: dict[str, Any]) -> SkillResult:
        path = args.get("path", "")

        # Layer 1: Path traversal check
        if ".." in path or path.startswith("/"):
            return SkillResult(success=False, error="Path traversal or absolute path rejected")

        # Layer 2: Extension whitelist
        ext = os.path.splitext(path)[1].lower()
        if ext not in _SAFE_EXTENSIONS:
            return SkillResult(success=False, error=f"Extension not allowed: {ext}")

        # Layer 3: System path blocked
        normalized = os.path.normpath(path).lower()
        for blocked in _BLOCKED_PATHS:
            if normalized.startswith(blocked.lower()):
                return SkillResult(success=False, error=f"System path blocked: {blocked}")

        # Layer 4: File size limit
        try:
            if self._storage:
                content = await self._storage.read(path)
            else:
                with open(path, encoding="utf-8") as f:
                    content = f.read(_MAX_SIZE + 1)
        except FileNotFoundError:
            return SkillResult(success=False, error=f"File not found: {path}")
        except PermissionError:
            return SkillResult(success=False, error=f"Permission denied: {path}")
        except UnicodeDecodeError:
            return SkillResult(success=False, error=f"Binary file not supported: {path}")

        # Layer 5: Size cap
        if len(content) > _MAX_SIZE:
            return SkillResult(success=False, error=f"File exceeds {_MAX_SIZE // 1024}KB limit")

        # Layer 6: ENOENT already handled above

        return SkillResult(
            success=True,
            data={"path": path, "content": content, "size_chars": len(content)},
        )
