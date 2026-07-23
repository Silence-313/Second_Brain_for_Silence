"""Memory writer — post-interaction classification, consolidation, and persistence."""

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from agent.concepts.extractor import ConceptExtractor
from agent.memory.episodic import EpisodicMemory
from agent.memory.profile import UserProfile
from agent.memory.store import MemoryStore
from agent.memory.tool_stats import ToolMemory
from agent.models.memory import Episode, MemoryWriteDecision


class Interaction(BaseModel, frozen=True):
    user_message: str
    assistant_response: str = ""
    tool_used: str | None = None
    tool_result: str | None = None
    router_confidence: float = 0.5
    timestamp: datetime = Field(default_factory=datetime.now)


# Profile regex patterns (Chinese + English)
_NAME_RE = re.compile(r"(?:我是|我叫|I am|I'm)\s*(.+)", re.IGNORECASE)
_ROLE_RE = re.compile(r"(?:我(?:在)?(?:做|从事|负责|是(?:一个|一名)?))\s*(.+)")
_INTEREST_RE = re.compile(r"(?:我喜欢|我对|我的爱好|我(?:很)?感兴趣|I like|I love|I enjoy)\s*(.+)")
_TOOLS_RE = re.compile(r"(?:我(?:在)?用|我使用|I use|我用过)\s*(.+)")
_PROJECT_RE = re.compile(r"(?:我的(?:项目|工作)|My project|I(?:'m| am) working on)\s*(.+)")
_GOAL_RE = re.compile(r"(?:目标|计划|打算|想要|希望|决定|Goal|Plan|Decide|Want to|Will)")
_MILESTONE_RE = re.compile(r"(?:完成|达成|里程碑|实现|Milestone|Achieved|Completed)")


def _jaccard_bigrams(a: str, b: str) -> float:
    def bigrams(s: str) -> set[str]:
        return {s[i : i + 2] for i in range(len(s) - 1)} if len(s) >= 2 else set()

    ba = bigrams(a.lower())
    bb = bigrams(b.lower())
    if not ba or not bb:
        return 0.0
    return len(ba & bb) / len(ba | bb)


