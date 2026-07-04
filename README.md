<div align="center">

# 🔥 Novel Forge

### 网文故事基因与长篇创作辅助系统 / AI-Powered Long-Form Novel Creation Engine

<p>
<strong>从创意到正文，用结构化数据驱动百万字长篇小说创作</strong><br/>
<em>From a one-line idea to a million-word novel — powered by structured data and AI</em>
</p>

---

<p>
  <a href="#-中文">🇨🇳 中文</a> &nbsp;|&nbsp;
  <a href="#-english">🇺🇸 English</a>
</p>

<p>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Next.js-16-000000?style=flat&logo=next.js&logoColor=white" alt="Next.js" />
  <img src="https://img.shields.io/badge/TypeScript-5.9-3178C6?style=flat&logo=typescript&logoColor=white" alt="TypeScript" />
  <img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=flat&logoColor=white" alt="SQLAlchemy" />
</p>
<p>
  <img src="https://img.shields.io/badge/Tests-272_passing-4CAF50?style=flat" alt="Tests" />
  <img src="https://img.shields.io/badge/License-MIT-blue?style=flat" alt="License" />
  <img src="https://img.shields.io/badge/API_Endpoints-116+-FF6F00?style=flat" alt="API" />
  <img src="https://img.shields.io/badge/Pages-22-9C27B0?style=flat" alt="Pages" />
</p>

</div>

---

## 🇨🇳 中文

### 为什么需要 Novel Forge？

写一部百万字长篇网文，你需要**同时维护**：

| 挑战 | 描述 |
|:---|:---|
| 🧑‍🤝‍🧑 角色网络 | 几十个角色的性格、关系、成长轨迹 |
| 🧩 伏笔系统 | 数百条伏笔的埋设与回收 |
| 🌍 世界观规则 | 科技树、魔法体系、社会结构的一致性 |
| ⚔️ 战力与设定 | 战力体系、时间线、地理设定的精准管理 |
| 📈 节奏控制 | 每章的情绪曲线、高潮低谷、读者留存 |

> **人类大脑不擅长做这个。**
> Novel Forge 把这些结构化为数据，让 AI 辅助你完成繁琐的一致性维护，而你专注于**创作本身**。

---

### 核心特性

<table>
<tr>
<td width="50%">

#### 🎨 创意阶段
- **创意方向生成** — 一句话变 3 个结构化方向
- **融合与编辑** — 保留 AI 原始版，逐字段编辑，支持方案融合

#### 📖 大纲阶段
- **小说圣经** — 人物/规则/剧情/伏笔统一管理
- **全书总纲** — 14 维故事架构，版本化管理
- **分卷大纲** — 每卷目标、冲突、成长线
- **章节节奏表** — 10 种功能章节规划

</td>
<td width="50%">

#### ✍️ 创作阶段
- **单章策划** — 每章 3 个方案，场景/阻碍/转折/钩子
- **正文生成** — 带文风参数的 AI 草稿，段落级重写
- **版本管理** — 5 种版本类型，diff 比较，一键恢复

#### 🔍 分析阶段
- **故事基因分析** — 从文本提取冲突/情绪/爽点/伏笔
- **批量分析** — 多章节并发，失败隔离
- **状态变化提取** — AI 提取 + 人工确认 → 更新圣经

</td>
</tr>
</table>

#### 🛡️ 安全机制

| 机制 | 说明 |
|:---|:---|
| 权利登记 | 6 种权利状态，自动推导分析/参考权限 |
| AI 隔离 | AI 不直接修改圣经，所有建议需人工确认 |
| 事务保护 | 操作失败自动回滚 |
| 版本历史 | 任何修改可追溯、可恢复 |

---

