"""Tests for FallbackStrategy."""

import pytest

from agent.execution.fallback import FallbackAction, FallbackStrategy


class TestFallbackStrategy:
    @pytest.mark.asyncio
    async def test_retry_on_first_attempt(self) -> None:
        fs = FallbackStrategy(max_retries=2)
        action = await fs.on_failure("step-1", Exception("fail"), 1, [])
        assert action == FallbackAction.RETRY

    @pytest.mark.asyncio
    async def test_switch_on_second_attempt_with_alternatives(self) -> None:
        fs = FallbackStrategy(max_retries=1)
        action = await fs.on_failure("step-1", Exception("fail"), 2, ["alt_provider"])
        assert action == FallbackAction.SWITCH_PROVIDER

    @pytest.mark.asyncio
    async def test_skip_when_no_alternatives(self) -> None:
        fs = FallbackStrategy(max_retries=1)
        action = await fs.on_failure("step-1", Exception("fail"), 2, [])
        assert action == FallbackAction.SKIP

    @pytest.mark.asyncio
    async def test_abort_on_fail_fast(self) -> None:
        fs = FallbackStrategy(max_retries=1, degrade_policy="fail_fast")
        action = await fs.on_failure("step-1", Exception("fail"), 2, [])
        assert action == FallbackAction.ABORT

    @pytest.mark.asyncio
    async def test_partial_results(self) -> None:
        fs = FallbackStrategy(max_retries=1, degrade_policy="partial_results")
        action = await fs.on_failure("step-1", Exception("fail"), 2, [])
        assert action == FallbackAction.PARTIAL
