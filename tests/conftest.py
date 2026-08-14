"""Shared test fixtures for the Agent Framework."""

import pytest


@pytest.fixture
def in_memory_storage():
    from agent.infrastructure.storage.memory_fs import InMemoryFileStorage

    return InMemoryFileStorage()


@pytest.fixture
def episodic_memory():
    from agent.memory.episodic import EpisodicMemory

    return EpisodicMemory(max_entries=200)


@pytest.fixture
def user_profile():
    from agent.memory.profile import UserProfile

    return UserProfile()


@pytest.fixture
def tool_memory():
    from agent.memory.tool_stats import ToolMemory

    return ToolMemory()


@pytest.fixture
def mock_llm():
    from agent.infrastructure.llm.mock import MockLLMClient

    return MockLLMClient(responses=["This is a test response."])


@pytest.fixture
def event_bus():
    from agent.bus.memory_bus import InMemoryEventBus

    return InMemoryEventBus()