class MemoryWriter:
    """Post-interaction classifier and persistence coordinator."""

    def __init__(
        self,
        episodic: EpisodicMemory,
        profile: UserProfile,
        tool_memory: ToolMemory,
        store: MemoryStore,
        concept_extractor: ConceptExtractor | None = None,
        mutation_queue: object | None = None,
    ) -> None:
        self._episodic = episodic
        self._profile = profile
        self._tool_memory = tool_memory
        self._store = store
        self._extractor = concept_extractor or ConceptExtractor()
        self._mutation_queue = mutation_queue

    def analyze(self, interaction: Interaction) -> list[MemoryWriteDecision]:
        decisions: list[MemoryWriteDecision] = []
        msg = interaction.user_message

        decisions.extend(self._analyze_profile(msg))
        decisions.extend(self._analyze_episodic(msg))
        decisions.extend(self._analyze_semantic(msg))
        decisions.append(self._analyze_tool(interaction))

        return decisions

    async def commit(
        self, decisions: list[MemoryWriteDecision], interaction: Interaction
    ) -> None:
        for decision in decisions:
            if decision.action == "ignore":
                continue

            if decision.type == "profile":
                if decision.target_field and decision.detected_value:
                    self._profile.set(
                        decision.target_field,
                        decision.detected_value,
                        decision.confidence,
                    )

            elif decision.type in ("episodic", "semantic"):
                entry = Episode(
                    id=f"ep-{int(interaction.timestamp.timestamp() * 1000)}-{decision.type}",
                    timestamp=interaction.timestamp,
                    type=self._classify_episode_type(interaction),
                    summary=self._make_summary(interaction, decision),
                    detail=f"Q: {interaction.user_message}\nA: {interaction.assistant_response}",
                    importance=decision.importance,
                    tags=self._extract_tags(interaction, decision),
                )

                # Consolidation check
                consolidated = self._consolidate(entry)
                if consolidated:
                    continue

                self._episodic.add(entry)

                if decision.action == "append" and decision.importance >= 0.4:
                    try:
                        await self._store.write_episode(entry)
                    except Exception:
                        pass

                concepts = self._extractor.extract(
                    entry.detail,
                    [],  # existing concepts loaded separately
                )
                for concept in concepts:
                    if concept.confidence >= 0.4:
                        from agent.models.concepts import Concept

                        c = Concept(
                            id=f"concept-{concept.slug}",
                            name=concept.name,
                            slug=concept.slug,
                            confidence=concept.confidence,
                            source_episodes=[entry.id],
                        )
                        try:
                            await self._store.upsert_concept(c)
                        except Exception:
                            pass

            elif decision.type == "tool":
                self._tool_memory.record_call(
                    tool_name=interaction.tool_used or "unknown",
                    success=True,
                    query=interaction.user_message,
                )

    def run_maintenance(self) -> int:
        return self._episodic.apply_decay()

    # -- Private analysis methods --

    def _analyze_profile(self, msg: str) -> list[MemoryWriteDecision]:
        decisions: list[MemoryWriteDecision] = []

        for pattern, field, imp in [
            (_NAME_RE, "name", 0.8),
            (_ROLE_RE, "role", 0.7),
            (_INTEREST_RE, "interests", 0.6),
            (_TOOLS_RE, "common_tools", 0.6),
            (_PROJECT_RE, "active_projects", 0.7),
        ]:
            m = pattern.search(msg)
            if m:
                value = m.group(1).strip().rstrip("。，. ,")
                if value and len(value) > 1 and len(value) < 100:
                    decisions.append(
                        MemoryWriteDecision(
                            type="profile",
                            importance=imp,
                            action="append",
                            target_field=field,
                            detected_value=value,
                            confidence=imp,
                            reason=f"regex match: {pattern.pattern[:40]}",
                        )
                    )

        return decisions

    def _analyze_episodic(self, msg: str) -> list[MemoryWriteDecision]:
        decisions: list[MemoryWriteDecision] = []

        if _GOAL_RE.search(msg):
            decisions.append(
                MemoryWriteDecision(
                    type="episodic",
                    importance=0.7,
                    action="append",
                    reason="goal keyword detected",
                )
            )
        elif _MILESTONE_RE.search(msg):
            decisions.append(
                MemoryWriteDecision(
                    type="episodic",
                    importance=0.8,
                    action="append",
                    reason="milestone keyword detected",
                )
            )

        return decisions

    def _analyze_semantic(self, msg: str) -> list[MemoryWriteDecision]:
        if len(msg) > 80 and any(kw in msg for kw in ["是", "就是", "意味着", "定义", "概念"]):
            return [
                MemoryWriteDecision(
                    type="semantic",
                    importance=0.4,
                    action="append",
                    reason="factual statement detected",
                )
            ]
        return []

    def _analyze_tool(self, interaction: Interaction) -> MemoryWriteDecision:
        if interaction.tool_used:
            return MemoryWriteDecision(
                type="tool",
                importance=0.3,
                action="append",
                reason=f"tool used: {interaction.tool_used}",
            )
        return MemoryWriteDecision(
            type="tool", importance=0.0, action="ignore", reason="no tool"
        )

    def _consolidate(self, new_entry: Episode) -> bool:
        existing = self._episodic.get_active_entries()
        for ex in existing:
            combined = f"{new_entry.summary} {new_entry.detail}"
            existing_text = f"{ex.summary} {ex.detail}"
            sim = _jaccard_bigrams(combined, existing_text)
            if sim > 0.85:
                self._episodic.reinforce(ex.id, 0.02)
                return True
        return False

    @staticmethod
    def _classify_episode_type(
        interaction: Interaction,
    ) -> Literal["event", "goal", "decision", "milestone", "question"]:
        msg = interaction.user_message
        if _GOAL_RE.search(msg):
            return "goal"
        if _MILESTONE_RE.search(msg):
            return "milestone"
        if any(kw in msg for kw in ["决定", "选择", "决定要", "Decide"]):
            return "decision"
        return "event"

    @staticmethod
    def _make_summary(interaction: Interaction, decision: MemoryWriteDecision) -> str:
        msg = interaction.user_message
        if len(msg) <= 80:
            return msg
        return msg[:77] + "..."

    @staticmethod
    def _extract_tags(interaction: Interaction, decision: MemoryWriteDecision) -> list[str]:
        tags: list[str] = [decision.type]
        msg = interaction.user_message
        tag_keywords = {
            "code": ["代码", "编程", "code", "programming", "python", "java", "go", "rust"],
            "ai": ["ai", "人工智能", "机器学习", "深度学习", "llm", "模型", "agent"],
            "knowledge": ["知识", "笔记", "学习", "阅读", "read", "study", "wiki"],
            "tool": ["工具", "软件", "tool", "app", "安装", "配置"],
        }
        msg_lower = msg.lower()
        for tag, keywords in tag_keywords.items():
            if any(kw in msg_lower for kw in keywords):
                tags.append(tag)
        return tags[:5]
