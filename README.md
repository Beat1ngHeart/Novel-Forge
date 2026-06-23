# 🔥 Novel Forge

> **网文故事基因与长篇创作辅助系统**
> 从创意到正文，用结构化数据驱动百万字长篇小说创作

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16-000000?style=flat&logo=next.js&logoColor=white)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178C6?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=flat&logoColor=white)](https://www.sqlalchemy.org/)
[![Tests](https://img.shields.io/badge/Tests-272_passing-4CAF50?style=flat)]()
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat)]()

---

## 为什么需要 Novel Forge？

写一部百万字长篇网文，你需要同时维护：

- 几十个角色的性格、关系、成长轨迹
- 数百条伏笔的埋设与回收
- 世界观规则的一致性
- 战力体系、时间线、地理设定
- 每章的情绪曲线和节奏控制

**人类大脑不擅长做这个。** Novel Forge 把这些结构化为数据，让 AI 辅助你完成繁琐的一致性维护，而你专注于创作本身。

---

## 核心特性

### 🎨 创意阶段
- **创意方向生成** — 输入一句话创意，AI 生成 3 个结构不同的方向
- **融合与编辑** — 保留 AI 原始版本，逐字段编辑，支持方案融合

### 📖 大纲阶段
- **小说圣经** — 人物、世界规则、剧情线、伏笔的统一管理
- **全书总纲** — 14 个维度的故事架构，版本化管理
- **分卷大纲** — 每卷目标、冲突、成长线、伏笔计划
- **章节节奏表** — 10 种不同功能的章节规划

### ✍️ 创作阶段
- **单章策划** — 每章 3 个方案，场景/阻碍/转折/钩子全覆盖
- **正文生成** — 带文风参数的 AI 草稿，支持段落级重写
- **版本管理** — 5 种版本类型，diff 比较，一键恢复

### 🔍 分析阶段
- **故事基因分析** — 从已有文本提取冲突/情绪/爽点/伏笔等叙事规律
- **批量分析** — 多章节并发，失败隔离，进度追踪
- **状态变化提取** — AI 提取正文中的设定变化，人工逐项确认后更新圣经

### 🛡️ 安全机制
- **权利登记** — 6 种权利状态，自动推导分析/参考权限
- **AI 不直接修改圣经** — 所有 AI 建议需人工确认
- **事务保护** — 操作失败自动回滚
- **版本历史** — 任何修改可追溯、可恢复

---

## 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                       浏览器 (localhost:3001)                │
│  Next.js 16 + TypeScript + Tailwind CSS + App Router        │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST API
┌──────────────────────────▼──────────────────────────────────┐
│                    FastAPI (localhost:8000)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ 项目管理  │  │ 文本处理  │  │ LLM 服务  │  │ 分析引擎 │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              SQLAlchemy 2 + Pydantic v2              │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│              PostgreSQL 16 + pgvector (Docker)               │
│  novel_projects │ source_documents │ chapters │ bible_* │ … │
└─────────────────────────────────────────────────────────────┘
```

---

## 快速开始

### 前置条件

- Docker Desktop
- Python 3.12+
- Node.js 22+
- pnpm
- uv

### 一键启动

```bash
# 克隆项目
git clone <repo-url> novel-forge
cd novel-forge

# 配置环境变量
cp .env.example apps/api/.env
cp .env.example apps/web/.env.local

# 启动数据库
make db-up

# 启动后端
make api

# 新终端，启动前端
make web
```

访问 **http://localhost:3001** 🎉

### 运行测试

```bash
make api-test    # 272 个测试
make check       # 全部检查（lint + test + typecheck）
```

---

## 项目结构

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

## 创作工作流

```
一句话创意
  ↓ AI 生成 3 个方向
选择方向 + 编辑
  ↓ 生成圣经候选
人工确认 → 小说圣经
  ↓ 生成总纲
编辑 + 采用
  ↓ 生成分卷大纲
逐卷编辑
  ↓ 生成章节节奏表
逐章编辑
  ↓ 生成 3 个策划方案
选择方案
  ↓ 生成正文草稿
编辑 + AI 改写/扩写/压缩
  ↓ 提取状态变化
人工确认 → 更新圣经
  ↓ 标记正式稿
导出
```

---

## LLM Provider

默认使用 **Mock Provider**（无需 API Key，返回预设数据）。

切换到真实模型：

```bash
# apps/api/.env
LLM_PROVIDER=openai
LLM_API_KEY=sk-xxx
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
```

支持所有 OpenAI 兼容接口（OpenAI、DeepSeek、Moonshot、Ollama 等）。

---

## API 概览

| 模块 | 端点数 | 说明 |
|---|---|---|
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

完整 API 文档：启动后端后访问 **http://127.0.0.1:8000/docs**

---

## 数据与版权原则

- ❌ 不抓取盗版小说
- ❌ 不自动登录小说平台
- ❌ 不自动发布小说
- ❌ 不模仿具体在世作者
- ✅ 仅保存抽象标签和摘要，不保留原文片段
- ✅ 未授权文件默认不进入分析/生成参考库
- ✅ 用户可随时删除所有数据
- ✅ AI 建议与人工确认严格分离

---

## 常见问题

**Q: Docker Desktop 启动失败？**
A: 确保 Docker Desktop 已启动且状态栏图标为绿色。macOS 上 Docker 有时会在空闲后自动停止引擎。

**Q: 端口被占用？**
A: 端口 3000 可能被 Docker Desktop 占用，前端使用 3001。修改 `.env` 中的端口配置即可。

**Q: 如何切换到真实 LLM？**
A: 编辑 `apps/api/.env`，设置 `LLM_PROVIDER=openai` 并填写 API Key 和 Base URL。

**Q: 测试需要数据库吗？**
A: 不需要。后端测试使用 SQLite 内存数据库，无需 Docker 即可运行。

---

## 技术栈详情

| 层 | 技术 | 版本 |
|---|---|---|
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

## 许可证

MIT License

---

> **Novel Forge** — 让 AI 帮你维护一致性，你专注于讲好故事。