### 技术架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     🌐 Browser (localhost:3001)                  │
│           Next.js 16 + TypeScript + Tailwind CSS                │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API
┌────────────────────────────▼────────────────────────────────────┐
│                    ⚡ FastAPI (localhost:8000)                    │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐   │
│  │ 📁 项目管理 │  │ 📝 文本处理 │  │ 🤖 LLM服务 │  │ 🔬 分析引擎│   │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘   │
│  ┌────────────────────────────────────────────────────────┐     │
│  │              SQLAlchemy 2 + Pydantic v2                │     │
│  └────────────────────────────────────────────────────────┘     │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│              🗄️  PostgreSQL 16 + pgvector (Docker)               │
│   novel_projects │ source_documents │ chapters │ bible_* │ …    │
└─────────────────────────────────────────────────────────────────┘
```

---

### 快速开始

<details>
<summary><strong>📋 前置条件</strong></summary>

- Docker Desktop
- Python 3.12+
- Node.js 22+
- pnpm
- uv

</details>

```bash
# 1. 克隆项目
git clone <repo-url> novel-forge && cd novel-forge

# 2. 配置环境变量
cp .env.example apps/api/.env
cp .env.example apps/web/.env.local

# 3. 启动数据库
make db-up

# 4. 启动后端 (Terminal 1)
make api

# 5. 启动前端 (Terminal 2)
make web
```

> 🎉 访问 **http://localhost:3001** 开始创作！

#### 运行测试

```bash
make api-test    # 272 个测试
make check       # 全部检查（lint + test + typecheck）
```

---

### 创作工作流

```
  💡 一句话创意
     ↓ AI 生成 3 个方向
  🔀 选择方向 + 编辑
     ↓ 生成圣经候选
  ✅ 人工确认 → 小说圣经
     ↓ 生成总纲
  ✏️  编辑 + 采用
     ↓ 生成分卷大纲
  📑 逐卷编辑
     ↓ 生成章节节奏表
  📝 逐章编辑
     ↓ 生成 3 个策划方案
  🎯 选择方案
     ↓ 生成正文草稿
  ✨ 编辑 + AI 改写/扩写/压缩
     ↓ 提取状态变化
  ✅ 人工确认 → 更新圣经
     📤 导出
