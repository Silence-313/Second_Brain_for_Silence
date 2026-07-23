"""Result verifier — validate tool/skill/search execution outputs."""

from typing import Any

from pydantic import BaseModel, Field


class VerificationResult(BaseModel, frozen=True):
    valid: bool = True
    issues: list[str] = Field(default_factory=list)
    quality: float = Field(default=1.0, ge=0, le=1)


class ResultVerifier:
    """Validate capability execution outputs for correctness."""

    def verify(self, result: Any, capability_type: str = "tool") -> VerificationResult:
        """Check result structure and data completeness."""
        issues: list[str] = []
        quality: float = 1.0

        if result is None:
            return VerificationResult(valid=False, issues=["result is None"], quality=0.0)

        if hasattr(result, "success") and not result.success:
            issues.append(f"result indicates failure: {getattr(result, 'error', 'unknown')}")
            quality = 0.2

        if hasattr(result, "data"):
            data = result.data
            if data is None:
                issues.append("result.data is None")
                quality = max(0.0, quality - 0.3)
        else:
            if capability_type != "search":
                issues.append("result missing 'data' field")
                quality = max(0.0, quality - 0.2)

        if hasattr(result, "error") and result.error and hasattr(result, "success") and result.success:
            issues.append("result has error message despite success=True")
            quality = max(0.0, quality - 0.1)

        if issues:
            quality = max(0.0, min(1.0, quality))

        return VerificationResult(
            valid=len(issues) == 0,
            issues=issues,
            quality=round(quality, 4),
        )
