"""Memory store — YAML frontmatter persistence via FileStorage port."""

import json
import re
from datetime import UTC, datetime
from typing import Any

import yaml

from agent.models.concepts import Concept
from agent.models.memory import Episode, UserProfileData
from agent.models.policy import CognitivePolicy
from agent.models.reasoning import ReasoningTrace
from agent.ports.storage import FileStorage

_YAML_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)", re.DOTALL)


def _parse_yaml_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    m = _YAML_RE.match(text)
    if not m:
        return {}, text
    fm = yaml.safe_load(m.group(1)) or {}
    if not isinstance(fm, dict):
        return {}, m.group(2).strip()
    return fm, m.group(2).strip()


def _encode_yaml_frontmatter(fields: dict[str, Any], body: str) -> str:
    frontmatter = yaml.safe_dump(
        fields, allow_unicode=True, sort_keys=False, default_flow_style=False
    ).strip()
    return f"---\n{frontmatter}\n---\n\n{body}\n"


def _get_str(d: dict[str, Any], key: str, default: str = "") -> str:
    v = d.get(key, default)
    return str(v) if v is not None else default


def _get_float(d: dict[str, Any], key: str, default: float = 0.5) -> float:
    try:
        return float(d[key])
    except (KeyError, TypeError, ValueError):
        return default


def _get_int(d: dict[str, Any], key: str, default: int = 0) -> int:
    try:
        return int(d[key])
    except (KeyError, TypeError, ValueError):
        return default


def _get_bool(d: dict[str, Any], key: str, default: bool = False) -> bool:
    v = d.get(key)
    if v is None:
        return default
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.lower() in ("true", "yes", "1")
    return bool(v)


def _get_str_list(d: dict[str, Any], key: str) -> list[str]:
    v = d.get(key, [])
    if isinstance(v, list):
        return [str(item).strip() for item in v if str(item).strip()]
    if isinstance(v, str):
        return [t.strip() for t in v.split(",") if t.strip()]
    return []


def _get_datetime(d: dict[str, Any], key: str) -> datetime:
    v = d.get(key)
    if v is None:
        return datetime.now(UTC)
    if isinstance(v, datetime):
        return v
    try:
        return datetime.fromisoformat(str(v))
    except (ValueError, TypeError):
        return datetime.now(UTC)


def _episode_to_frontmatter(e: Episode) -> dict[str, Any]:
    return {
        "id": e.id,
        "timestamp": e.timestamp.isoformat(),
        "type": e.type,
        "summary": e.summary,
        "detail": e.detail,
        "importance": e.importance,
        "tags": e.tags,
        "related_files": e.related_files,
        "importance_score": e.importance_score,
        "usage_frequency": e.usage_frequency,
        "last_access_time": e.last_access_time.isoformat(),
        "decay_score": e.decay_score,
        "usefulness_score": e.usefulness_score,
        "marked_for_removal": e.marked_for_removal,
    }


def _frontmatter_to_episode(fm: dict[str, Any]) -> Episode:
    return Episode(
        id=_get_str(fm, "id"),
        timestamp=_get_datetime(fm, "timestamp"),
        type=_get_str(fm, "type", "event"),  # type: ignore[arg-type]
        summary=_get_str(fm, "summary"),
        detail=_get_str(fm, "detail"),
        importance=_get_float(fm, "importance", 0.5),
        tags=_get_str_list(fm, "tags"),
        related_files=_get_str_list(fm, "related_files"),
        importance_score=_get_float(fm, "importance_score", 0.5),
        usage_frequency=_get_int(fm, "usage_frequency", 0),
        last_access_time=_get_datetime(fm, "last_access_time"),
        decay_score=_get_float(fm, "decay_score", 1.0),
        usefulness_score=_get_float(fm, "usefulness_score", 0.5),
        marked_for_removal=_get_bool(fm, "marked_for_removal", False),
    )