```

---

### 项目结构

```
novel-forge/
├── apps/
│   ├── api/                    # FastAPI 后端
│   │   ├── app/
│   │   │   ├── api/routes/     # 17 个 API 路由模块
│   │   │   ├── core/           # 配置、日志、异常处理
│   │   │   ├── db/models/      # 12 个 SQLAlchemy 模型
│   │   │   ├── llm/            # 统一 LLM Provider 接口
│   │   │   ├── schemas/        # Pydantic v2 Schema
│   │   │   └── services/       # 业务逻辑层
│   │   ├── alembic/            # 数据库迁移（16 个版本）
│   │   └── tests/              # 272 个测试
│   └── web/                    # Next.js 前端
│       ├── app/                # 22 个页面（App Router）
│       └── lib/api.ts          # 类型安全的 API 客户端
├── data/                       # 本地数据（不入 Git）
├── docs/                       # 项目文档
├── docker-compose.yml          # PostgreSQL + pgvector
├── Makefile                    # 常用命令
└── README.md
```

---

### LLM Provider

默认使用 **Mock Provider**（无需 API Key，返回预设数据）。切换到真实模型：

```bash
# apps/api/.env
LLM_PROVIDER=openai
LLM_API_KEY=sk-xxx
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
```

> 支持所有 OpenAI 兼容接口：OpenAI / DeepSeek / Moonshot / Ollama 等。

---

### API 概览

> 完整 API 文档：启动后端后访问 **http://127.0.0.1:8000/docs**

| 模块 | 端点 | 说明 |
|:---|:---:|:---|
| 项目管理 | 8 | CRUD + 归档/恢复 + 统计 |
| 文件与章节 | 10 | 上传、解析、编辑、合并/拆分 |
| 故事基因 | 5 | 分析、历史、结果 |
| 批量分析 | 5 | 创建、状态、取消、重试 |
| 小说圣经 | 28 | 人物/规则/剧情/伏笔 CRUD |
| 创意方向 | 7 | 生成、采用、编辑、融合 |
| 圣经候选 | 6 | 生成、确认、应用、撤销 |
| 总纲 | 7 | 生成、版本、编辑、diff |
| 分卷大纲 | 7 | 生成、编辑、重排 |
| 章节节奏 | 8 | 生成、编辑、插入/删除/重排 |
| 单章策划 | 8 | 3 方案、采用、融合 |
| 正文草稿 | 6 | 生成、编辑、段落重写 |
| 版本管理 | 7 | 保存、恢复、diff、正式标记 |
| 状态变化 | 5 | 提取、接受、拒绝、撤销 |
| LLM Provider | 4 | 列表、健康检查、测试、日志 |

---

### 数据与版权原则

| | 原则 |
|:---:|:---|
| ❌ | 不抓取盗版小说 |
| ❌ | 不自动登录小说平台 |
| ❌ | 不自动发布小说 |
| ❌ | 不模仿具体在世作者 |
| ✅ | 仅保存抽象标签和摘要，不保留原文片段 |
| ✅ | 未授权文件默认不进入分析/生成参考库 |
| ✅ | 用户可随时删除所有数据 |
| ✅ | AI 建议与人工确认严格分离 |

---

<details>
<summary><strong>❓ 常见问题</strong></summary>

**Q: Docker Desktop 启动失败？**
确保 Docker Desktop 已启动且状态栏图标为绿色。macOS 上 Docker 有时会在空闲后自动停止引擎。

**Q: 端口被占用？**
端口 3000 可能被 Docker Desktop 占用，前端使用 3001。修改 `.env` 中的端口配置即可。

**Q: 如何切换到真实 LLM？**
编辑 `apps/api/.env`，设置 `LLM_PROVIDER=openai` 并填写 API Key 和 Base URL。

**Q: 测试需要数据库吗？**
不需要。后端测试使用 SQLite 内存数据库，无需 Docker 即可运行。

</details>

---

### 技术栈详情

| 层 | 技术 | 版本 |
|:---|:---|:---:|
| 前端框架 | Next.js (App Router) | 16.x |
| 类型系统 | TypeScript | 5.9 |
| 样式 | Tailwind CSS | 4.x |
| 后端框架 | FastAPI | 0.115+ |
| ORM | SQLAlchemy (async) | 2.0 |
| 数据校验 | Pydantic v2 | 2.10+ |
| 数据库 | PostgreSQL + pgvector | 16 |
| 迁移 | Alembic | 1.14+ |
| 包管理 | pnpm (前端) / uv (后端) | latest |
| 容器 | Docker Compose | v5 |
| 测试 | pytest + httpx | latest |
| Lint | Ruff (后端) / ESLint (前端) | latest |

---

<div align="center">

**MIT License** &nbsp;|&nbsp; Made with ❤️

> **Novel Forge** — 让 AI 帮你维护一致性，你专注于讲好故事。

</div>

---

## 🇺🇸 English

### Why Novel Forge?

Writing a million-word web novel means juggling **all of these simultaneously**:

| Challenge | Description |
|:---|:---|
| 🧑‍🤝‍🧑 Character Networks | Dozens of characters with personalities, relationships, and growth arcs |
| 🧩 Foreshadowing System | Hundreds of planted hints and their payoffs |
| 🌍 World Rules | Tech trees, magic systems, social structures — all consistent |
| ⚔️ Power & Settings | Power levels, timelines, geography — tracked precisely |
| 📈 Pacing Control | Per-chapter emotional curves, climaxes, reader retention |

> **Human brains aren't built for this.**
> Novel Forge structures it all as data, letting AI handle consistency grunt work while you **focus on storytelling**.

---

### Core Features

<table>
<tr>
<td width="50%">

#### 🎨 Ideation
- **Direction Generation** — One idea → 3 structured directions
- **Merge & Edit** — Keep AI originals, edit field by field, fuse proposals

#### 📖 Outlining
- **Story Bible** — Unified management of characters, rules, plotlines, foreshadowing
- **Master Outline** — 14-dimension story architecture, versioned
- **Volume Outlines** — Per-volume goals, conflicts, growth arcs
- **Chapter Rhythm** — 10 chapter types for pacing

</td>
<td width="50%">

#### ✍️ Writing
- **Chapter Planning** — 3 proposals per chapter: scene/obstacle/twist/hook
- **Draft Generation** — AI drafts with style parameters, paragraph-level rewrite
- **Version Control** — 5 version types, diff comparison, one-click restore

#### 🔍 Analysis
- **Story Gene Analysis** — Extract conflict, emotion, satisfaction, foreshadowing from text
- **Batch Analysis** — Multi-chapter concurrent, failure isolation
- **State Change Extraction** — AI extracts + human confirms → updates bible

</td>
</tr>
</table>

#### 🛡️ Safety Mechanisms

| Mechanism | Description |
|:---|:---|
| Rights Registration | 6 rights states, auto-derives analysis/reference permissions |
| AI Isolation | AI never directly modifies the bible — all suggestions require human confirmation |
| Transaction Safety | Automatic rollback on failure |
| Version History | Every change is traceable and reversible |

---

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     🌐 Browser (localhost:3001)                  │
│           Next.js 16 + TypeScript + Tailwind CSS                │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API
┌────────────────────────────▼────────────────────────────────────┐
│                    ⚡ FastAPI (localhost:8000)                    │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐   │
│  │ 📁 Project │  │ 📝 Text    │  │ 🤖 LLM    │  │ 🔬 Analysis│  │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘   │
│  ┌────────────────────────────────────────────────────────┐     │
│  │              SQLAlchemy 2 + Pydantic v2                │     │
│  └────────────────────────────────────────────────────────┘     │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│              🗄️  PostgreSQL 16 + pgvector (Docker)               │
│   novel_projects │ source_documents │ chapters │ bible_* │ …    │
└─────────────────────────────────────────────────────────────────┘
```

