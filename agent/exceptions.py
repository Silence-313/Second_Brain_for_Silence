"""Agent exception hierarchy."""


class AgentException(Exception):
    """Base exception for all agent errors."""


class ConfigurationError(AgentException):
    """Invalid configuration."""


class PipelineError(AgentException):
    """Pipeline execution error."""


class StageExecutionError(PipelineError):
    """A pipeline stage failed."""


class StageTimeoutError(PipelineError):
    """A pipeline stage timed out."""


class LLMError(AgentException):
    """LLM API error."""


class LLMTimeoutError(LLMError):
    """LLM API call timed out."""


class LLMAuthenticationError(LLMError):
    """LLM API authentication failed."""


class LLMRateLimitError(LLMError):
    """LLM API rate limit exceeded."""


class ToolError(AgentException):
    """Tool execution error."""


class ToolNotFoundError(ToolError):
    """Requested tool not found in registry."""


class ToolExecutionError(ToolError):
    """Tool execution failed."""


class ToolTimeoutError(ToolError):
    """Tool execution timed out."""


class SkillError(AgentException):
    """Skill execution error."""


class SkillNotFoundError(SkillError):
    """Requested skill not found in registry."""


class SkillPermissionError(SkillError):
    """Skill requires elevated permissions."""


class SkillExecutionError(SkillError):
    """Skill execution failed."""


class SearchError(AgentException):
    """Search execution error."""


class ProviderNotFoundError(SearchError):
    """Search provider not found."""


class ProviderTimeoutError(SearchError):
    """Search provider timed out."""


class AllProvidersFailedError(SearchError):
    """All search providers failed."""


class MemoryError(AgentException):
    """Memory operation error."""


class MemoryLoadError(MemoryError):
    """Failed to load memory from storage."""


class MemorySaveError(MemoryError):
    """Failed to save memory to storage."""


class ValidationError(AgentException):
    """Data validation error."""


class ReentrancyError(AgentException):
    """Concurrent process() call rejected."""
