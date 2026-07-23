"""Tests for SkillRegistry."""

import pytest

from agent.models.skills import SkillResult
from agent.skills.builtins.file_reader import ReadFileSkill
from agent.skills.builtins.location import GetLocationSkill
from agent.skills.protocol import Skill
from agent.skills.registry import SkillRegistry


class _MockSkill(Skill):
    name = "mock_skill"
    description = "A mock skill for testing"
    permissions = "safe"

    async def execute(self, args: dict) -> SkillResult:
        return SkillResult(success=True, data="mock result")


class TestSkillRegistry:
    def test_register(self) -> None:
        reg = SkillRegistry()
        reg.register(GetLocationSkill())
        assert reg.has("get_current_location")

    def test_get(self) -> None:
        reg = SkillRegistry()
        reg.register(GetLocationSkill())
        assert reg.get("get_current_location") is not None

    def test_get_nonexistent(self) -> None:
        reg = SkillRegistry()
        assert reg.get("nonexistent") is None

    @pytest.mark.asyncio
    async def test_execute(self) -> None:
        reg = SkillRegistry()
        reg.register(_MockSkill())
        result = await reg.execute("mock_skill", {})
        assert result.success

    @pytest.mark.asyncio
    async def test_execute_nonexistent(self) -> None:
        reg = SkillRegistry()
        result = await reg.execute("nonexistent", {})
        assert not result.success

    def test_get_skill_names(self) -> None:
        reg = SkillRegistry()
        reg.register(GetLocationSkill())
        reg.register(ReadFileSkill())
        names = reg.get_skill_names()
        assert "get_current_location" in names
        assert "read_local_file" in names

    def test_list_all(self) -> None:
        reg = SkillRegistry()
        reg.register(GetLocationSkill())
        skills = reg.list_all()
        assert len(skills) == 1

    @pytest.mark.asyncio
    async def test_execution_log(self) -> None:
        reg = SkillRegistry()
        reg.register(_MockSkill())
        await reg.execute("mock_skill", {})
        log = reg.get_execution_log()
        assert len(log) == 1

    def test_clear_log(self) -> None:
        reg = SkillRegistry()
        reg.register(_MockSkill())
        reg.clear_log()
        assert len(reg.get_execution_log()) == 0
