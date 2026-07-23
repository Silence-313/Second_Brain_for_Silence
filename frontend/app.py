"""Agent Flask Frontend — REST API + Web Chat UI with Agent internals."""

import asyncio
import json
import os
import queue
import sys
import threading
import time
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, Response, jsonify, render_template, request, stream_with_context
from flask_cors import CORS

from agent.agent import Agent, AgentConfig
from agent.pipeline.context import PipelineContext

app = Flask(__name__)
CORS(app)

_agent: Agent | None = None


@app.before_request
def ensure_agent():
    global _agent
    if _agent is None or not _agent._initialized:
        config = AgentConfig()
        _agent = Agent(config)
        asyncio.run(_agent.initialize())


def _run_full_pipeline(message: str, session_id: str, history: list[dict] | None = None) -> dict:
    global _agent
    ctx = PipelineContext(session_id=session_id, user_input_raw=message, chat_history=history or [])
    result = asyncio.run(_agent._pipeline.execute(ctx))

    internal: dict = {
        "stage_timings": dict(result.stage_timings),
        "errors": [e.error for e in result.errors] if result.errors else [],
    }

    if result.router_result and hasattr(result.router_result, "tool"):
        internal["router"] = {
            "tool": result.router_result.tool,
            "confidence": getattr(result.router_result, "confidence", 0),
            "reason": getattr(result.router_result, "reason", ""),
        }

    mc = result.memory_context or {}
    wiki = mc.get("wiki_results", [])
    episodic = mc.get("episodic_context", "")
    profile = mc.get("profile_context", "")
    internal["memory"] = {
        "wiki_count": len(wiki),
        "has_episodic": bool(episodic),
        "has_profile": bool(profile),
    }

    # KB prompt injection tracking
    kb = _agent._knowledge_base
    if kb is not None:
        concepts = asyncio.run(kb.list_concepts())
        internal["kb"] = {
            "prompt_injected": len(concepts) > 0,
            "concept_count": len(concepts),
        }

    reasoning = mc.get("reasoning_context")
    if reasoning and hasattr(reasoning, "key_concepts"):
        internal["reasoning"] = {
            "key_concepts": reasoning.key_concepts[:8],
            "insights": getattr(reasoning, "inferred_insights", [])[:3],
            "confidence": getattr(reasoning, "confidence", 0),
        }

    if result.execution_result and hasattr(result.execution_result, "results"):
        exec_info = {}
        for sid, r in result.execution_result.results.items():
            exec_info[sid] = {
                "success": getattr(r, "success", False),
                "data_preview": str(getattr(r, "data", ""))[:100],
            }
        internal["execution"] = exec_info

    return {
        "text": result.llm_response_clean or "",
        "session_id": session_id,
        "duration_ms": sum(result.stage_timings.values()) if result.stage_timings else 0,
        "internal": internal,
    }


# ── REST API ──

@app.post("/api/chat")
def api_chat():
    message = request.json.get("message", "")  # type: ignore[union-attr]
    session_id = request.json.get("session_id", uuid.uuid4().hex[:12])  # type: ignore[union-attr]
    history = request.json.get("history", [])  # type: ignore[union-attr]
    if not message.strip():
        return jsonify({"error": "message is required"}), 400
    return jsonify(_run_full_pipeline(message, session_id, history))


