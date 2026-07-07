# Second Brain for Silence

Python Agent Framework — 个人第二大脑系统，基于 5 层认知架构（记忆 → 概念 → 推理 → 反馈 → 策略），支持 12 阶段请求流水线。

## 快速开始

```bash
conda activate agent
pip install -e ".[dev]"
python frontend/app.py
```

Web UI: `http://127.0.0.1:5001`

## 运行测试

```bash
pytest tests/ -v
```

## 架构

- **Ports & Adapters** — 所有外部依赖通过 Protocol 接口抽象
- **依赖反转** — 高层模块依赖抽象，不依赖实现
- **异步优先** — 所有 I/O async，CPU 密集型工作隔离
- **不可变模型** — Pydantic frozen 模型，单一事实来源

## 项目结构

| 路径 | 用途 |
|------|------|
| `agent/` | 框架源码（12 层） |
| `agent/pipeline/` | 12 阶段流水线 |
| `agent/memory/` | 记忆系统（工作、情景、画像） |
| `agent/reasoning/` | 概念图 + 推理引擎 |
| `agent/knowledge/` | llm-wiki 知识库 |
| `agent/tools/` | 工具系统 |
| `agent/search/` | 联网搜索（DuckDuckGo / Bing / 搜狗） |
| `frontend/` | Flask Web 前端 |
| `tests/` | 304 个测试 |
| `docs/` | 设计文档 |

## 配置

环境变量前缀 `AGENT_`，从 `.env` 加载：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `llm_endpoint` | `https://api.deepseek.com/v1` | LLM API 端点 |
| `llm_model` | `deepseek-v4-flash` | 模型名 |
| `llm_api_key` | — | DeepSeek API Key |
| `memory_base_path` | `./agent-memory` | 记忆存储路径 |
| `knowledge_base_enabled` | `true` | 启用知识库 |
| `knowledge_base_path` | `./knowledge-base` | 知识库路径 |

## 许可

MIT
