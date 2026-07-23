"""Built-in skill: get current location via Geolocation API."""

from typing import Any

from agent.models.skills import SkillResult
from agent.skills.protocol import Skill


class GetLocationSkill(Skill):
    name = "get_current_location"
    description = "获取当前设备的物理位置"
    permissions = "privileged"

    def __init__(self) -> None:
        self._cached: dict[str, Any] | None = None
        self._cache_time: float = 0.0
        self._cache_ttl: float = 300.0  # 5 minutes

    async def execute(self, args: dict[str, Any]) -> SkillResult:
        import time

        now = time.monotonic()
        if self._cached and (now - self._cache_time) < self._cache_ttl:
            return SkillResult(success=True, data={"location": self._cached, "cached": True})

        return SkillResult(
            success=False,
            error="Geolocation requires browser environment. Inject location data via args.",
        )