@app.post("/api/chat/stream")
def api_chat_stream():
    message = request.json.get("message", "")  # type: ignore[union-attr]
    session_id = request.json.get("session_id", uuid.uuid4().hex[:12])  # type: ignore[union-attr]
    history = request.json.get("history", [])  # type: ignore[union-attr]
    if not message.strip():
        return jsonify({"error": "message is required"}), 400

    q: queue.Queue[tuple] = queue.Queue()

    def generate():
        t0 = time.monotonic()

        async def run():
            ctx = PipelineContext(session_id=session_id, user_input_raw=message, chat_history=history or [])

            # Run pre-generate stages (priority < 8)
            for stage in _agent._pipeline._stages:
                if stage.priority >= 8:
                    break
                t_stage = time.monotonic()
                try:
                    ctx = await stage.execute(ctx)
                except Exception:
                    pass
                ctx = ctx.with_timing(stage.name, (time.monotonic() - t_stage) * 1000)

            system_prompt = ctx.system_prompt or ""
            messages: list[dict] = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            for h in (history or [])[-20:]:
                role = h.get("role", "user")
                content = h.get("text") or h.get("content", "")
                if content.strip():
                    api_role = "assistant" if role == "agent" else "user"
                    messages.append({"role": api_role, "content": content})

            messages.append({"role": "user", "content": message})

            async def on_chunk(token: str):
                q.put(("token", token))

            full_text = ""
            try:
                full_text = await _agent._llm.stream(messages, on_chunk=on_chunk, temperature=0.7)
            except Exception as e:
                q.put(("error", str(e)))
                return

            q.put(("done", full_text, ctx, t0))

        def run_in_loop():
            loop = asyncio.new_event_loop()
            loop.run_until_complete(run())
            loop.close()

        thread = threading.Thread(target=run_in_loop)
        thread.start()

        while True:
            item = q.get()
            kind = item[0]
            if kind == "token":
                yield f"data: {json.dumps({'token': item[1]}, ensure_ascii=False)}\n\n"
            elif kind == "error":
                yield f"data: {json.dumps({'error': item[1]}, ensure_ascii=False)}\n\n"
                break
            elif kind == "done":
                full_text, ctx, t0 = item[1], item[2], item[3]
                duration = (time.monotonic() - t0) * 1000

                # Run post-generate stages
                ctx = ctx.with_updates(llm_response=full_text, llm_response_clean=full_text)
                for stage in _agent._pipeline._stages:
                    if stage.priority < 8:
                        continue
                    t_stage = time.monotonic()
                    try:
                        ctx = asyncio.run(stage.execute(ctx))
                    except Exception:
                        pass
                    ctx = ctx.with_timing(stage.name, (time.monotonic() - t_stage) * 1000)

                # Build internal state
                internal: dict = {"stage_timings": dict(ctx.stage_timings), "errors": []}
                if hasattr(ctx, 'router_result') and ctx.router_result and hasattr(ctx.router_result, 'tool'):
                    internal["router"] = {
                        "tool": ctx.router_result.tool,
                        "confidence": getattr(ctx.router_result, 'confidence', 0),
                        "reason": getattr(ctx.router_result, 'reason', ''),
                    }
                mc = ctx.memory_context or {}
                internal["memory"] = {
                    "wiki_count": len(mc.get("wiki_results", [])),
                    "has_episodic": bool(mc.get("episodic_context", "")),
                    "has_profile": bool(mc.get("profile_context", "")),
                }
                kb = _agent._knowledge_base
                if kb is not None:
                    concepts = asyncio.run(kb.list_concepts())
                    internal["kb"] = {"prompt_injected": len(concepts) > 0, "concept_count": len(concepts)}
                reasoning = mc.get("reasoning_context")
                if reasoning and hasattr(reasoning, "key_concepts"):
                    internal["reasoning"] = {
                        "key_concepts": reasoning.key_concepts[:8],
                        "insights": getattr(reasoning, "inferred_insights", [])[:3],
                        "confidence": getattr(reasoning, "confidence", 0),
                    }

                yield f"data: {json.dumps({'done': True, 'session_id': session_id, 'duration_ms': duration, 'internal': internal}, ensure_ascii=False)}\n\n"
                break

        thread.join()

    return Response(stream_with_context(generate()), mimetype='text/event-stream')


@app.get("/api/health")
def api_health():
    health = asyncio.run(_agent.health_check())  # type: ignore[union-attr]
    state = asyncio.run(_agent.get_state())  # type: ignore[union-attr]
    kb_enabled = _agent._knowledge_base is not None

    # Count episodes from both in-memory and disk
    episodic_count = _agent._episodic.count if _agent._episodic else 0
    if episodic_count == 0 and _agent._memory_store is not None:
        try:
            episodes = asyncio.run(_agent._memory_store.load_episodes())
            episodic_count = len(episodes)
        except Exception:
            pass

    return jsonify({
        "status": health.status, "version": health.version, "model": health.model,
        "memory_episodic_count": episodic_count,
        "cognitive_health_score": health.cognitive_health_score,
        "tool_count": state.get("tool_count", 0),
        "skill_count": state.get("skill_count", 0),
        "kb_enabled": kb_enabled,
        "kb_path": _agent._knowledge_base.base_path if kb_enabled else "",
    })


