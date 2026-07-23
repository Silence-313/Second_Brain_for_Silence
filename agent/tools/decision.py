"""Tool decision policy — LLM-based autonomous tool usage decision."""

import json
import re
from typing import Any


class ToolDecisionPolicy:
    """LLM-based autonomous tool usage decision. Independent of keyword router."""

    def __init__(self, llm_client: Any = None) -> None:  # LLMClient | None
        self._llm_client = llm_client

    async def decide(
        self,
        query: str,
        available_tools: list[dict[str, Any]] | None = None,
        available_skills: list[dict[str, Any]] | None = None,
        wiki_context: str = "",
        concept_context: str = "",
        episodic_context: str = "",
    ) -> dict[str, Any]:
        tools_list = available_tools or []
        skills_list = available_skills or []

        if self._llm_client is not None:
            return await self._llm_decide(
                query, tools_list, skills_list, wiki_context, concept_context, episodic_context
            )

        return self._heuristic_fallback(query, tools_list, skills_list)

    async def _llm_decide(
        self,
        query: str,
        tools: list[dict[str, Any]],
        skills: list[dict[str, Any]],
        wiki_context: str,
        concept_context: str,
        episodic_context: str,
    ) -> dict[str, Any]:
        tool_descriptions = "\n".join(
            f"- {t.get('name', '')}: {t.get('description', '')}" for t in tools
        )
        skill_descriptions = "\n".join(
            f"- {s.get('name', '')}: {s.get('description', '')}" for s in skills
        )

        prompt = f"""决定是否使用工具或技能来回答用户查询。

## 可用工具
{tool_descriptions or '(无)'}

## 可用技能
{skill_descriptions or '(无)'}

## 决策规则
1. 技能优于工具
2. 工具优于直接回答
3. 如果直接回答即可，选择 none

## 上下文
{wiki_context[:500] if wiki_context else '(无)'}
{concept_context[:500] if concept_context else '(无)'}

## 用户查询
{query}

请以 JSON 格式回复:
{{"use_tool": true/false, "tool_name": "xxx" or null, "use_skill": true/false, "skill_name": "xxx" or null, "confidence": 0.0-1.0, "reason": "说明", "query_rewrite": "改写后的查询" or null}}"""

        try:
            response = await self._llm_client.complete(
                [{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=256,
            )
            content = response.get("content", "")
            return self._parse_decision(content)
        except Exception:
            return self._heuristic_fallback(query, tools, skills)

    @staticmethod
    def _parse_decision(content: str) -> dict[str, Any]:
        # 3-layer tolerance: direct JSON → regex extraction → conservative fallback
        try:
            result = json.loads(content)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass

        json_match = re.search(r"\{[^}]+\}", content)
        if json_match:
            try:
                result = json.loads(json_match.group(0))
                if isinstance(result, dict):
                    return result
            except json.JSONDecodeError:
                pass

        return {
            "use_tool": False,
            "tool_name": None,
            "use_skill": False,
            "skill_name": None,
            "confidence": 0.3,
            "reason": "fallback: parse failed",
            "query_rewrite": None,
        }

    @staticmethod
    def _heuristic_fallback(
        query: str,
        tools: list[dict[str, Any]],
        skills: list[dict[str, Any]],
    ) -> dict[str, Any]:
        tool_names = [t.get("name", "") for t in tools]
        query_lower = query.lower()

        result: dict[str, Any] = {
            "use_tool": False,
            "tool_name": None,
            "use_skill": False,
            "skill_name": None,
            "confidence": 0.5,
            "reason": "heuristic fallback",
            "query_rewrite": query,
            "fallback_used": True,
        }

        # URLs or "search" keywords → web_search
        if re.search(r"https?://|www\.", query) or any(
            kw in query_lower for kw in ["搜索", "查一下", "搜一下", "search"]
        ):
            if "web_search" in tool_names:
                result.update(use_tool=True, tool_name="web_search", reason="search intent detected")

        # Date mentions → get_todos
        elif any(kw in query_lower for kw in ["今天", "明天", "日期", "待办", "todo"]):
            if "get_todos" in tool_names:
                result.update(use_tool=True, tool_name="get_todos", reason="todo intent detected")

        # Todo creation
        elif any(kw in query for kw in ["添加待办", "记一下", "安排", "提醒我"]):
            if "add_todos" in tool_names:
                result.update(use_tool=True, tool_name="add_todos", reason="add todo intent detected")

        # File reading
        elif any(kw in query_lower for kw in ["读文件", "打开文件", "读取", "read file"]):
            if "read_local_file" in [s.get("name", "") for s in skills]:
                result.update(
                    use_skill=True, skill_name="read_local_file", reason="file read intent"
                )

        # Time queries
        elif any(kw in query_lower for kw in ["几点", "时间", "日期", "星期几"]):
            if "get_current_time" in tool_names:
                result.update(use_tool=True, tool_name="get_current_time", reason="time query")

        return result
