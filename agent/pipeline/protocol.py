"""Pipeline stage protocol."""

from abc import ABC, abstractmethod

from agent.pipeline.context import PipelineContext


class PipelineStage(ABC):
    """A single step in the request processing pipeline."""

    name: str = ""
    priority: int = 0

    @abstractmethod
    async def execute(self, context: PipelineContext) -> PipelineContext:
        """Execute the stage and return updated context."""
        ...

    async def on_startup(self) -> None:
        """Called once at agent init. Override in subclasses."""
        return

    async def on_shutdown(self) -> None:
        """Called once at agent shutdown. Override in subclasses."""
        return
