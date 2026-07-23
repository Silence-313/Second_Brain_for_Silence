"""Agent configuration loaded from environment variables and defaults."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentConfig(BaseSettings):
    """All agent configuration. Loaded from env vars / config file / defaults."""

    # LLM
    llm_endpoint: str = "https://api.deepseek.com/v1"
    llm_model: str = "deepseek-chat"
    llm_api_key: str = ""
    llm_timeout_ms: int = 60_000
    llm_max_tokens: int = 4096
    llm_temperature: float = 0.7

    # Memory
    memory_working_capacity: int = 20
    memory_episodic_capacity: int = 200
    memory_base_path: str = "./agent-memory"

    # Knowledge Base (llm-wiki)
    knowledge_base_enabled: bool = True
    knowledge_base_path: str = "./knowledge-base"

    # Evolution
    evolution_cycle_interval: int = 10
    evolution_concept_interval: int = 20
    evolution_health_interval: int = 15

    # Safety
    safety_max_update_per_cycle: float = 0.05
    safety_min_confirmations: int = 3
    safety_low_confidence_threshold: float = 0.3
    safety_max_input_chars: int = 4000
    safety_max_prompt_chars: int = 8000

    # Decay
    decay_base_rate: float = 0.03
    decay_usage_damping: float = 0.6
    decay_removal_threshold: float = 0.25
    decay_removal_cycles: int = 14

    # Concept Evolution
    concept_merge_similarity: float = 0.7
    concept_decay_days: int = 7
    concept_decay_rate: float = 0.05
    concept_decay_floor: float = 0.15

    # Search
    search_default_providers: list[str] = ["bing", "duckduckgo"]
    search_max_results: int = 10
    search_timeout_ms: int = 15_000

    # Pipeline
    pipeline_stages: list[str] = [
        "sanitize",
        "route",
        "retrieve",
        "reason",
        "plan",
        "execute",
        "prompt",
        "generate",
        "sanitize_response",
        "persist",
        "learn",
        "health",
    ]

    # Observability
    log_level: str = "INFO"
    metrics_enabled: bool = True
    tracer_enabled: bool = True

    model_config = SettingsConfigDict(env_prefix="AGENT_", env_file=".env")
