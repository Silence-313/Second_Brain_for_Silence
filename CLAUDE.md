# CLAUDE.md — Second Brain for Silence

## 项目概述

Python Agent Framework — 为 Silence 构建的个人第二大脑系统。基于 5 层认知架构（记忆 → 概念 → 推理 → 反馈 → 策略），支持 12 阶段请求流水线。

| 组件 | 值 |
|------|-----|
| Conda 环境 | `agent`（Python 3.12.13） |
| 工作目录 | `/Users/xuejingchen/Desktop/vscode/python/Second_brain_for_Silence/` |
| 源文件 | 121 个 .py 文件 |
| 测试 | 304 个（265 单元 + 39 集成） |
| Git 仓库 | `https://github.com/Silence-313/Second_Brain_for_Silence.git` |
| 默认分支 | `main` |

## 启动服务

```bash
conda activate agent
cd /Users/xuejingchen/Desktop/vscode/python/Second_brain_for_Silence
python frontend/app.py
```

Web UI: `http://127.0.0.1:5001`（端口 5000 被 macOS AirPlay Receiver 占用）

## 运行测试

```bash
conda activate agent
cd /Users/xuejingchen/Desktop/vscode/python/Second_brain_for_Silence
pytest tests/ -v
```

## 关键路径

| 路径 | 用途 |
|------|------|
| `agent/` | 框架源码（121 文件，12 层） |
| `agent/agent.py` | Agent 公开 API，组合根 |
| `agent/models/` | Pydantic 数据模型（13 类） |
| `agent/ports/` | 抽象协议（LLM、存储、HTTP、向量、事件总线） |
| `agent/memory/` | 记忆系统（工作、情景、画像、工具、存储、写入） |
| `agent/reasoning/` | 概念图构建 + 3 策略推理引擎 |
| `agent/routing/` | 关键词评分意图路由 + 自适应遥测 |
| `agent/tools/` | 工具系统（协议、注册表、决策策略、内置工具） |
| `agent/skills/` | 技能系统（协议、注册表、内置技能） |
| `agent/search/` | 搜索框架（协议、管理器、Bing/DuckDuckGo 提供者） |
| `agent/pipeline/` | 12 阶段流水线（sanitize → route → retrieve → reason → plan → execute → prompt → generate → sanitize_response → persist → learn → health） |
| `agent/evolution/` | 记忆进化（衰减、强化、合并）+ 概念进化器 |
| `agent/policy/` | 认知策略调节器（偏好平衡、压缩检测、健康评分） |
| `agent/core/` | 变更运行时（MutationQueue + StateMutationEngine） |
| `agent/infrastructure/` | 适配器实现（DeepSeek LLM、本地文件系统、HTTPX、TF-IDF） |
| `agent/knowledge/` | llm-wiki 知识库框架（管理器 + 10 个工具） |
| `agent/plugins/` | 插件 SDK（发现、加载、验证） |
| `agent/bus/` | 内存事件总线 |
| `frontend/app.py` | Flask Web 前端 |
| `docs/` | 4 份设计文档 + 对齐文档 |
| `.env` | 环境变量（API Key、模型名） |
| `.vscode/` | VS Code 配置（解释器、启动、linting） |

## 配置

环境变量前缀 `AGENT_`，从 `.env` 文件加载。

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `llm_endpoint` | `https://api.deepseek.com/v1` | LLM API 端点 |
| `llm_model` | `deepseek-v4-flash` | 模型名 |
| `llm_api_key` | — | DeepSeek API Key |
| `memory_base_path` | `./agent-memory` | 记忆存储路径 |
| `knowledge_base_enabled` | `true` | 启用 llm-wiki 知识库 |
| `knowledge_base_path` | `./knowledge-base` | 知识库路径 |

## 架构原则

- **Ports & Adapters**：每个外部依赖都通过 Protocol 接口抽象
- **依赖反转**：高层模块依赖抽象（Protocols），不依赖实现
- **单一事实来源**：CognitiveState 是权威状态快照，所有写入通过 MutationEngine
- **异步优先**：所有 I/O 操作 async，CPU 密集型工作隔离
- **不可变事件**：PipelineContext 和所有模型都是 frozen Pydantic
- **LLM 无状态**：Agent 拥有状态，LLM 是纯推理引擎

## Agent 身份

