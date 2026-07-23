"""Execution engine — plan execution, fallback strategy, result verification."""

from agent.execution.engine import ExecutionEngine, ExecutionResult
from agent.execution.fallback import FallbackAction, FallbackStrategy
from agent.execution.verifier import ResultVerifier, VerificationResult

__all__ = [
    "ExecutionEngine",
    "ExecutionResult",
    "FallbackStrategy",
    "FallbackAction",
    "ResultVerifier",
    "VerificationResult",
]
