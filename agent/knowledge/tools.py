"""Knowledge base tools — tools the Agent can use to interact with the knowledge base."""

from datetime import UTC, datetime
from typing import Any

from agent.models.tools import ToolResult
from agent.tools.protocol import Tool


class ListKBSummariesTool(Tool):
    name = "kb_list_summaries"
    description = "列出知识库中所有笔记摘要"
    permissions = "safe"
    parameters = {}

    def __init__(self, kb_manager: Any = None) -> None:
        self._kb = kb_manager

    async def execute(self, args: dict[str, Any]) -> ToolResult:
        if self._kb is None:
            return ToolResult(success=False, error="Knowledge base not configured")
        files = await self._kb.list_summaries()
        return ToolResult(success=True, data={"files": files, "count": len(files)})


class ListKBConceptsTool(Tool):
    name = "kb_list_concepts"
    description = "列出知识库中所有概念页面"
    permissions = "safe"
    parameters = {}

    def __init__(self, kb_manager: Any = None) -> None:
        self._kb = kb_manager

    async def execute(self, args: dict[str, Any]) -> ToolResult:
        if self._kb is None:
            return ToolResult(success=False, error="Knowledge base not configured")
        files = await self._kb.list_concepts()
        return ToolResult(success=True, data={"files": files, "count": len(files)})


class ReadKBFileTool(Tool):
    name = "kb_read_file"
    description = "读取知识库中的文件内容"
    permissions = "safe"
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件路径，如 summaries/xxx.md 或 index.md"},
        },
        "required": ["path"],
    }

    def __init__(self, kb_manager: Any = None) -> None:
        self._kb = kb_manager

    async def execute(self, args: dict[str, Any]) -> ToolResult:
        if self._kb is None:
            return ToolResult(success=False, error="Knowledge base not configured")
        path = args["path"]
        try:
            content = await self._kb.read_file(path)
            return ToolResult(success=True, data={"path": path, "content": content, "size_chars": len(content)})
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class SearchKBTool(Tool):
    name = "kb_search"
    description = "全文搜索知识库内容"
    permissions = "safe"
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "搜索关键词"},
        },
        "required": ["query"],
    }

    def __init__(self, kb_manager: Any = None) -> None:
        self._kb = kb_manager

    async def execute(self, args: dict[str, Any]) -> ToolResult:
        if self._kb is None:
            return ToolResult(success=False, error="Knowledge base not configured")
        results = await self._kb.search(args["query"])
        return ToolResult(success=True, data={"results": results, "count": len(results)})


class WriteKBSummaryTool(Tool):
    name = "kb_write_summary"
    description = "为笔记创建或更新摘要页面。设置 source_path 为 None 可删除对应摘要。"
    permissions = "safe"
    parameters = {
        "type": "object",
        "properties": {
            "source_path": {"type": "string", "description": "原始笔记路径"},
            "content": {"type": "string", "description": "摘要内容（markdown）"},
            "tags": {"type": "array", "items": {"type": "string"}, "description": "标签列表"},
        },
        "required": ["source_path", "content"],
    }

    def __init__(self, kb_manager: Any = None) -> None:
        self._kb = kb_manager

    async def execute(self, args: dict[str, Any]) -> ToolResult:
        if self._kb is None:
            return ToolResult(success=False, error="Knowledge base not configured")
        try:
            path = await self._kb.write_summary(
                args["source_path"], args["content"], args.get("tags", [])
            )
            return ToolResult(success=True, data={"path": path, "action": "written"})
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class WriteKBConceptTool(Tool):
    name = "kb_write_concept"
    description = "创建或更新知识库概念页面"
    permissions = "safe"
    parameters = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "概念名称"},
            "content": {"type": "string", "description": "概念内容（markdown）"},
            "tags": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["name", "content"],
    }

    def __init__(self, kb_manager: Any = None) -> None:
        self._kb = kb_manager

    async def execute(self, args: dict[str, Any]) -> ToolResult:
        if self._kb is None:
            return ToolResult(success=False, error="Knowledge base not configured")
        try:
            path = await self._kb.write_concept(args["name"], args["content"], args.get("tags", []))
            return ToolResult(success=True, data={"path": path, "action": "written"})
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GetKBIndexTool(Tool):
    name = "kb_get_index"
    description = "获取知识库目录索引"
    permissions = "safe"
    parameters = {}

    def __init__(self, kb_manager: Any = None) -> None:
        self._kb = kb_manager

    async def execute(self, args: dict[str, Any]) -> ToolResult:
        if self._kb is None:
            return ToolResult(success=False, error="Knowledge base not configured")
        content = await self._kb.read_index()
        return ToolResult(success=True, data={"content": content, "size_chars": len(content)})


