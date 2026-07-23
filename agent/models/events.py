"""Pipeline event discriminated union — all event types emitted during processing."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class PipelineEventBase(BaseModel, frozen=True):
    timestamp: datetime = Field(default_factory=datetime.now)


# Pipeline lifecycle events
class InputSanitized(PipelineEventBase, frozen=True):
    type: Literal["input_sanitized"] = "input_sanitized"
    original_length: int = 0
    sanitized_length: int = 0


class IntentClassified(PipelineEventBase, frozen=True):
    type: Literal["intent_classified"] = "intent_classified"
    tool: str = ""
    confidence: float = 0.0


class MemoryRetrieved(PipelineEventBase, frozen=True):
    type: Literal["memory_retrieved"] = "memory_retrieved"
    wiki_results: int = 0
    episodic_entries: int = 0


class ConceptsReasoned(PipelineEventBase, frozen=True):
    type: Literal["concepts_reasoned"] = "concepts_reasoned"
    concept_count: int = 0
    insight_count: int = 0


class PlanGenerated(PipelineEventBase, frozen=True):
    type: Literal["plan_generated"] = "plan_generated"
    step_count: int = 0
    strategy: str = ""


class ToolExecuted(PipelineEventBase, frozen=True):
    type: Literal["tool_executed"] = "tool_executed"
    tool_name: str = ""
    success: bool = False
    latency_ms: float = 0.0


class SkillExecuted(PipelineEventBase, frozen=True):
    type: Literal["skill_executed"] = "skill_executed"
    skill_name: str = ""
    success: bool = False
    latency_ms: float = 0.0


class SearchExecuted(PipelineEventBase, frozen=True):
    type: Literal["search_executed"] = "search_executed"
    provider: str = ""
    result_count: int = 0
    latency_ms: float = 0.0


class PromptBuilt(PipelineEventBase, frozen=True):
    type: Literal["prompt_built"] = "prompt_built"
    prompt_length: int = 0
    sections: list[str] = Field(default_factory=list)


class LLMCallStarted(PipelineEventBase, frozen=True):
    type: Literal["llm_call_started"] = "llm_call_started"
    model: str = ""
    message_count: int = 0


class LLMChunkReceived(PipelineEventBase, frozen=True):
    type: Literal["llm_chunk_received"] = "llm_chunk_received"
    chunk_length: int = 0


class LLMCallCompleted(PipelineEventBase, frozen=True):
    type: Literal["llm_call_completed"] = "llm_call_completed"
    total_tokens: int = 0
    duration_ms: float = 0.0


class ResponseSanitized(PipelineEventBase, frozen=True):
    type: Literal["response_sanitized"] = "response_sanitized"
    stripped_blocks: int = 0


class MemoryWritten(PipelineEventBase, frozen=True):
    type: Literal["memory_written"] = "memory_written"
    decisions_count: int = 0
    episodes_written: int = 0


class ConceptsExtracted(PipelineEventBase, frozen=True):
    type: Literal["concepts_extracted"] = "concepts_extracted"
    concepts_found: int = 0


class StateSaved(PipelineEventBase, frozen=True):
    type: Literal["state_saved"] = "state_saved"
    files_written: int = 0


class RouterLearned(PipelineEventBase, frozen=True):
    type: Literal["router_learned"] = "router_learned"
    tool: str = ""
    threshold_delta: float = 0.0


class RAGUpdated(PipelineEventBase, frozen=True):
    type: Literal["rag_updated"] = "rag_updated"
    doc_count: int = 0


class EvolutionCycleCompleted(PipelineEventBase, frozen=True):
    type: Literal["evolution_cycle_completed"] = "evolution_cycle_completed"
    decayed: int = 0
    merged: int = 0


class HealthCheckCompleted(PipelineEventBase, frozen=True):
    type: Literal["health_check_completed"] = "health_check_completed"
    health_score: float = 0.0
    status: str = ""


# System events
class AgentInitialized(PipelineEventBase, frozen=True):
    type: Literal["agent_initialized"] = "agent_initialized"
    version: str = ""
    model: str = ""


class AgentShutdown(PipelineEventBase, frozen=True):
    type: Literal["agent_shutdown"] = "agent_shutdown"


class ErrorOccurred(PipelineEventBase, frozen=True):
    type: Literal["error_occurred"] = "error_occurred"
    stage: str = ""
    error: str = ""


class ReentrancyBlocked(PipelineEventBase, frozen=True):
    type: Literal["reentrancy_blocked"] = "reentrancy_blocked"
    session_id: str = ""


PipelineEvent = Annotated[
    InputSanitized
    | IntentClassified
    | MemoryRetrieved
    | ConceptsReasoned
    | PlanGenerated
    | ToolExecuted
    | SkillExecuted
    | SearchExecuted
    | PromptBuilt
    | LLMCallStarted
    | LLMChunkReceived
    | LLMCallCompleted
    | ResponseSanitized
    | MemoryWritten
    | ConceptsExtracted
    | StateSaved
    | RouterLearned
    | RAGUpdated
    | EvolutionCycleCompleted
    | HealthCheckCompleted
    | AgentInitialized
    | AgentShutdown
    | ErrorOccurred
    | ReentrancyBlocked,
    Field(discriminator="type"),
]
