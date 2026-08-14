"""Knowledge base manager — CRUD, maintenance, and sync operations."""

from datetime import UTC, datetime
from typing import Any

from agent.knowledge.schema import KB_SCHEMA, PROTECTED_FILES
from agent.ports.storage import FileStorage


class KnowledgeBaseManager:
    """Manages the llm-wiki knowledge base: summaries, concepts, index, overview, log."""

    def __init__(self, storage: FileStorage, base_path: str) -> None:
        self._storage = storage
        self._base_path = base_path
        self._initialized = False

    @property
    def base_path(self) -> str:
        return self._base_path

    async def initialize(self) -> None:
        """Create knowledge base structure if not exists."""
        dirs = ["summaries", "concepts"]
        for d in dirs:
            await self._storage.mkdir(f"{self._base_path}/{d}")

        # Create SCHEMA.md if not exists
        if not await self._storage.exists(f"{self._base_path}/SCHEMA.md"):
            await self._storage.write(f"{self._base_path}/SCHEMA.md", KB_SCHEMA)

        # Create log.md if not exists
        if not await self._storage.exists(f"{self._base_path}/log.md"):
            await self._storage.write(
                f"{self._base_path}/log.md",
                f"# 操作日志\n\n## [{datetime.now(UTC).strftime('%Y-%m-%d %H:%M')}] 知识库初始化\n",
            )

        # Create index.md stub
        if not await self._storage.exists(f"{self._base_path}/index.md"):
            await self._storage.write(
                f"{self._base_path}/index.md",
                "# 知识库目录\n\n> 知识库内容待扩充。使用 Agent 对话积累知识后，执行维护操作生成索引。\n",
            )

        # Create overview.md stub
        if not await self._storage.exists(f"{self._base_path}/overview.md"):
            await self._storage.write(
                f"{self._base_path}/overview.md",
                "# 知识库总览\n\n> 知识库内容待扩充。\n",
            )

        self._initialized = True

    # ── File CRUD ──

    async def list_files(self, subdir: str = "") -> list[str]:
        path = f"{self._base_path}/{subdir}".rstrip("/")
        try:
            return await self._storage.list_dir(path)
        except Exception:
            return []

    async def read_file(self, path: str) -> str:
        full = f"{self._base_path}/{path}"
        return await self._storage.read(full)

    async def write_file(self, path: str, content: str) -> None:
        if path in PROTECTED_FILES:
            raise ValueError(f"Protected file cannot be overwritten: {path}")
        full = f"{self._base_path}/{path}"
        await self._storage.write(full, content)

    async def delete_file(self, path: str) -> None:
        if path in PROTECTED_FILES:
            raise ValueError(f"Protected file cannot be deleted: {path}")
        full = f"{self._base_path}/{path}"
        await self._storage.delete(full)

    # ── Summary Operations ──

    async def write_summary(
        self, source_path: str, content: str, tags: list[str] | None = None
    ) -> str:
        """Write a summary page for a source note."""
        import os

        from agent.memory.store import _encode_yaml_frontmatter

        name = os.path.basename(source_path).replace(".md", "")
        fm: dict[str, Any] = {
            "source": source_path,
            "date": datetime.now(UTC).strftime("%Y-%m-%d"),
            "tags": tags or [],
        }
        body = f"# 摘要: {name}\n\n{content}"
        page = _encode_yaml_frontmatter(fm, body)
        safe_name = name.replace("/", "-").replace(" ", "-")
        path = f"summaries/{safe_name}.md"
        await self._storage.write(f"{self._base_path}/{path}", page)
        await self._append_log(f"写入摘要: {path}")
        return path

    async def read_summary(self, name: str) -> str:
        return await self._storage.read(f"{self._base_path}/summaries/{name}.md")

    async def list_summaries(self) -> list[str]:
        try:
            files = await self._storage.list_dir(f"{self._base_path}/summaries")
            return [f for f in files if f.endswith(".md")]
        except Exception:
            return []

    # ── Concept Operations ──

    async def write_concept(self, name: str, content: str, tags: list[str] | None = None) -> str:
        from agent.memory.store import _encode_yaml_frontmatter

        fm: dict[str, Any] = {
            "type": "concept",
            "date": datetime.now(UTC).strftime("%Y-%m-%d"),
            "tags": tags or [],
        }
        body = f"# 概念: {name}\n\n{content}"
        page = _encode_yaml_frontmatter(fm, body)
        safe_name = name.replace("/", "-").replace(" ", "-")
        path = f"concepts/{safe_name}.md"
        await self._storage.write(f"{self._base_path}/{path}", page)
        await self._append_log(f"写入概念: {path}")
        return path

    async def read_concept(self, name: str) -> str:
        return await self._storage.read(f"{self._base_path}/concepts/{name}.md")

    async def list_concepts(self) -> list[str]:
        try:
            files = await self._storage.list_dir(f"{self._base_path}/concepts")
            return [f for f in files if f.endswith(".md")]
        except Exception:
            return []

    async def mark_concept_relationship(
        self, name_a: str, name_b: str, weight: float = 0.8
    ) -> None:
        from agent.memory.store import (
            _encode_yaml_frontmatter,
            _get_str_list,
            _parse_yaml_frontmatter,
        )

        safe_a = name_a.replace("/", "-").replace(" ", "-")
        safe_b = name_b.replace("/", "-").replace(" ", "-")

        for safe_name, other in [(safe_a, name_b), (safe_b, name_a)]:
            try:
                text = await self._storage.read(f"{self._base_path}/concepts/{safe_name}.md")
                fm, body = _parse_yaml_frontmatter(text)
                if not fm:
                    continue
                related = _get_str_list(fm, "related")
                if other not in related:
                    related.append(other)
                fm["related"] = related
                content = _encode_yaml_frontmatter(fm, body)
                await self._storage.write(f"{self._base_path}/concepts/{safe_name}.md", content)
            except Exception:
                continue

    # ── Index & Overview ──

    async def read_index(self) -> str:
        try:
            return await self._storage.read(f"{self._base_path}/index.md")
        except Exception:
            return ""

    async def write_index(self, content: str) -> None:
        await self._storage.write(f"{self._base_path}/index.md", content)
        await self._append_log("更新 index.md")

    async def read_overview(self) -> str:
        try:
            return await self._storage.read(f"{self._base_path}/overview.md")
        except Exception:
            return ""

    async def write_overview(self, content: str) -> None:
        await self._storage.write(f"{self._base_path}/overview.md", content)
        await self._append_log("更新 overview.md")

    # ── Profile ──

    async def read_profile(self) -> str:
        try:
            return await self._storage.read(f"{self._base_path}/profile.md")
        except Exception:
            return ""

    async def write_profile(self, content: str) -> None:
        await self._storage.write(f"{self._base_path}/profile.md", content)
        await self._append_log("更新 profile.md")

    # ── Chat Log ──

    async def read_chat_log(self) -> str:
        try:
            return await self._storage.read(f"{self._base_path}/chat-log.md")
        except Exception:
            return ""

    async def append_chat_log(self, user_msg: str, assistant_msg: str) -> None:
        ts = datetime.now(UTC).isoformat()
        entry = f"\n## [{ts}] 用户\n{user_msg}\n\n## [{ts}] Agent\n{assistant_msg}\n"
        try:
            existing = await self._storage.read(f"{self._base_path}/chat-log.md")
        except Exception:
            existing = "# 对话记录\n\n> 这些对话将在下次知识库维护时被消化，然后清空。\n"
        await self._storage.write(f"{self._base_path}/chat-log.md", existing + entry)

    async def clear_chat_log(self) -> None:
        await self._storage.write(
            f"{self._base_path}/chat-log.md",
            f"# 对话记录\n\n> 上次消化时间: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M')}\n> 等待新对话...\n",
        )
        await self._append_log("清空对话记录")

    # ── Search ──

    async def search(self, query: str) -> list[dict[str, Any]]:
        """Full-text search across all knowledge base files."""
        results: list[dict[str, Any]] = []
        dirs = ["", "summaries", "concepts"]
        query_lower = query.lower()

        for d in dirs:
            try:
                files = await self._storage.list_dir(f"{self._base_path}/{d}".rstrip("/"))
            except Exception:
                continue

            for fname in files:
                if not fname.endswith(".md"):
                    continue
                path = f"{d}/{fname}".lstrip("/") if d else fname
                try:
                    content = await self._storage.read(f"{self._base_path}/{path}")
                    if query_lower in content.lower():
                        lines = content.split("\n")
                        snippets = [ln for ln in lines if query_lower in ln.lower()]
                        results.append(
                            {
                                "path": path,
                                "snippets": snippets[:5],
                                "match_count": len(snippets),
                            }
                        )
                except Exception:
                    continue

        results.sort(key=lambda r: r["match_count"], reverse=True)
        return results[:20]

    # ── Log ──

    async def _append_log(self, entry: str) -> None:
        ts = datetime.now(UTC).strftime("%Y-%m-%d %H:%M")
        log_entry = f"\n## [{ts}] {entry}\n"
        try:
            existing = await self._storage.read(f"{self._base_path}/log.md")
            await self._storage.write(f"{self._base_path}/log.md", existing + log_entry)
        except Exception:
            pass
