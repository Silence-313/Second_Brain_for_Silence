"""Tests for AgentConfig."""

import os

import pytest

from agent.config import AgentConfig


class TestAgentConfig:
    def test_defaults(self) -> None:
        c = AgentConfig()
        assert c.llm_model in ("deepseek-chat", "deepseek-v4-flash")
        assert c.memory_working_capacity == 20
        assert c.evolution_cycle_interval == 10
        assert c.concept_merge_similarity == 0.7

    def test_env_prefix(self) -> None:
        os.environ["AGENT_LLM_MODEL"] = "test-model"
        os.environ["AGENT_MEMORY_WORKING_CAPACITY"] = "50"
        try:
            c = AgentConfig()
            assert c.llm_model == "test-model"
            assert c.memory_working_capacity == 50
        finally:
            del os.environ["AGENT_LLM_MODEL"]
            del os.environ["AGENT_MEMORY_WORKING_CAPACITY"]

    def test_pipeline_stages_list(self) -> None:
        c = AgentConfig()
        assert "sanitize" in c.pipeline_stages
        assert "generate" in c.pipeline_stages


class TestExceptions:
    def test_hierarchy(self) -> None:
        from agent.exceptions import (
            AgentException,
            LLMError,
            LLMTimeoutError,
            ReentrancyError,
            ToolError,
            ToolNotFoundError,
        )

        assert issubclass(LLMTimeoutError, LLMError)
        assert issubclass(LLMError, AgentException)
        assert issubclass(ToolNotFoundError, ToolError)
        assert issubclass(ReentrancyError, AgentException)

    def test_raise_catch(self) -> None:
        from agent.exceptions import LLMTimeoutError

        with pytest.raises(LLMTimeoutError):
            raise LLMTimeoutError("timeout")

    def test_str_message(self) -> None:
        from agent.exceptions import ConfigurationError

        e = ConfigurationError("bad config")
        assert "bad config" in str(e)
