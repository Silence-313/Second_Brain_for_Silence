"""Tests for Pipeline and PipelineContext."""

from agent.pipeline.context import PipelineContext
from agent.pipeline.pipeline import Pipeline
from agent.pipeline.protocol import PipelineStage
from agent.pipeline.stages.sanitize import SanitizeStage


class _SimpleStage(PipelineStage):
    name = "test_stage"
    priority = 1

    async def execute(self, context: PipelineContext) -> PipelineContext:
        return context.with_updates(user_input_sanitized="processed")


class _FailingStage(PipelineStage):
    name = "failing_stage"
    priority = 2

    async def execute(self, context: PipelineContext) -> PipelineContext:
        raise RuntimeError("stage failure")


class TestPipelineContext:
    def test_create_default(self) -> None:
        ctx = PipelineContext(session_id="s1", user_input_raw="hello")
        assert ctx.session_id == "s1"
        assert ctx.user_input_raw == "hello"

    def test_with_updates(self) -> None:
        ctx = PipelineContext(session_id="s1", user_input_raw="hello")
        ctx2 = ctx.with_updates(user_input_sanitized="HELLO")
        assert ctx2.user_input_sanitized == "HELLO"
        # Original is unchanged
        assert ctx.user_input_sanitized is None

    def test_with_error(self) -> None:
        ctx = PipelineContext(session_id="s1", user_input_raw="hello")
        ctx2 = ctx.with_error("test_stage", "something went wrong")
        assert len(ctx2.errors) == 1
        assert ctx2.errors[0].stage == "test_stage"

    def test_with_timing(self) -> None:
        ctx = PipelineContext(session_id="s1", user_input_raw="hello")
        ctx2 = ctx.with_timing("sanitize", 42.5)
        assert ctx2.stage_timings["sanitize"] == 42.5


class TestPipeline:
    def test_execute_stages(self) -> None:
        pipeline = Pipeline([_SimpleStage()])
        ctx = PipelineContext(session_id="s1", user_input_raw="hello")

        import asyncio
        result = asyncio.run(pipeline.execute(ctx))
        assert result.user_input_sanitized == "processed"

    def test_error_isolation(self) -> None:
        pipeline = Pipeline([_FailingStage()])
        ctx = PipelineContext(session_id="s1", user_input_raw="hello")

        import asyncio
        result = asyncio.run(pipeline.execute(ctx))
        assert len(result.errors) == 1
        assert result.errors[0].stage == "failing_stage"

    def test_stage_sorting(self) -> None:
        class StageA(PipelineStage):
            name = "a"
            priority = 10
            async def execute(self, context: PipelineContext) -> PipelineContext:
                return context
        class StageB(PipelineStage):
            name = "b"
            priority = 5
            async def execute(self, context: PipelineContext) -> PipelineContext:
                return context

        pipeline = Pipeline([StageA(), StageB()])
        assert pipeline.stage_names == ["b", "a"]

    def test_add_stage(self) -> None:
        pipeline = Pipeline([])
        pipeline.add_stage(_SimpleStage())
        assert "test_stage" in pipeline.stage_names

    def test_remove_stage(self) -> None:
        pipeline = Pipeline([_SimpleStage()])
        assert pipeline.remove_stage("test_stage")
        assert "test_stage" not in pipeline.stage_names

    def test_remove_nonexistent(self) -> None:
        pipeline = Pipeline([])
        assert not pipeline.remove_stage("nonexistent")


class TestSanitizeStage:
    def test_sanitize_code_blocks(self) -> None:
        stage = SanitizeStage()
        ctx = PipelineContext(session_id="s1", user_input_raw="hello ```code``` world")
        import asyncio
        result = asyncio.run(stage.execute(ctx))
        assert "[code removed]" in (result.user_input_sanitized or "")

    def test_truncate(self) -> None:
        stage = SanitizeStage(max_chars=10)
        ctx = PipelineContext(session_id="s1", user_input_raw="a" * 50)
        import asyncio
        result = asyncio.run(stage.execute(ctx))
        assert len(result.user_input_sanitized or "") <= 10
