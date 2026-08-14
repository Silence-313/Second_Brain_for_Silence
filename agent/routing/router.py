"""Tool router — fast deterministic keyword-scoring intent classifier."""

import re

from agent.models.routing import RouterResult, ToolMetrics

_TOOL_PATTERNS: dict[str, dict[str, object]] = {
    "add_todos": {
        "weight": 1.0,
        "keywords": [
            "添加待办",
            "安排",
            "计划",
            "加入待办",
            "新增任务",
            "待办事项",
            "提醒我",
            "创建任务",
            "add todo",
            "创建待办",
            "记一下",
        ],
        "exclusives": ["添加待办", "add todo", "记一下"],
        "patterns": [re.compile(r"添加.*待办"), re.compile(r"记.*一下"), re.compile(r"add.*todo")],
    },
    "get_todos": {
        "weight": 0.9,
        "keywords": [
            "待办",
            "任务列表",
            "进度",
            "还有什么",
            "查看待办",
            "今天要做什么",
            "还有什么事",
            "待办事项",
            "任务进度",
            "get todo",
            "还有哪些",
        ],
        "exclusives": ["查看待办", "还有什么事", "今天要做什么"],
        "patterns": [
            re.compile(r"查看.*待办"),
            re.compile(r"还有.*什么"),
            re.compile(r"今天.*做什么"),
        ],
    },
    "get_current_time": {
        "weight": 0.85,
        "keywords": [
            "几点",
            "日期",
            "时间",
            "今天几号",
            "星期几",
            "现在几点",
            "当前时间",
            "今天日期",
            "what time",
            "几月几号",
        ],
        "exclusives": ["几点", "日期", "现在几点"],
        "patterns": [re.compile(r"现在.*几点"), re.compile(r"今天.*几号"), re.compile(r"星期几")],
    },
    "web_search": {
        "weight": 0.7,
        "keywords": [
            "搜索",
            "查一下",
            "最新",
            "网上",
            "搜索引擎",
            "查找",
            "帮我查",
            "搜一下",
            "search",
            "查一查",
            "帮我搜",
            "帮我找",
            "查查",
            "最近新闻",
            "有没有关于",
        ],
        "exclusives": ["搜索", "搜一下", "帮我查"],
        "patterns": [re.compile(r"搜索.*一下"), re.compile(r"帮我查.*"), re.compile(r"搜.*一下")],
    },
    "wiki_search": {
        "weight": 0.75,
        "keywords": [
            "笔记",
            "知识库",
            "我记得",
            "之前记过",
            "wiki",
            "我的笔记",
            "查笔记",
            "记录",
            "知识",
            "我记",
            "看看笔记",
        ],
        "exclusives": ["笔记", "知识库", "wiki"],
        "patterns": [re.compile(r"笔记.*有"), re.compile(r"我.*记过"), re.compile(r"知识库.*有")],
    },
    "memory_search": {
        "weight": 0.6,
        "keywords": [
            "记得",
            "回忆",
            "之前",
            "上次",
            "以前说过",
            "你还记得",
            "想起",
            "记忆",
            "不记得",
            "忘了",
            "remember",
        ],
        "exclusives": ["记得", "回忆", "你还记得"],
        "patterns": [re.compile(r"你还记得"), re.compile(r"之前.*说过"), re.compile(r"上次.*说过")],
    },
    "kb_maintain": {
        "weight": 0.9,
        "keywords": [
            "维护知识库",
            "整理知识",
            "消化对话",
            "更新知识库",
            "整理笔记",
            "知识库维护",
        ],
        "exclusives": ["维护知识库", "知识库维护"],
        "patterns": [
            re.compile(r"维护.*知识"),
            re.compile(r"整理.*知识"),
            re.compile(r"消化.*对话"),
        ],
    },
}


class ToolRouter:
    """Fast deterministic intent classification. No LLM dependency."""

    def __init__(self) -> None:
        self._default_telemetry: dict[str, ToolMetrics] = {}

    def route_tool(
        self, query: str, telemetry: dict[str, ToolMetrics] | None = None
    ) -> RouterResult:
        if telemetry is None:
            telemetry = {}

        best_tool: str | None = None
        best_score: float = 0.0
        best_reason: str = ""

        for tool, pattern_def in _TOOL_PATTERNS.items():
            score = self._score_tool(query, pattern_def)

            weight_raw = pattern_def.get("weight", 0.5)
            weight = float(weight_raw) if isinstance(weight_raw, (int, float)) else 0.5
            score *= weight

            threshold = self._get_threshold(tool, telemetry)
            if score >= threshold and score > best_score:
                best_score = score
                best_tool = tool
                best_reason = self._build_reason(query, pattern_def, score)

        if best_tool is None:
            return RouterResult(
                tool="memory_search",
                confidence=0.3,
                reason="no match, default to memory_search",
            )

        max_possible = float(_TOOL_PATTERNS.get(best_tool, {}).get("weight", 0.5)) * 5  # type: ignore[arg-type]
        confidence = min(1.0, best_score / max(max_possible, 1))
        return RouterResult(tool=best_tool, confidence=round(confidence, 4), reason=best_reason)

    @staticmethod
    def _score_tool(query: str, pattern_def: dict[str, object]) -> float:
        score: float = 0.0
        query_lower = query.lower()

        keywords = pattern_def.get("keywords", [])
        if isinstance(keywords, list):
            for kw in keywords:
                if isinstance(kw, str) and kw in query_lower:
                    score += 1.0

        exclusives = pattern_def.get("exclusives", [])
        if isinstance(exclusives, list):
            for ex in exclusives:
                if isinstance(ex, str) and ex in query_lower:
                    score += 3.0

        patterns = pattern_def.get("patterns", [])
        if isinstance(patterns, list):
            for pat in patterns:
                if isinstance(pat, re.Pattern) and pat.search(query):
                    score += 2.0

        return score

    @staticmethod
    def _get_threshold(tool_name: str, telemetry: dict[str, ToolMetrics]) -> float:
        metrics = telemetry.get(tool_name)
        if metrics is None:
            return 0.2
        return max(0.1, min(0.6, 0.2 + (1 - metrics.success_rate) * 0.4))

    @staticmethod
    def _build_reason(query: str, pattern_def: dict[str, object], score: float) -> str:
        matched: list[str] = []
        query_lower = query.lower()

        keywords = pattern_def.get("keywords", [])
        if isinstance(keywords, list):
            for kw in keywords:
                if isinstance(kw, str) and kw in query_lower:
                    matched.append(kw)

        if matched:
            return f"matched keywords: {', '.join(matched[:5])} (score={score:.1f})"
        return f"pattern matched (score={score:.1f})"
