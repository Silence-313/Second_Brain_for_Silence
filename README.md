# Second Brain for Silence

Python Agent Framework — 5 层认知架构，12 阶段请求流水线，约 9000 行 Python，37 个测试文件（79 个测试类）。

## 架构概览

```
用户输入 → Sanitize → Route → Retrieve → Reason → Plan → Execute → Prompt → Generate → Sanitize Response → Persist → Learn → Health
              ↑                                                                                                            │
              └──────────────────────── 认知反馈回路（memory evolution / concept evolver / policy drift）──────────────────┘
```

六层端口抽象：`LLMClient` | `HttpClient` | `FileStorage` | `VectorStore` | `EventBus` | `Logger`，全部通过 `Protocol` 定义，运行时适配器注入。

## 12 阶段流水线

| 阶段 | 名称 | 职责 |
|------|------|------|
| P0 | Sanitize | 输入清洗、敏感信息过滤 |
| P1 | Route | 关键词评分意图路由 + 自适应遥测 |
| P2 | Retrieve | 多源记忆检索（向量 + 全文 + 图谱） |
| P3 | Reason | 概念图推理（3 策略引擎） |
| P4 | Plan | 计划生成 + 资源调度 |
| P5 | Execute | 工具/技能编排执行 |
| P6 | Prompt | 提示词组装（记忆 + 概念 + 搜索结果注入） |
| P7 | Generate | LLM 调用 + SSE 流式输出 |
| P8 | Sanitize Response | 响应清洗、防幻觉校验 |
| P9 | Persist | 对话写入 chat-log + 记忆持久化 |
| P10 | Learn | 每 5 轮自动提取概念、更新知识库 |
| P11 | Health | 健康检查 + 记忆计数兜底 |

## 记忆系统

| 组件 | 类型 | 说明 |
|------|------|------|
| WorkingMemory | 短期 | 当前对话上下文窗口 |
| EpisodicMemory | 长期 | 磁盘持久化情景记忆 |
| UserProfile | 长期 | 用户画像（硬编码种子 + LLM 提取） |
| ToolMemory | 统计 | 工具使用频率/成功率记录 |
| MemoryStore | 存储层 | YAML frontmatter 读写 |
| MemoryWriter | 决策层 | 写入策略判断（阈值门控） |

## 认知核心

### 推理引擎 — 3 策略

1. **概念图遍历** — TF-IDF + 向量相似度检索相关概念子图
2. **关联推理** — 跨簇连接发现（`_enrich_cross_connections`）
3. **反馈驱动** — 反馈信号触发策略调节（认知策略调节器）

### 变更运行时

所有状态变更通过 `MutationQueue → StateMutationEngine.validate() → apply()` 单一路径，保证可审计、可回放。

7 种判别联合变更类型：`ConceptUpdate` | `ConceptMerge` | `ConceptDecay` | `MemoryWrite` | `PolicyUpdate` | `ReasoningTrace` | `RelationshipMark`，Pydantic `Literal` + `TypeAdapter` 反序列化。

### 进化系统

- **MemoryEvolution** — 衰减（frequency × recency）、强化、阈值合并
- **ConceptEvolver** — 概念权重迭代 + 过时概念淘汰
- **CognitivePolicy** — 偏好平衡、压缩检测、健康评分

## 事件模型

26 种 `PipelineEvent` 事件（`InputSanitized` → `LLMChunkReceived` → `AgentShutdown`），`ExecutionTracer` 收集，`MetricsCollector` 聚合，`HealthCheck` 端点暴露。

## 知识库（llm-wiki）

- 对话 → `chat-log.md` → LLM 提取概念 → `concepts/*.md` → 更新 `index.md` / `overview.md`
- `log.md` 记录维护历史
- 前端 D3.js v7 力导向图展示概念图谱，支持缩放、拖拽、点击详情

## 联网搜索

三层回退：DuckDuckGo → Bing → 搜狗，搜索结果以 `标题 + URL + 摘要` 可读格式注入 LLM 提示词。

## 快速开始

```bash
conda activate agent
pip install -e ".[dev]"
python frontend/app.py
```

Web UI: `http://127.0.0.1:5001`

## 运行测试

```bash
pytest tests/ -v --cov=agent
```

## 配置

环境变量前缀 `AGENT_`，`.env` 加载：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `llm_endpoint` | `https://api.deepseek.com/v1` | LLM API 端点 |
| `llm_model` | `deepseek-v4-flash` | 模型名 |
| `llm_api_key` | — | DeepSeek API Key |
| `memory_base_path` | `./agent-memory` | 记忆存储路径 |
| `knowledge_base_enabled` | `true` | 启用知识库 |
| `knowledge_base_path` | `./knowledge-base` | 知识库路径 |
