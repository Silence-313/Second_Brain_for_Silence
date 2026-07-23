"""Intent parser — keyword + pattern based intent classification. No LLM."""

from typing import Any

from agent.planner.plan import Intent

_INTENT_RULES: list[dict[str, Any]] = [
    # Bilibili / video search
    {
        "keywords": ["b站", "bilibili", "哔哩", "视频", "弹幕", "up主", "B站", "bil"],
        "patterns": [r"[Bb]站.*搜", r"搜.*[Bb]站", r"bilibili.*搜", r"搜.*bilibili", r"搜.*视频", r"看.*视频"],
        "action": "search",
        "domain": "video",
        "platform": "bilibili",
    },
    # GitHub / code search
    {
        "keywords": ["github", "git", "repo", "仓库", "开源", "代码库"],
        "patterns": [r"github.*搜", r"搜.*github", r"找.*开源", r"搜.*代码"],
        "action": "search",
        "domain": "code",
        "platform": "github",
    },
    # ArXiv / paper search
    {
        "keywords": ["论文", "paper", "arxiv", "学术", "文献", "期刊"],
        "patterns": [r"搜.*论文", r"找.*论文", r"arxiv.*搜", r"搜.*paper"],
        "action": "search",
        "domain": "paper",
        "platform": "arxiv",
    },
    # Obsidian / knowledge
    {
        "keywords": ["笔记", "obsidian", "知识库", "wiki", "我的笔记", "查笔记"],
        "patterns": [r"笔记.*有", r"查.*笔记", r"wiki.*搜"],
        "action": "read",
        "domain": "knowledge",
        "platform": "obsidian",
    },
    # Local file
    {
        "keywords": ["文件", "本地", "文件夹", "读取", "打开文件"],
        "patterns": [r"读.*文件", r"打开.*文件", r"看.*文件"],
        "action": "read",
        "domain": "local_file",
        "platform": "local",
    },
    # Code writing
    {
        "keywords": ["写代码", "编程", "函数", "class", "def", "实现", "代码", "帮我写"],
        "patterns": [r"写.*(?:函数|代码|程序|脚本)", r"帮我写", r"实现.*功能"],
        "action": "write",
        "domain": "code",
        "platform": "none",
    },
    # Web search
    {
        "keywords": ["搜索", "查一下", "网上", "搜", "查找", "帮我查"],
        "patterns": [r"搜.*一下", r"查.*一下"],
        "action": "search",
        "domain": "general",
        "platform": "web",
    },
    # Analysis
    {
        "keywords": ["分析", "总结", "归纳", "梳理", "概括"],
        "patterns": [r"分析.*一下", r"总结.*一下"],
        "action": "analyze",
        "domain": "general",
        "platform": "none",
    },
    # Summarization
    {
        "keywords": ["摘要", "简述", "简单说", "概括一下"],
        "patterns": [r"简单.*说一下", r"概括.*一下"],
        "action": "summarize",
        "domain": "general",
        "platform": "none",
    },
    # Knowledge base maintenance
    {
        "keywords": ["维护", "整理知识", "消化对话", "整理笔记", "知识管理"],
        "patterns": [r"维护.*知识", r"整理.*知识", r"消化.*对话", r"整理.*笔记"],
        "action": "maintain",
        "domain": "knowledge",
        "platform": "none",
    },
]


class IntentParser:
    """Parse user query into structured Intent without LLM."""

    def parse(self, query: str, context: Any = None) -> Intent:  # MemoryContext | None
        if not query.strip():
            return Intent(action="chat", domain="general", platform="none", confidence=0.5, query=query)

        best_match: dict[str, Any] | None = None
        best_score: float = 0.0

        query_lower = query.lower()

        for rule in _INTENT_RULES:
            score: float = 0.0

            for kw in rule.get("keywords", []):
                if kw in query_lower:
                    score += 1.0 + (0.3 if kw in query_lower.split() else 0)

            for pat in rule.get("patterns", []):
                import re

                if re.search(pat, query):
                    score += 2.5

            if score > best_score:
                best_score = score
                best_match = rule

        if best_match is None or best_score < 0.5:
            # Check if it's a simple greeting
            greetings = ["你好", "hi", "hello", "嗨", "hey", "早上好", "晚上好", "下午好"]
            if any(g in query_lower for g in greetings):
                return Intent(
                    action="chat", domain="general", platform="none", confidence=0.9, query=query
                )
            return Intent(
                action="chat", domain="general", platform="none", confidence=0.4, query=query
            )

        confidence = min(1.0, best_score / 8.0)
        return Intent(
            action=best_match["action"],
            domain=best_match["domain"],
            platform=best_match["platform"],
            confidence=round(confidence, 4),
            query=query,
        )
