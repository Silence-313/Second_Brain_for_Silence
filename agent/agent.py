"""Agent — public API, composition root, lifecycle management."""

import time
from typing import Any

from pydantic import BaseModel

from agent.config import AgentConfig
from agent.exceptions import ReentrancyError
from agent.observability.health import HealthCheck, HealthReport
from agent.observability.metrics import MetricsCollector
from agent.observability.tracer import ExecutionTracer
from agent.pipeline.context import PipelineContext
from agent.pipeline.pipeline import Pipeline


class AgentResponse(BaseModel, frozen=True):
    text: str
    session_id: str = ""
    duration_ms: float = 0.0


class Agent:
    """Public API for the Agent Framework. Wire everything together."""

    def __init__(self, config: AgentConfig | None = None) -> None:
        self._config = config or AgentConfig()

        # Infrastructure adapters (Stage 8)
        self._llm: Any = None
        self._storage: Any = None
        self._http: Any = None
        self._vector: Any = None
        self._event_bus: Any = None
        self._logger: Any = None

        # Domain services (Stages 2-5, 8-9)
        self._working_memory: Any = None
        self._episodic: Any = None
        self._profile: Any = None
        self._tool_memory: Any = None
        self._memory_store: Any = None
        self._memory_writer: Any = None
        self._concept_extractor: Any = None
        self._graph_builder: Any = None
        self._reasoner: Any = None
        self._feedback_processor: Any = None
        self._router: Any = None
        self._router_telemetry: Any = None
        self._rag_feedback: Any = None
        self._planner: Any = None
        self._drift_controller: Any = None
        self._memory_evolution: Any = None
        self._concept_evolver: Any = None
        self._mutation_queue: Any = None
        self._mutation_engine: Any = None

        # Knowledge Base (llm-wiki)
        self._knowledge_base: Any = None

        # Capability layer (Stages 6-7)
        self._tool_registry: Any = None
        self._skill_registry: Any = None
        self._search_manager: Any = None
        self._tool_decision: Any = None
        self._execution_engine: Any = None

        # Pipeline (Stage 10)
        self._pipeline: Pipeline | None = None

        # Observability (Stage 10)
        self._health: HealthCheck | None = None
        self._metrics: MetricsCollector | None = None
        self._tracer: ExecutionTracer | None = None

        # Guards
        self._initialized: bool = False
        self._processing: bool = False
        self._error_count: int = 0

    # -- Lifecycle --

    async def initialize(self) -> None:
        """Initialize all subsystems and build the pipeline."""
        from agent.bus.memory_bus import InMemoryEventBus
        from agent.concepts.extractor import ConceptExtractor
        from agent.core.engine import StateMutationEngine
        from agent.core.queue import MutationQueue
        from agent.evolution.concept_evolver import ConceptEvolver
        from agent.evolution.memory_evolution import MemoryEvolution
        from agent.execution.engine import ExecutionEngine
        from agent.infrastructure.llm.deepseek import DeepSeekLLMClient
        from agent.infrastructure.logging.structlog_adapter import StructlogLogger
        from agent.infrastructure.storage.local_fs import LocalFileStorage
        from agent.infrastructure.vector.tfidf_store import TfidfVectorStore
        from agent.memory.episodic import EpisodicMemory
        from agent.memory.profile import UserProfile
        from agent.memory.store import MemoryStore
        from agent.memory.tool_stats import ToolMemory
        from agent.memory.working import WorkingMemory
        from agent.memory.writer import MemoryWriter
        from agent.pipeline.stages.execute import ExecuteStage
        from agent.pipeline.stages.generate import GenerateStage
        from agent.pipeline.stages.health import HealthStage
        from agent.pipeline.stages.learn import LearnStage
        from agent.pipeline.stages.persist import PersistStage
        from agent.pipeline.stages.plan import PlanStage
        from agent.pipeline.stages.prompt import PromptStage
        from agent.pipeline.stages.reason import ReasonStage
        from agent.pipeline.stages.retrieve import RetrieveStage
        from agent.pipeline.stages.route import RouteStage
        from agent.pipeline.stages.sanitize import SanitizeStage
        from agent.pipeline.stages.sanitize_response import ResponseSanitizeStage
        from agent.planner.intent import IntentParser
        from agent.planner.planner import Planner
        from agent.policy.controller import DriftController
        from agent.reasoning.feedback import FeedbackProcessor
        from agent.reasoning.graph import ConceptGraphBuilder
        from agent.reasoning.reasoner import ConceptReasoner
        from agent.retrieval.feedback import RagFeedback
        from agent.routing.router import ToolRouter
        from agent.routing.telemetry import RouterTelemetry
        from agent.search.manager import SearchManager
        from agent.skills.builtins.file_reader import ReadFileSkill
        from agent.skills.builtins.location import GetLocationSkill
        from agent.skills.registry import SkillRegistry
        from agent.tools.builtins.time import GetCurrentTimeTool
        from agent.tools.builtins.todos import AddTodosTool, GetTodosTool, TodoStatsTool
        from agent.tools.builtins.web_search import WebSearchTool
        from agent.tools.builtins.wiki_crud import (
            DeleteWikiTool,
            ListWikiTool,
            ReadWikiTool,
            SearchWikiTool,
            WriteWikiTool,
        )
        from agent.tools.decision import ToolDecisionPolicy
        from agent.tools.registry import ToolRegistry

        # Infrastructure
        self._storage = LocalFileStorage()
        self._vector = TfidfVectorStore()
        self._event_bus = InMemoryEventBus()
        self._logger = StructlogLogger(level=self._config.log_level)
        self._llm = DeepSeekLLMClient(
            endpoint=self._config.llm_endpoint,
            api_key=self._config.llm_api_key,
            model=self._config.llm_model,
            timeout_ms=self._config.llm_timeout_ms,
        )

        # Memory (Stage 2)
        self._working_memory = WorkingMemory(self._config.memory_working_capacity)
        self._episodic = EpisodicMemory(self._config.memory_episodic_capacity)
        self._profile = UserProfile()
        self._seed_user_profile()
        self._tool_memory = ToolMemory()
        self._memory_store = MemoryStore(self._storage, self._config.memory_base_path)
        self._concept_extractor = ConceptExtractor()
        self._mutation_queue = MutationQueue()
        self._mutation_engine = StateMutationEngine(
            store=self._memory_store, episodic=self._episodic, profile=self._profile
        )
        self._memory_writer = MemoryWriter(
            episodic=self._episodic,
            profile=self._profile,
            tool_memory=self._tool_memory,
            store=self._memory_store,
            concept_extractor=self._concept_extractor,
            mutation_queue=self._mutation_queue,
        )

        # Knowledge Base (llm-wiki)
        if self._config.knowledge_base_enabled:
            from agent.knowledge.manager import KnowledgeBaseManager
            self._knowledge_base = KnowledgeBaseManager(self._storage, self._config.knowledge_base_path)
            await self._knowledge_base.initialize()

        # Reasoning (Stage 3)
        self._graph_builder = ConceptGraphBuilder()
        self._reasoner = ConceptReasoner()
        self._drift_controller = DriftController()
        self._feedback_processor = FeedbackProcessor(
            store=self._memory_store,
            drift_controller=self._drift_controller,
            mutation_queue=self._mutation_queue,
        )

        # Routing & Retrieval (Stage 4)
        self._router = ToolRouter()
        self._router_telemetry = RouterTelemetry()
        self._rag_feedback = RagFeedback()

        # Planner (Stage 5)
        self._planner = Planner(IntentParser())

        # Tools (Stage 6)
        self._tool_registry = ToolRegistry()
        self._tool_registry.register(GetCurrentTimeTool())
        self._tool_registry.register(GetTodosTool())
        self._tool_registry.register(AddTodosTool())
        self._tool_registry.register(TodoStatsTool())
        from agent.infrastructure.http.httpx_client import HttpxHttpClient
        _http = HttpxHttpClient()
        self._tool_registry.register(WebSearchTool(http_client=_http))
        self._tool_registry.register(ListWikiTool(storage=self._storage, base_path=self._config.memory_base_path))
        self._tool_registry.register(ReadWikiTool(storage=self._storage, base_path=self._config.memory_base_path))
        self._tool_registry.register(WriteWikiTool(storage=self._storage, base_path=self._config.memory_base_path))
        self._tool_registry.register(DeleteWikiTool(storage=self._storage, base_path=self._config.memory_base_path))
        self._tool_registry.register(SearchWikiTool(storage=self._storage, base_path=self._config.memory_base_path))

        # Knowledge Base Tools
        if self._knowledge_base is not None:
            from agent.knowledge.tools import (
                GetKBIndexTool, GetKBOverviewTool, ListKBConceptsTool, ListKBSummariesTool,
                MaintainKBTool, ReadKBFileTool, SearchKBTool, WriteKBConceptTool, WriteKBSummaryTool,
            )
            self._tool_registry.register(ListKBSummariesTool(kb_manager=self._knowledge_base))
            self._tool_registry.register(ListKBConceptsTool(kb_manager=self._knowledge_base))
            self._tool_registry.register(ReadKBFileTool(kb_manager=self._knowledge_base))
            self._tool_registry.register(SearchKBTool(kb_manager=self._knowledge_base))
            self._tool_registry.register(WriteKBSummaryTool(kb_manager=self._knowledge_base))
            self._tool_registry.register(WriteKBConceptTool(kb_manager=self._knowledge_base))
            self._tool_registry.register(GetKBIndexTool(kb_manager=self._knowledge_base))
            self._tool_registry.register(GetKBOverviewTool(kb_manager=self._knowledge_base))
            self._tool_registry.register(MaintainKBTool(kb_manager=self._knowledge_base, llm_client=self._llm))

        self._tool_decision = ToolDecisionPolicy(llm_client=self._llm)

        # Skills (Stage 6)
        self._skill_registry = SkillRegistry()
        self._skill_registry.register(GetLocationSkill())
        self._skill_registry.register(ReadFileSkill(storage=self._storage))

        # Search (Stage 6)
        from agent.search.providers.bing import BingSearchProvider
        from agent.search.providers.duckduckgo import DuckDuckGoSearchProvider
        from agent.search.providers.sogou import SogouSearchProvider
        self._search_manager = SearchManager()
        self._search_manager.register_provider(BingSearchProvider(http_client=_http))
        self._search_manager.register_provider(DuckDuckGoSearchProvider(http_client=_http))
        self._search_manager.register_provider(SogouSearchProvider(http_client=_http))

        # Execution (Stage 7)
        self._execution_engine = ExecutionEngine(
            tool_registry=self._tool_registry,
            skill_registry=self._skill_registry,
            search_manager=self._search_manager,
            event_bus=self._event_bus,
        )

        # Evolution (Stage 9)
        self._memory_evolution = MemoryEvolution(self._episodic)
        self._concept_evolver = ConceptEvolver(
            store=self._memory_store, mutation_queue=self._mutation_queue
        )

        # Pipeline (Stage 10)
        stages = [
            SanitizeStage(max_chars=self._config.safety_max_input_chars),
            RouteStage(router=self._router),
            RetrieveStage(
                vector_store=self._vector,
                episodic_memory=self._episodic,
                user_profile=self._profile,
            ),
            ReasonStage(
                graph_builder=self._graph_builder,
                reasoner=self._reasoner,
                store=self._memory_store,
            ),
            PlanStage(planner=self._planner, tool_registry=self._tool_registry, search_manager=self._search_manager),
            ExecuteStage(engine=self._execution_engine),
            PromptStage(max_chars=self._config.safety_max_prompt_chars, kb_manager=self._knowledge_base),
            GenerateStage(llm_client=self._llm),
            ResponseSanitizeStage(),
            PersistStage(memory_writer=self._memory_writer, profile=self._profile, kb_manager=self._knowledge_base),
            LearnStage(
                router_telemetry=self._router_telemetry,
                rag_feedback=self._rag_feedback,
                feedback_processor=self._feedback_processor,
                memory_evolution=self._memory_evolution,
                concept_evolver=self._concept_evolver,
                kb_manager=self._knowledge_base,
                llm_client=self._llm,
            ),
            HealthStage(
                drift_controller=self._drift_controller,
                store=self._memory_store,
                interval=self._config.evolution_health_interval,
            ),
        ]
        self._pipeline = Pipeline(stages)

        # Observability
        self._health = HealthCheck(
            version="0.1.0-dev", model=self._config.llm_model
        )
        self._metrics = MetricsCollector()
        self._tracer = ExecutionTracer()

        self._initialized = True

    async def shutdown(self) -> None:
        """Save all state and clean up."""
        if self._episodic:
            try:
                data = self._episodic.serialize()
                await self._storage.write(
                    f"{self._config.memory_base_path}/episodic.json", data
                )
            except Exception:
                pass

        if self._memory_store and self._profile:
            try:
                await self._memory_store.save_profile(self._profile.to_data())
            except Exception:
                pass

        self._initialized = False

    # -- Core API --

    async def process(
        self,
        user_input: str,
        session_id: str = "",
    ) -> AgentResponse:
        if not self._initialized:
            await self.initialize()

        if self._processing:
            raise ReentrancyError("Agent is already processing a request")

        self._processing = True
        t0 = time.monotonic()

        try:
            if not session_id:
                import uuid
                session_id = uuid.uuid4().hex[:12]

            context = PipelineContext(
                session_id=session_id,
                user_input_raw=user_input,
            )

            context = await self._pipeline.execute(context)  # type: ignore[union-attr]

            if self._metrics:
                self._metrics.incr("interactions_total")
                self._metrics.observe(
                    "pipeline_duration_ms",
                    (time.monotonic() - t0) * 1000,
                )

            if self._tracer:
                error_msgs = [e.error for e in context.errors] if context.errors else []
                await self._tracer.trace_interaction(
                    session_id=session_id,
                    user_input=user_input,
                    response=context.llm_response_clean or "",
                    stage_timings=dict(context.stage_timings),
                    errors=error_msgs,
                    duration_ms=(time.monotonic() - t0) * 1000,
                )

            return AgentResponse(
                text=context.llm_response_clean or "",
                session_id=session_id,
                duration_ms=round((time.monotonic() - t0) * 1000, 2),
            )
        except ReentrancyError:
            raise
        except Exception:
            self._error_count += 1
            return AgentResponse(
                text="Sorry, I encountered an error.",
                session_id=session_id,
                duration_ms=round((time.monotonic() - t0) * 1000, 2),
            )
        finally:
            self._processing = False

    # -- Health & State --

    async def health_check(self) -> HealthReport:
        if self._health is None:
            return HealthReport(status="error", errors=["agent not initialized"])

        episodic_count = self._episodic.count if self._episodic else 0
        concept_count = len(
            await self._memory_store.load_concepts()
        ) if self._memory_store else 0

        health_score = 1.0
        if self._drift_controller:
            try:
                concepts = (
                    await self._memory_store.load_concepts()
                    if self._memory_store
                    else []
                )
                confidences = [c.confidence for c in concepts]
                metrics = self._drift_controller.compute_health(
                    confidences, len(concepts)
                )
                health_score = metrics.health_score
            except Exception:
                pass

        return self._health.compute(
            episodic_count=episodic_count,
            concept_count=concept_count,
            health_score=health_score,
        )

    async def get_state(self) -> dict[str, Any]:
        return {
            "initialized": self._initialized,
            "error_count": self._error_count,
            "episodic_count": self._episodic.count if self._episodic else 0,
            "tool_count": self._tool_registry.count if self._tool_registry else 0,
            "skill_count": (
                len(self._skill_registry.get_skill_names())
                if self._skill_registry
                else 0
            ),
        }

    async def search_episodic(self, query: str, top_k: int = 5) -> list[Any]:
        if self._episodic is None:
            return []
        return self._episodic.search(query, top_k)  # type: ignore[no-any-return]

    async def search_wiki(self, query: str, top_k: int = 3) -> list[Any]:
        if self._vector is None:
            return []
        return await self._vector.search(query, top_k)  # type: ignore[no-any-return]

    async def rebuild_vector_index(self) -> None:
        if self._memory_store is None or self._vector is None:
            return
        try:
            episodes = await self._memory_store.load_episodes()
            docs = [
                {"path": e.id, "content": f"{e.summary} {e.detail}"}
                for e in episodes
            ]
            self._vector.build(docs)
        except Exception:
            pass

    async def save_state(self) -> None:
        if self._episodic:
            data = self._episodic.serialize()
            await self._storage.write(
                f"{self._config.memory_base_path}/episodic.json", data
            )

    # -- Plugin --

    def _seed_user_profile(self) -> None:
        """Seed Silence's identity into the user profile."""
        if self._profile is None:
            return
        self._profile.set("name", "Silence", 1.0)
        self._profile.set("preferred_name", "Silence", 1.0)
        self._profile.add_to_array("interests", "编程")
        self._profile.add_to_array("interests", "人工智能")
        self._profile.add_to_array("interests", "知识管理")
        self._profile.add_to_array("expertise", "Python")
        self._profile.add_to_array("expertise", "全栈开发")
        self._profile.add_to_array("expertise", "AI Agent")
        self._profile.add_to_array("common_tools", "VS Code")
        self._profile.add_to_array("common_tools", "Claude Code")
        self._profile.add_to_array("common_tools", "OpenClaw")
        self._profile.add_to_array("common_tools", "Obsidian")
        self._profile.add_to_array("current_focus", "构建个人第二大脑系统")
        self._profile.set("response_style", "concise", 1.0)

    def register_tool(self, tool: Any) -> None:
        if self._tool_registry:
            self._tool_registry.register(tool)

    def register_skill(self, skill: Any) -> None:
        if self._skill_registry:
            self._skill_registry.register(skill)

    def register_search_provider(self, provider: Any) -> None:
        if self._search_manager:
            self._search_manager.register_provider(provider)

    def register_pipeline_stage(self, stage: Any) -> None:
        if self._pipeline:
            self._pipeline.add_stage(stage)
