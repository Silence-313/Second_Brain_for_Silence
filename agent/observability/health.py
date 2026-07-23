"""Health check service — agent health status."""

from typing import Literal

from pydantic import BaseModel, Field


class HealthReport(BaseModel, frozen=True):
    status: Literal["healthy", "degraded", "error"] = "healthy"
    version: str = ""
    model: str = ""
    memory_episodic_count: int = 0
    memory_concept_count: int = 0
    cognitive_health_score: float = 1.0
    errors: list[str] = Field(default_factory=list)


class HealthCheck:
    """Compute agent health from component states."""

    def __init__(
        self,
        version: str = "0.1.0-dev",
        model: str = "",
    ) -> None:
        self._version = version
        self._model = model

    def compute(
        self,
        episodic_count: int = 0,
        concept_count: int = 0,
        health_score: float = 1.0,
        errors: list[str] | None = None,
    ) -> HealthReport:
        status: Literal["healthy", "degraded", "error"] = "healthy"
        if health_score < 0.3:
            status = "error"
        elif health_score < 0.6:
            status = "degraded"

        return HealthReport(
            status=status,
            version=self._version,
            model=self._model,
            memory_episodic_count=episodic_count,
            memory_concept_count=concept_count,
            cognitive_health_score=round(health_score, 4),
            errors=errors or [],
        )