class MemoryStore:
    """Human-readable vault-native persistence layer via FileStorage port."""

    def __init__(self, storage: FileStorage, base_path: str) -> None:
        self._storage = storage
        self._base_path = base_path

    async def _ensure_dirs(self) -> None:
        for sub in ["episodes", "concepts", "reasoning", "policy"]:
            await self._storage.mkdir(f"{self._base_path}/{sub}")

    # -- Episodes --

    async def load_episodes(self) -> list[Episode]:
        episodes: list[Episode] = []
        try:
            files = await self._storage.list_dir(f"{self._base_path}/episodes")
        except Exception:
            return episodes

        for fname in files:
            if not fname.endswith(".md"):
                continue
            try:
                text = await self._storage.read(f"{self._base_path}/episodes/{fname}")
                fm, body = _parse_yaml_frontmatter(text)
                if fm:
                    if "detail" not in fm:
                        fm["detail"] = body
                    episodes.append(_frontmatter_to_episode(fm))
            except Exception:
                continue
        return episodes

    async def write_episode(self, episode: Episode) -> None:
        await self._ensure_dirs()
        fm = _episode_to_frontmatter(episode)
        body = fm.pop("detail", episode.detail)
        content = _encode_yaml_frontmatter(fm, body)
        await self._storage.write(
            f"{self._base_path}/episodes/{episode.id}.md", content
        )

    async def sync_episodes(self, episodes: list[Episode]) -> None:
        for ep in episodes:
            await self.write_episode(ep)

    # -- Concepts --

    async def load_concepts(self) -> list[Concept]:
        concepts: list[Concept] = []
        try:
            files = await self._storage.list_dir(f"{self._base_path}/concepts")
        except Exception:
            return concepts

        for fname in files:
            if not fname.endswith(".md"):
                continue
            try:
                text = await self._storage.read(f"{self._base_path}/concepts/{fname}")
                fm, _ = _parse_yaml_frontmatter(text)
                if fm:
                    concepts.append(
                        Concept(
                            id=_get_str(fm, "id", fname.replace(".md", "")),
                            name=_get_str(fm, "name", fname.replace(".md", "")),
                            slug=_get_str(fm, "slug", fname.replace(".md", "")),
                            confidence=_get_float(fm, "confidence", 0.5),
                            source_episodes=_get_str_list(fm, "source_episodes"),
                            related=_get_str_list(fm, "related"),
                            tags=_get_str_list(fm, "tags"),
                        )
                    )
            except Exception:
                continue
        return concepts

    async def upsert_concept(self, concept: Concept) -> None:
        await self._ensure_dirs()
        fm: dict[str, Any] = {
            "id": concept.id,
            "name": concept.name,
            "slug": concept.slug,
            "confidence": concept.confidence,
            "source_episodes": concept.source_episodes,
            "related": concept.related,
            "tags": concept.tags,
            "created_at": concept.created_at.isoformat(),
            "updated_at": concept.updated_at.isoformat(),
        }
        content = _encode_yaml_frontmatter(fm, f"# {concept.name}\n\n{concept.slug}")
        await self._storage.write(
            f"{self._base_path}/concepts/{concept.slug}.md", content
        )

    async def update_concept_weight(self, slug: str, delta: float) -> None:
        try:
            text = await self._storage.read(f"{self._base_path}/concepts/{slug}.md")
            fm, body = _parse_yaml_frontmatter(text)
            if not fm:
                return
            old_conf = _get_float(fm, "confidence", 0.5)
            fm["confidence"] = max(0.15, min(1.0, old_conf + delta))
            content = _encode_yaml_frontmatter(fm, body)
            await self._storage.write(f"{self._base_path}/concepts/{slug}.md", content)
        except Exception:
            pass

    async def mark_concept_relationship(
        self, slug_a: str, slug_b: str, weight: float
    ) -> None:
        for slug in [slug_a, slug_b]:
            try:
                text = await self._storage.read(
                    f"{self._base_path}/concepts/{slug}.md"
                )
                fm, body = _parse_yaml_frontmatter(text)
                if not fm:
                    continue
                related = _get_str_list(fm, "related")
                other = slug_b if slug == slug_a else slug_a
                if other not in related:
                    related.append(other)
                fm["related"] = related
                content = _encode_yaml_frontmatter(fm, body)
                await self._storage.write(
                    f"{self._base_path}/concepts/{slug}.md", content
                )
            except Exception:
                continue

    # -- Profile --

    async def load_profile(self) -> UserProfileData | None:
        try:
            text = await self._storage.read(f"{self._base_path}/profile.md")
            fm, _ = _parse_yaml_frontmatter(text)
            if not fm:
                return None
            response_style = _get_str(fm, "response_style", "concise")
            return UserProfileData(
                name=_get_str(fm, "name"),
                preferred_name=_get_str(fm, "preferred_name"),
                role=_get_str(fm, "role"),
                timezone=_get_str(fm, "timezone"),
                language=_get_str(fm, "language"),
                interests=_get_str_list(fm, "interests"),
                expertise=_get_str_list(fm, "expertise"),
                active_projects=_get_str_list(fm, "active_projects"),
                common_tools=_get_str_list(fm, "common_tools"),
                response_style=response_style,  # type: ignore[arg-type]
            )
        except Exception:
            return None

    async def save_profile(self, profile: UserProfileData) -> None:
        await self._ensure_dirs()
        fm: dict[str, Any] = {
            "name": profile.name,
            "preferred_name": profile.preferred_name,
            "role": profile.role,
            "timezone": profile.timezone,
            "language": profile.language,
            "interests": profile.interests,
            "expertise": profile.expertise,
            "active_projects": profile.active_projects,
            "common_tools": profile.common_tools,
            "response_style": profile.response_style,
            "last_updated": profile.last_updated.isoformat(),
        }
        content = _encode_yaml_frontmatter(fm, "# 用户画像")
        await self._storage.write(f"{self._base_path}/profile.md", content)

    # -- Policy --

    async def load_policy(self) -> CognitivePolicy | None:
        try:
            text = await self._storage.read(
                f"{self._base_path}/policy/cognitive_policy.json"
            )
            return CognitivePolicy.model_validate_json(text)
        except Exception:
            return None

    async def save_policy(self, policy: CognitivePolicy) -> None:
        await self._ensure_dirs()
        await self._storage.write(
            f"{self._base_path}/policy/cognitive_policy.json",
            policy.model_dump_json(indent=2),
        )

    # -- Tool Decisions --

    async def save_tool_decision(self, record: dict[str, object]) -> None:
        await self._ensure_dirs()
        try:
            text = await self._storage.read(
                f"{self._base_path}/policy/tool_decisions.jsonl"
            )
        except Exception:
            text = ""
        text += json.dumps(record, ensure_ascii=False, default=str) + "\n"
        await self._storage.write(
            f"{self._base_path}/policy/tool_decisions.jsonl", text
        )

    # -- Reasoning Traces --

    async def save_reasoning_trace(self, trace: ReasoningTrace) -> None:
        await self._ensure_dirs()
        fm: dict[str, Any] = {
            "id": trace.id,
            "query": trace.query,
            "confidence": trace.confidence,
            "strategies_used": trace.strategies_used,
            "timestamp": trace.timestamp.isoformat(),
        }
        body = "## Key Concepts\n\n" + "\n".join(
            f"- {c}" for c in trace.key_concepts
        )
        body += "\n\n## Insights\n\n" + "\n".join(f"- {i}" for i in trace.insights)
        content = _encode_yaml_frontmatter(fm, body)
        await self._storage.write(
            f"{self._base_path}/reasoning/{trace.id}.md", content
        )
