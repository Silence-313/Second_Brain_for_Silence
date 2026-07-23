"""Integration tests: Pipeline — multiple stages working together."""


import pytest

from agent.infrastructure.llm.mock import MockLLMClient
from agent.pipeline.context import PipelineContext
from agent.pipeline.pipeline import Pipeline
from agent.pipeline.stages.generate import GenerateStage
from agent.pipeline.stages.prompt import PromptStage
from agent.pipeline.stages.sanitize import SanitizeStage
from agent.pipeline.stages.sanitize_response import ResponseSanitizeStage


class TestPipelineIntegration:
    """Test pipeline stages chained together."""

    @pytest.fixture
    def pipeline_stages(self):
        mock_llm = MockLLMClient(responses=["Hello! I am an AI assistant. How can I help you?"])
        return [
            SanitizeStage(max_chars=4000),
            PromptStage(max_chars=8000),
            GenerateStage(llm_client=mock_llm),
            ResponseSanitizeStage(),
        ]

    @pytest.mark.asyncio
    async def test_sanitize_to_generate_flow(self, pipeline_stages):
        pipeline = Pipeline(pipeline_stages)
        ctx = PipelineContext(
            session_id="test-session",
            user_input_raw="Hello, how are you?",
        )
        result = await pipeline.execute(ctx)

        assert result.llm_response_clean is not None
        assert len(result.llm_response_clean) > 0
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_code_block_sanitization(self, pipeline_stages):
        pipeline = Pipeline(pipeline_stages[:1] + pipeline_stages[1:])  # sanitize + rest
        ctx = PipelineContext(
            session_id="test-session",
            user_input_raw="Help me with ```print('hello')``` code",
        )
        result = await pipeline.execute(ctx)
        assert result.user_input_sanitized is not None
        assert "[code removed]" in result.user_input_sanitized

    @pytest.mark.asyncio
    async def test_llm_error_graceful(self):
        mock_llm = MockLLMClient(responses=["OK"])
        stages = [GenerateStage(llm_client=mock_llm)]
        pipeline = Pipeline(stages)

        ctx = PipelineContext(session_id="test", user_input_raw="test")
        result = await pipeline.execute(ctx)
        assert result.llm_response is not None

    @pytest.mark.asyncio
    async def test_pipeline_timing(self, pipeline_stages):
        pipeline = Pipeline(pipeline_stages)
        ctx = PipelineContext(session_id="test", user_input_raw="timing test")
        result = await pipeline.execute(ctx)

        assert len(result.stage_timings) > 0
        for _stage_name, duration in result.stage_timings.items():
            assert duration >= 0

    @pytest.mark.asyncio
    async def test_system_prompt_built(self):
        mock_llm = MockLLMClient(responses=["Test response."])
        stages = [
            SanitizeStage(),
            PromptStage(),
            GenerateStage(llm_client=mock_llm),
        ]
        pipeline = Pipeline(stages)
        ctx = PipelineContext(session_id="s1", user_input_raw="What is machine learning?")
        result = await pipeline.execute(ctx)

        assert result.system_prompt is not None
        assert "当前时间" in result.system_prompt
        assert "规则" in result.system_prompt
