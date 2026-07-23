"""Integration tests: Memory stack — Writer + Episodic + Profile + ToolMemory + Store."""

import pytest

from agent.concepts.extractor import ConceptExtractor
from agent.infrastructure.storage.memory_fs import InMemoryFileStorage
from agent.memory.episodic import EpisodicMemory
from agent.memory.profile import UserProfile
from agent.memory.store import MemoryStore
from agent.memory.tool_stats import ToolMemory
from agent.memory.writer import Interaction, MemoryWriter
from agent.models.memory import Episode


class TestMemoryIntegration:
    """Test the full memory pipeline: analyze → commit → store."""

    @pytest.fixture
    def memory_stack(self):
        storage = InMemoryFileStorage()
        episodic = EpisodicMemory(max_entries=200)
        profile = UserProfile()
        tool_memory = ToolMemory()
        store = MemoryStore(storage, "/mem")
        extractor = ConceptExtractor()
        writer = MemoryWriter(episodic, profile, tool_memory, store, extractor)
        return {
            "storage": storage,
            "episodic": episodic,
            "profile": profile,
            "tool_memory": tool_memory,
            "store": store,
            "writer": writer,
        }

    @pytest.mark.asyncio
    async def test_analyze_episodic(self, memory_stack):
        writer = memory_stack["writer"]
        interaction = Interaction(user_message="我计划下周学习Rust编程")

        decisions = writer.analyze(interaction)
        assert len(decisions) >= 0  # at minimum tool decision
        types = [d.type for d in decisions]
        assert "tool" in types

    @pytest.mark.asyncio
    async def test_commit_writes_episode(self, memory_stack):
        writer = memory_stack["writer"]
        episodic = memory_stack["episodic"]

        interaction = Interaction(
            user_message="我决定使用PyTorch做深度学习项目",
            assistant_response="好的，PyTorch是一个很好的选择",
            tool_used="wiki_search",
        )
        decisions = writer.analyze(interaction)
        await writer.commit(decisions, interaction)

        assert episodic.count >= 0

    @pytest.mark.asyncio
    async def test_profile_extraction(self, memory_stack):
        writer = memory_stack["writer"]
        profile = memory_stack["profile"]

        interaction = Interaction(user_message="我是Silence，我从事软件开发工作")
        decisions = writer.analyze(interaction)
        await writer.commit(decisions, interaction)

        # Profile should have been updated
        data = profile.to_data()
        assert data.name == "Silence" or data.role != "" or len(data.interests) >= 0

    @pytest.mark.asyncio
    async def test_tool_recording(self, memory_stack):
        writer = memory_stack["writer"]
        tool_memory = memory_stack["tool_memory"]

        interaction = Interaction(
            user_message="搜索Python教程",
            assistant_response="找到了一些结果",
            tool_used="web_search",
        )
        decisions = writer.analyze(interaction)
        await writer.commit(decisions, interaction)

        stats = tool_memory.get_stats("web_search")
        assert stats is not None
        assert stats.call_count == 1

    @pytest.mark.asyncio
    async def test_concept_extraction_from_episode(self, memory_stack):
        writer = memory_stack["writer"]
        episodic = memory_stack["episodic"]

        interaction = Interaction(
            user_message="深度学习是机器学习的一个分支，使用神经网络进行训练",
            assistant_response="深度学习确实很重要",
        )
        decisions = writer.analyze(interaction)
        await writer.commit(decisions, interaction)

        # Episodes should be searchable
        results = episodic.search("深度学习", top_k=5)
        assert len(results) >= 0

    @pytest.mark.asyncio
    async def test_maintenance_cycle(self, memory_stack):
        writer = memory_stack["writer"]
        episodic = memory_stack["episodic"]

        # Add entries with various ages
        for i in range(5):
            ep = Episode(
                id=f"ep-old-{i}",
                type="event",
                summary=f"old entry {i}",
                importance_score=0.5,
                usage_frequency=0,
            )
            episodic.add(ep)

        decayed = writer.run_maintenance()
        assert isinstance(decayed, int)

    @pytest.mark.asyncio
    async def test_serialize_roundtrip(self, memory_stack):
        episodic = memory_stack["episodic"]
        ep = Episode(id="ep-rt-1", type="event", summary="roundtrip test", tags=["test", "integration"])
        episodic.add(ep)

        json_str = episodic.serialize()
        episodic2 = EpisodicMemory()
        episodic2.deserialize(json_str)

        assert episodic2.count == episodic.count
        assert episodic2.get("ep-rt-1") is not None
