"""LLM Wiki knowledge base schema and rules."""

KB_SCHEMA = """# LLM Wiki 知识库

你是 Silence 的第二大脑知识库维护者。你的任务是阅读笔记并维护结构化的知识库。

## 目录结构

```
index.md       — 所有页面的目录，带链接和摘要
overview.md    — 知识领域总览
log.md         — 按时间顺序记录所有操作
summaries/     — 每篇笔记的摘要（YAML frontmatter + 正文）
concepts/      — 跨笔记的概念页面
chat-log.md    — 待消化的对话记录
profile.md     — 用户画像
```

## 摘要格式

```markdown
---
source: 原始笔记路径
source_mtime: 1720000000000
date: 2026-07-01
tags: [标签1, 标签2]
---

# 摘要: 笔记标题

## 关键要点
- 要点1
- 要点2

## 详细摘要
...

## 相关概念
- [[概念1]]
- [[概念2]]
```

## 规则

1. 用户笔记是只读的，绝对不要修改
2. 每个摘要页面要包含：来源文件名、关键要点、标签
3. 概念页面要交叉引用相关的笔记和摘要
4. 每次操作后更新 index.md 和 log.md
5. 发现矛盾或不一致时记录到 log.md
6. 所有页面用中文撰写
7. 维护完成后重建向量索引
"""

# Tags used for categorizing summary entries
SUMMARY_FRONTMATTER_KEYS = [
    "source",
    "source_mtime",
    "date",
    "tags",
]

# Top-level files that should never be deleted
PROTECTED_FILES = {"SCHEMA.md"}
