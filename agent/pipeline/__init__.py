"""Pipeline — ordered stage sequence executor."""

from agent.pipeline.context import PipelineContext, StageError
from agent.pipeline.pipeline import Pipeline
from agent.pipeline.protocol import PipelineStage

__all__ = ["Pipeline", "PipelineStage", "PipelineContext", "StageError"]
