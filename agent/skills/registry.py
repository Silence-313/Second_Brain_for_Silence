"""Skill registry — central registration and management of skills."""

import time
from typing import Any

from agent.models.skills import SkillExecutionRecord, SkillResult
from agent.skills.protocol import Skill


class SkillRegistry:
    """Register and manage skills. Tracks execution logs."""

    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}
        self._log: list[SkillExecutionRecord] = []

    def register(self, skill: Skill) -> None:
        if not skill.name:
            raise ValueError("Skill must have a name")
        self._skills[skill.name] = skill

    def has(self, name: str) -> bool:
        return name in self._skills

    def get(self, name: str) -> Skill | None:
        return self._skills.get(name)

    def get_skill_names(self) -> list[str]:
        return list(self._skills.keys())

    def list_all(self) -> list[dict[str, Any]]:
        return [s.to_info() for s in self._skills.values()]

    async def execute(self, name: str, args: dict[str, Any]) -> SkillResult:
        skill = self._skills.get(name)
        if skill is None:
            return SkillResult(success=False, error=f"Skill not found: {name}")

        start = time.monotonic()
        try:
            result = await skill.execute(args)
            latency = (time.monotonic() - start) * 1000
            self._log.append(
                SkillExecutionRecord(
                    skill_name=name,
                    args=args,
                    result=result,
                    success=result.success,
                    latency_ms=round(latency, 2),
                )
            )
            return result
        except Exception as e:
            latency = (time.monotonic() - start) * 1000
            error_result = SkillResult(success=False, error=str(e))
            self._log.append(
                SkillExecutionRecord(
                    skill_name=name,
                    args=args,
                    result=error_result,
                    success=False,
                    latency_ms=round(latency, 2),
                )
            )
            return error_result

    def get_execution_log(self) -> list[SkillExecutionRecord]:
        return list(self._log)

    def clear_log(self) -> None:
        self._log.clear()