---

### Quick Start

<details>
<summary><strong>📋 Prerequisites</strong></summary>

- Docker Desktop
- Python 3.12+
- Node.js 22+
- pnpm
- uv

</details>

```bash
# 1. Clone
git clone <repo-url> novel-forge && cd novel-forge

# 2. Configure environment
cp .env.example apps/api/.env
cp .env.example apps/web/.env.local

# 3. Start database
make db-up

# 4. Start backend (Terminal 1)
make api

# 5. Start frontend (Terminal 2)
make web
```

> 🎉 Visit **http://localhost:3001** to start creating!

#### Run Tests

```bash
make api-test    # 272 tests
make check       # Full check (lint + test + typecheck)
```

---

### Creative Workflow

```
  💡 One-line idea
     ↓ AI generates 3 directions
  🔀 Pick & edit direction
     ↓ Generate bible candidates
  ✅ Human confirms → Story Bible
     ↓ Generate master outline
  ✏️  Edit & adopt
     ↓ Generate volume outlines
  📑 Edit per volume
     ↓ Generate chapter rhythm
  📝 Edit per chapter
     ↓ Generate 3 planning proposals
  🎯 Pick proposal
     ↓ Generate draft
  ✨ Edit + AI rewrite/expand/compress
     ↓ Extract state changes
  ✅ Human confirms → Update bible
     📤 Export
```

---

### Project Structure

```
novel-forge/
├── apps/
│   ├── api/                    # FastAPI backend
│   │   ├── app/
│   │   │   ├── api/routes/     # 17 API route modules
│   │   │   ├── core/           # Config, logging, exceptions
│   │   │   ├── db/models/      # 12 SQLAlchemy models
│   │   │   ├── llm/            # Unified LLM Provider interface
│   │   │   ├── schemas/        # Pydantic v2 schemas
│   │   │   └── services/       # Business logic layer
│   │   ├── alembic/            # DB migrations (16 versions)
│   │   └── tests/              # 272 tests
│   └── web/                    # Next.js frontend
│       ├── app/                # 22 pages (App Router)
│       └── lib/api.ts          # Type-safe API client
├── data/                       # Local data (not in Git)
├── docs/                       # Documentation
├── docker-compose.yml          # PostgreSQL + pgvector
├── Makefile                    # Common commands
└── README.md
```

