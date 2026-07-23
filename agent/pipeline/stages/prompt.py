"""Prompt stage — assemble system prompt from gathered context."""

from datetime import UTC, datetime
from typing import Any

from agent.pipeline.context import PipelineContext
from agent.pipeline.protocol import PipelineStage

_RULES = [
    "你是 Silence 的第二大脑，不是通用 AI 助手。你的回答应当体现对他的了解",
    "优先根据概念推理和记忆中的知识组织回答",
    "基于知识库和情景记忆内容回答，注明来源",
    "知识库没有时基于常识但要说明「根据常识推测」",
    "提到 Silence 相关的事时，引用记忆中的上下文",
    "使用可用工具获取实时数据",
    "不编造不存在的内容",
    "绝对禁止 Markdown 表格，用列表代替表格",
    "用 **键**: 值 代替键值对",
    "绝对禁止伪造 URL、链接、GitHub 仓库名。只引用上下文中真实出现过的链接",
    "绝对禁止在回复中假装「正在搜索…」「Searching for…」「我先用搜索工具…」等工具调用过程。工具已经执行完毕，你只需要引用结果",
    "如果执行结果为空或你没有找到有效信息，诚实地告诉用户，给出替代建议",
    "如果用户说「搜」「搜一下」「给我链接」，你的上下文已经包含了搜索结果，直接引用即可，不要重复执行或假装正在执行",
]

_IDENTITY = """你是 Silence 的个人第二大脑（Second Brain）。

你不是一个通用 AI 助手。你的存在意义是作为 Silence 认知能力的延伸——帮他记忆、推理、连接想法、管理知识。

你了解 Silence 的工作习惯、兴趣领域、项目进展。你会主动关联他过去的想法和当前的问题。你的回答风格直接、高效，不啰嗦，像一个了解他的老搭档。

你有记忆系统：情景记忆记录他的事件和决策，概念系统构建他的知识图谱，策略系统持续演化以更好地服务他。

记住：你是 Silence 的第二大脑，不是 DeepSeek，不是豆包，不是任何其他 AI 服务。如果有人问你是谁，回答你是 Silence 的第二大脑。"""


class PromptStage(PipelineStage):
    name = "prompt"
    priority = 7

    def __init__(self, max_chars: int = 8000, kb_manager: Any = None) -> None:
        self._max_chars = max_chars
        self._kb = kb_manager

    async def execute(self, context: PipelineContext) -> PipelineContext:
        now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
        sections = [_IDENTITY, f"当前时间: {now}"]

        mc = context.memory_context or {}

        # Knowledge Base context (llm-wiki)
        if self._kb is not None:
            try:
                overview = await self._kb.read_overview()
                if overview and len(overview) > 100:
                    sections.append(f"## 你的知识库总览\n{overview[:2000]}")
            except Exception:
                pass

        # Profile context
        profile = mc.get("profile_context", "")
        if profile:
            sections.append(profile)

        # Wiki results
        wiki_results = mc.get("wiki_results", [])
        if wiki_results:
            wiki_lines = ["## 知识库相关结果"]
            for r in wiki_results[:3]:
                if hasattr(r, "content"):
                    wiki_lines.append(f"- [{getattr(r, 'source_path', '')}] {r.content[:200]}")
            sections.append("\n".join(wiki_lines))

        # Episodic context
        episodic = mc.get("episodic_context", "")
        if episodic:
            sections.append(episodic)

        # Concept reasoning
        reasoning = mc.get("reasoning_context")
        if reasoning and hasattr(reasoning, "key_concepts") and reasoning.key_concepts:
            lines = ["## 概念推理上下文"]
            lines.append(f"关键概念: {', '.join(reasoning.key_concepts[:8])}")
            if hasattr(reasoning, "inferred_insights") and reasoning.inferred_insights:
                lines.append(
                    "推理洞察: " + "; ".join(reasoning.inferred_insights[:3])
                )
            sections.append("\n".join(lines))

        # Execution results
        exec_result = context.execution_result
        if exec_result and hasattr(exec_result, "results"):
            lines = ["## 工具执行结果"]
            for step_id, r in exec_result.results.items():
                status = "成功" if getattr(r, "success", False) else "失败"
                data = getattr(r, "data", None)
                lines.append(f"- {step_id}: {status}")
                if data and isinstance(data, dict):
                    results_list = data.get("results", [])
                    if results_list:
                        lines.append("  搜索结果（直接引用以下链接和摘要回答用户）：")
                        for i, sr in enumerate(results_list[:8]):
                            title = sr.get("title", "") if isinstance(sr, dict) else ""
                            url = sr.get("url", "") if isinstance(sr, dict) else ""
                            snippet = sr.get("snippet", "") if isinstance(sr, dict) else ""
                            lines.append(f"  {i+1}. {title}")
                            if url:
                                lines.append(f"     URL: {url}")
                            if snippet:
                                lines.append(f"     摘要: {snippet[:150]}")
                    else:
                        lines.append(f"  结果: {str(data)[:200]}")
                elif data:
                    lines.append(f"  结果: {str(data)[:200]}")
            sections.append("\n".join(lines))

        # Rules
        rules_section = "## 规则\n" + "\n".join(f"- {r}" for r in _RULES)
        sections.append(rules_section)

        prompt = "\n\n".join(sections)

        if len(prompt) > self._max_chars:
            excess = len(prompt) - self._max_chars
            wiki_start = prompt.find("## 知识库")
            if wiki_start > 0 and excess > 0:
                wiki_end = prompt.find("## 相关记忆", wiki_start)
                if wiki_end < 0:
                    wiki_end = prompt.find("## 概念推理", wiki_start)
                if wiki_end > wiki_start:
                    mid = prompt[wiki_start:wiki_end]
                    truncated = mid[: max(0, len(mid) - excess - 50)]
                    prompt = prompt[:wiki_start] + truncated + prompt[wiki_end:]

            prompt = prompt[: self._max_chars]

        return context.with_updates(system_prompt=prompt)