@app.post("/api/reset")
def api_reset():
    global _agent
    asyncio.run(_agent.shutdown())  # type: ignore[union-attr]
    _agent = None
    return jsonify({"ok": True})


@app.get("/api/kb/info")
def api_kb_info():
    kb = _agent._knowledge_base
    if kb is None:
        return jsonify({"enabled": False})
    summaries = asyncio.run(kb.list_summaries())
    concepts = asyncio.run(kb.list_concepts())
    return jsonify({
        "enabled": True, "path": kb.base_path,
        "summary_count": len(summaries), "concept_count": len(concepts),
    })


@app.get("/api/kb/search")
def api_kb_search():
    kb = _agent._knowledge_base
    if kb is None:
        return jsonify({"results": [], "count": 0})
    query = request.args.get("query", "")
    results = asyncio.run(kb.search(query))
    return jsonify({"results": results, "count": len(results)})


@app.get("/api/kb/graph")
def api_kb_graph():
    if _agent._knowledge_base is None:
        return jsonify({"nodes": [], "edges": [], "concept_count": 0, "total_edges": 0})
    return jsonify(asyncio.run(_build_graph_data(_agent._knowledge_base)))


async def _build_graph_data(kb) -> dict:
    import re
    import yaml

    concept_files = await kb.list_concepts()

    _YAML_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)", re.DOTALL)
    nodes = []
    edges = []
    all_tags: dict[str, list[str]] = {}

    for fname in concept_files:
        slug = fname.replace(".md", "")
        try:
            raw = await kb.read_concept(slug)
            m = _YAML_RE.match(raw)
            fm = yaml.safe_load(m.group(1)) if m else {}
            if not isinstance(fm, dict):
                fm = {}
            body = m.group(2).strip() if m else raw

            name_match = re.match(r"^#\s*概念[：:]\s*(.+)", body)
            display_name = name_match.group(1).strip() if name_match else slug

            tags = fm.get("tags", []) or []
            related = fm.get("related", []) or []
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",") if t.strip()]
            if isinstance(related, str):
                related = [r.strip() for r in related.split(",") if r.strip()]

            all_tags[slug] = tags
            nodes.append({
                "id": slug,
                "label": display_name,
                "confidence": 0.7,
                "degree": len(related),
                "tags": tags,
            })

            for r in related:
                edges.append({"from": slug, "to": r, "weight": 0.8, "type": "related"})
        except Exception:
            nodes.append({
                "id": slug, "label": slug, "confidence": 0.5,
                "degree": 0, "tags": [],
            })

    # Deduplicate edges
    seen = set()
    deduped = []
    for e in edges:
        key = tuple(sorted([e["from"], e["to"]]))
        if key not in seen:
            seen.add(key)
            deduped.append(e)

    # Tag-overlap edges
    slugs = list(all_tags.keys())
    for i in range(len(slugs)):
        for j in range(i + 1, len(slugs)):
            shared = set(all_tags[slugs[i]]) & set(all_tags[slugs[j]])
            if shared:
                key = tuple(sorted([slugs[i], slugs[j]]))
                if key not in seen:
                    seen.add(key)
                    deduped.append({
                        "from": slugs[i], "to": slugs[j],
                        "weight": round(0.3 + len(shared) / max(len(all_tags[slugs[i]]), len(all_tags[slugs[j]])), 2),
                        "type": "tag-overlap",
                    })

    return {
        "nodes": nodes,
        "edges": deduped,
        "concept_count": len(nodes),
        "total_edges": len(deduped),
    }


# ── Web UI ──

@app.get("/")
def index():
    health = asyncio.run(_agent.health_check())  # type: ignore[union-attr]
    return render_template("index.html", status=health.status, model=health.model)


if __name__ == "__main__":
    print("Starting Agent Framework Frontend...")
    print("Web UI:  http://127.0.0.1:5001")
    print("API:     http://127.0.0.1:5001/api/")
    app.run(host="127.0.0.1", port=5001, debug=False)