class GetKBOverviewTool(Tool):
    name = "kb_get_overview"
    description = "获取知识库总览（知识领域、工作脉络、主题地图）"
    permissions = "safe"
    parameters = {}

    def __init__(self, kb_manager: Any = None) -> None:
        self._kb = kb_manager

    async def execute(self, args: dict[str, Any]) -> ToolResult:
        if self._kb is None:
            return ToolResult(success=True, data={"content": "", "size_chars": 0})
        content = await self._kb.read_overview()
        return ToolResult(success=True, data={"content": content, "size_chars": len(content)})


class MaintainKBTool(Tool):
    name = "kb_maintain"
    description = "触发知识库维护：消化对话记录，更新用户画像。调用此工具后 Agent 会重新整理知识库。"
    permissions = "safe"
    parameters = {}

    def __init__(self, kb_manager: Any = None, llm_client: Any = None) -> None:
        self._kb = kb_manager
        self._llm = llm_client

    async def execute(self, args: dict[str, Any]) -> ToolResult:
        if self._kb is None:
            return ToolResult(success=False, error="Knowledge base not configured")

        chat_log = await self._kb.read_chat_log()
        if len(chat_log) < 200:
            return ToolResult(success=True, data={"digested": False, "reason": "对话记录不足，跳过维护"})

        if self._llm is None:
            await self._kb.clear_chat_log()
            return ToolResult(success=True, data={
                "digested": False,
                "reason": "LLM 未配置，已清空对话记录",
            })

        try:
            concepts, relationships, summary = await self._extract_with_llm(chat_log)
            if not concepts:
                await self._kb.clear_chat_log()
                return ToolResult(success=True, data={"digested": False, "reason": "未提取到有价值的概念"})

            written_concepts = []
            for c in concepts:
                name = c.get("name", "")
                desc = c.get("description", "")
                tags = c.get("tags", [])
                if not name:
                    continue
                content = f"{desc}\n\n## 来源\n从对话记录中自动提取。"
                try:
                    path = await self._kb.write_concept(name, content, tags)
                    written_concepts.append({"name": name, "path": path})
                except Exception:
                    continue

            for rel in relationships:
                a, b = rel.get("from", ""), rel.get("to", "")
                if a and b:
                    try:
                        await self._kb.mark_concept_relationship(a, b, 0.8)
                    except Exception:
                        pass

            if summary:
                ts = datetime.now(UTC).strftime("%Y-%m-%d %H:%M")
                try:
                    await self._kb.write_file(
                        f"summaries/chat-{ts.replace(' ', '-').replace(':', '-')}.md",
                        f"# 对话摘要\n\n{summary}",
                    )
                except Exception:
                    pass

            await self._enrich_cross_connections()
            await self._update_index()
            await self._update_overview()

            await self._kb.clear_chat_log()

            return ToolResult(success=True, data={
                "digested": True,
                "chat_log_size": len(chat_log),
                "concepts_written": len(written_concepts),
                "concepts": written_concepts,
                "message": f"已从对话中提取 {len(written_concepts)} 个概念。",
            })
        except Exception as e:
            return ToolResult(success=False, error=f"维护失败: {e}")

    async def _extract_with_llm(self, chat_log: str) -> tuple[list[dict], list[dict], str]:
        import json as _json

        existing_concepts = await self._kb.list_concepts()
        existing_names = [c.replace(".md", "") for c in existing_concepts]
        existing_info = "\n".join(f"- {n}" for n in existing_names) if existing_names else "（无现有概念）"

        system_prompt = f"""你是知识库维护者。阅读对话记录，提取值得长期保留的知识。

## 现有概念
{existing_info}

## 要求
1. 提取 3-8 个核心概念。只提取有长期保留价值的知识，跳过琐碎/临时的内容（如：时间查询、系统报错、打招呼等）。每个包含：名称(简洁词条)、描述(1-2句说明)、标签([])
2. 对于每个新概念，如果与现有概念有关联，在 relationships 中标记。同时也要标记哪些新概念应该合并到现有概念（名称相同或高度重叠）
3. 标记新概念之间的关联
4. 生成一段 2-3 句的对话摘要

仅返回 JSON，不要其他文字：
{{"concepts":[{{"name":"","description":"","tags":[]}}],"relationships":[{{"from":"","to":"","type":"related"}}],"summary":""}}"""

        result = await self._llm.complete(messages, temperature=0.3, max_tokens=2048)
        text = result.get("content", "")

        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            text = text[start:end]
        data = _json.loads(text)

        return (
            data.get("concepts", []),
            data.get("relationships", []),
            data.get("summary", ""),
        )

    async def _enrich_cross_connections(self) -> None:
        """LLM scans all concepts and finds missing cross-connections."""
        if self._llm is None:
            return

        import json as _json
        concept_files = await self._kb.list_concepts()
        if len(concept_files) < 2:
            return

        concept_list: list[dict] = []
        for fname in concept_files:
            slug = fname.replace(".md", "")
            try:
                raw = await self._kb.read_concept(slug)
                fm, body = raw.split("---\n", 2)[1:] if "---" in raw else ({}, raw)
                import yaml
                fm = yaml.safe_load(fm) or {}
                name = fm.get("name", slug) if isinstance(fm, dict) else slug
                tags = fm.get("tags", []) if isinstance(fm, dict) else []
                related = fm.get("related", []) if isinstance(fm, dict) else []
                concept_list.append({"slug": slug, "name": name, "tags": tags, "related": related})
            except Exception:
                concept_list.append({"slug": slug, "name": slug, "tags": [], "related": []})

        prompt = f"""分析以下概念列表，找出应该关联但目前缺少关联的概念对。

现有概念：
{_json.dumps(concept_list, ensure_ascii=False, indent=2)}

找出有明确语义关联但尚未建立 related 关系的概念对。关联类型包括：同一领域、技术栈相关、概念之间有依赖/包含/应用关系。

仅返回 JSON：{{"new_relationships":[{{"from":"slug-a","to":"slug-b"}}]}}"""

        try:
            result = await self._llm.complete(
                [{"role": "user", "content": prompt}],
                temperature=0.2, max_tokens=1024,
            )
            text = result.get("content", "")
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                data = _json.loads(text[start:end])
                for rel in data.get("new_relationships", []):
                    a, b = rel.get("from", ""), rel.get("to", "")
                    if a and b:
                        await self._kb.mark_concept_relationship(a, b, 0.7)
        except Exception:
            pass

    async def _update_index(self) -> None:
        concepts = await self._kb.list_concepts()
        summaries = await self._kb.list_summaries()
        lines = [
            "# 知识库目录",
            "",
            f"> 自动生成于 {datetime.now(UTC).strftime('%Y-%m-%d %H:%M')}",
            "",
            "## 概念",
            "",
        ]
        for c in sorted(concepts):
            name = c.replace(".md", "")
            lines.append(f"- [[concepts/{name}]]")
        lines.extend(["", "## 摘要", ""])
        for s in sorted(summaries):
            name = s.replace(".md", "")
            lines.append(f"- [[summaries/{name}]]")
        await self._kb.write_file("index.md", "\n".join(lines))

    async def _update_overview(self) -> None:
        concepts = await self._kb.list_concepts()
        lines = [
            "# 知识库总览",
            "",
            f"> 自动生成于 {datetime.now(UTC).strftime('%Y-%m-%d %H:%M')}",
            "",
            "## 概念图谱",
            "",
            f"当前收录 **{len(concepts)}** 个概念。",
            "",
        ]
        if concepts:
            lines.append("| 概念 |")
            lines.append("|------|")
            for c in sorted(concepts):
                name = c.replace(".md", "")
                lines.append(f"| {name} |")
        await self._kb.write_file("overview.md", "\n".join(lines))