---

### LLM Provider

Defaults to **Mock Provider** (no API key needed, returns preset data). Switch to a real model:

```bash
# apps/api/.env
LLM_PROVIDER=openai
LLM_API_KEY=sk-xxx
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
```

> Compatible with all OpenAI-format APIs: OpenAI / DeepSeek / Moonshot / Ollama, etc.

---

### API Overview

> Full API docs: start the backend and visit **http://127.0.0.1:8000/docs**

| Module | Endpoints | Description |
|:---|:---:|:---|
| Projects | 8 | CRUD + archive/restore + stats |
| Files & Chapters | 10 | Upload, parse, edit, merge/split |
| Story Genes | 5 | Analyze, history, results |
| Batch Analysis | 5 | Create, status, cancel, retry |
| Story Bible | 28 | Characters/rules/plot/foreshadowing CRUD |
| Creative Directions | 7 | Generate, adopt, edit, fuse |
| Bible Candidates | 6 | Generate, confirm, apply, undo |
| Master Outline | 7 | Generate, version, edit, diff |
| Volume Outlines | 7 | Generate, edit, reorder |
| Chapter Rhythm | 8 | Generate, edit, insert/delete/reorder |
| Chapter Planning | 8 | 3 proposals, adopt, fuse |
| Drafts | 6 | Generate, edit, paragraph rewrite |
| Version Control | 7 | Save, restore, diff, mark final |
| State Changes | 5 | Extract, accept, reject, undo |
| LLM Provider | 4 | List, health check, test, logs |

---

### Data & Copyright Principles

| | Principle |
|:---:|:---|
| ❌ | No scraping pirated novels |
| ❌ | No auto-login to novel platforms |
| ❌ | No auto-publishing novels |
| ❌ | No imitating specific living authors |
| ✅ | Only abstract tags and summaries stored, no original text fragments |
| ✅ | Unauthorized files excluded from analysis/reference by default |
| ✅ | Users can delete all data at any time |
| ✅ | AI suggestions strictly separated from human confirmation |

---

<details>
<summary><strong>❓ FAQ</strong></summary>

**Q: Docker Desktop won't start?**
Make sure Docker Desktop is running and the menu bar icon is green. On macOS, Docker sometimes stops the engine after idle.

**Q: Port conflict?**
Port 3000 may be taken by Docker Desktop — the frontend uses 3001. Change the port in `.env` if needed.

**Q: How to switch to a real LLM?**
Edit `apps/api/.env`, set `LLM_PROVIDER=openai` and fill in your API Key and Base URL.

**Q: Do tests need a database?**
No. Backend tests use an in-memory SQLite database — no Docker required.

</details>

---

### Tech Stack

| Layer | Technology | Version |
|:---|:---|:---:|
| Frontend | Next.js (App Router) | 16.x |
| Type System | TypeScript | 5.9 |
| Styling | Tailwind CSS | 4.x |
| Backend | FastAPI | 0.115+ |
| ORM | SQLAlchemy (async) | 2.0 |
| Validation | Pydantic v2 | 2.10+ |
| Database | PostgreSQL + pgvector | 16 |
| Migrations | Alembic | 1.14+ |
| Package Mgmt | pnpm (web) / uv (api) | latest |
| Container | Docker Compose | v5 |
| Testing | pytest + httpx | latest |
| Linting | Ruff (API) / ESLint (web) | latest |

---

<div align="center">

**MIT License** &nbsp;|&nbsp; Made with ❤️

> **Novel Forge** — Let AI handle consistency. You focus on the story.

</div>