系统提示词将 Agent 定义为 Silence 的个人第二大脑（不是通用 AI 助手，不是 DeepSeek，不是豆包）。用户画像硬编码种子数据（Silence、编程、AI、知识管理）。

## 已解决问题

1. **macOS AirPlay Receiver 占用 5000 端口：** ✅ 已解决（2026-07-01）— 将 Flask 端口改为 5001。
2. **Event loop `run_until_complete` 报错：** ✅ 已解决（2026-07-01）— Flask 多线程模式下共享 event loop 不可靠，改为 `asyncio.run()`。
3. **prompt.py 缺少 `Any` 导入：** ✅ 已解决（2026-07-01）— 添加 `from typing import Any`。
4. **vis-network 9.x CDN 不创建浏览器全局变量：** ✅ 已解决（2026-07-01）— 改为 D3.js v7 实现力导向图。
5. **`.env` 文件首行被 corruption（`xian za` 前缀）：** ✅ 已解决（2026-07-01）— 手动修复。
6. **搜索不执行/返回空结果：** ✅ 已解决（2026-07-01）— (a) HTTP 客户端未实例化 → `HttpxHttpClient` 传入 WebSearchTool 和搜索提供者；(b) DuckDuckGoSearchProvider 解析正则不匹配 → 改用 `result__a` + DDG 重定向解码；(c) Intent 缺 `query` 字段 → 新增并全局填充；(d) `platform`/`platforms` 键名不匹配 → 统一为 `platforms`；(e) 短追问词"搜"不走搜索 → Planner 检测 ≤5 字追问，从聊天历史补全。
7. **LLM 编造链接/角色扮演工具调用：** ✅ 已解决（2026-07-01）— (a) 系统提示词新增 3 条反幻觉规则；(b) 执行结果格式化从截断 JSON dump 改为可读的 `1. 标题\n URL: xxx` 格式。
8. **手动"维护知识库"不提取概念：** ✅ 已解决（2026-07-01）— MaintainKBTool 注册时未传 `llm_client`，LLM=None → 直接清空 chat-log。
9. **侧边栏记忆计数为 0：** ✅ 已解决（2026-07-01）— EpisodicMemory 纯内存重启归零，health 端点增加磁盘 `load_episodes()` 兜底。

## 新增功能

### 流式渲染
- 端点：`POST /api/chat/stream`，SSE 格式逐 token 推送
- 前端用 `ReadableStream` 读取，实时渲染 markdown
- 流结束后自动更新 inspector 面板
- 降级：流式不可用时回退到非流式 `/api/chat`

### 知识图谱
- 端点：`GET /api/kb/graph`，返回节点+连线 JSON
- 前端用 D3 force 布局展示概念图谱，支持缩放、拖拽、点击查看详情
- 颜色按关联度/关系类型区分

### 知识库自动积累
- `PersistStage` 每次对话追加到 `knowledge-base/chat-log.md`
- `LearnStage` 每 5 轮自动触发 `kb_maintain`
- `kb_maintain` 调用 LLM 从 chat-log 提取概念、识别关联、更新索引和总览
- 维护后自动运行 `_enrich_cross_connections` 发现跨簇关联
- 也可在对话中说"维护知识库"手动触发

### 联网搜索
- 三层回退：DuckDuckGo → Bing → 搜狗
- WebSearchTool（`web_search`）用于 tool 类型步骤
- DuckDuckGoSearchProvider / SogouSearchProvider 用于 search 类型步骤
- 搜索结果以可读格式注入 LLM 提示词（标题 + URL + 摘要）

### 对话历史
- 前端 localStorage 持久化，刷新不丢失
- 每次请求携带最近 20 条历史给 LLM，支持多轮追问
- 侧边栏「导出对话」按钮下载 .txt

### 知识命中显示
- Inspector 顶部「知识命中」面板：显示 KB 注入状态、Wiki 匹配数、概念标签
- 也可在对话中说"维护知识库"手动触发

## 约定

- Python 3.12+，严格类型，async-first
- Pydantic 模型全部 frozen（不可变）
- Pydantic v2 字段约束验证（拒绝而非钳制越界值）
- 判别联合（StateMutation、PipelineEvent）使用 `Literal` + `TypeAdapter`
- datetime 始终附带时区（`datetime.now(UTC)`）
- MemroyStore YAML frontmatter 使用 pyyaml 而非手动字符串拼接
- ruff check + mypy --strict 必须通过
- 交流语言：中文，代码术语保留英文
