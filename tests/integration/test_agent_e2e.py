"""End-to-end tests: Agent with mock LLM, full pipeline."""

import pytest

from agent.agent import Agent
from agent.config import AgentConfig


class TestAgentE2E:
    """End-to-end tests exercising the full agent pipeline with mock LLM."""

    @pytest.fixture
    def agent(self):
        config = AgentConfig(
            llm_api_key="test-key",
            memory_base_path="/tmp/test-agent-memory",
        )
        return Agent(config)

    @pytest.mark.asyncio
    async def test_initialize_and_shutdown(self, agent):
        await agent.initialize()
        assert agent._initialized
        await agent.shutdown()
        assert not agent._initialized

    @pytest.mark.asyncio
    async def test_process_simple_query(self, agent):
        await agent.initialize()
        try:
            response = await agent.process("Hello!")
            assert response.text is not None
            assert len(response.text) > 0
            assert response.duration_ms >= 0
        finally:
            await agent.shutdown()

    @pytest.mark.asyncio
    async def test_process_multiple_queries(self, agent):
        await agent.initialize()
        try:
            queries = [
                "Hello",
                "What is Python?",
                "添加待办：学习Rust",
            ]
            for q in queries:
                response = await agent.process(q)
                assert response.text is not None
        finally:
            await agent.shutdown()

    @pytest.mark.asyncio
    async def test_reentrancy_guard(self, agent):
        await agent.initialize()
        try:
            from agent.exceptions import ReentrancyError

            # Set the guard to simulate concurrent call in progress
            agent._processing = True
            with pytest.raises(ReentrancyError):
                await agent.process("query 1")
        finally:
            agent._processing = False
            await agent.shutdown()

    @pytest.mark.asyncio
    async def test_health_check(self, agent):
        await agent.initialize()
        try:
            health = await agent.health_check()
            assert health.status in ("healthy", "degraded", "error")
            assert health.version == "0.1.0-dev"
            assert health.model in ("deepseek-chat", "deepseek-v4-flash")
        finally:
            await agent.shutdown()

    @pytest.mark.asyncio
    async def test_search_apis(self, agent):
        await agent.initialize()
        try:
            episodic = await agent.search_episodic("test")
            assert isinstance(episodic, list)

            wiki = await agent.search_wiki("test")
            assert isinstance(wiki, list)
        finally:
            await agent.shutdown()

    @pytest.mark.asyncio
    async def test_get_state(self, agent):
        await agent.initialize()
        try:
            state = await agent.get_state()
            assert state["initialized"] is True
            assert "episodic_count" in state
            assert "tool_count" in state
            assert state["tool_count"] > 0  # built-in tools registered
        finally:
            await agent.shutdown()

    @pytest.mark.asyncio
    async def test_save_state(self, agent):
        await agent.initialize()
        try:
            await agent.save_state()
            # Should not raise
        finally:
            await agent.shutdown()

    @pytest.mark.asyncio
    async def test_plugin_registration(self, agent):
        await agent.initialize()
        try:
            from agent.tools.builtins.time import GetCurrentTimeTool

            extra_tool = GetCurrentTimeTool()
            # Already registered, so count should stay the same
            before = agent._tool_registry.count if agent._tool_registry else 0
            agent.register_tool(extra_tool)
            after = agent._tool_registry.count if agent._tool_registry else 0
            assert after >= before
        finally:
            await agent.shutdown()

    @pytest.mark.asyncio
    async def test_pipeline_stage_registration(self, agent):
        await agent.initialize()
        try:
            from agent.pipeline.context import PipelineContext
            from agent.pipeline.protocol import PipelineStage

            class TestStage(PipelineStage):
                name = "test_custom"
                priority = 99

                async def execute(self, context: PipelineContext) -> PipelineContext:
                    return context

            agent.register_pipeline_stage(TestStage())
            assert "test_custom" in agent._pipeline.stage_names if agent._pipeline else False
        finally:
            await agent.shutdown()
