# 农智助手 | Agricultural Assistant

> 基于 LangChain + Multi-Agent 架构的农业知识问答与作物病害诊断系统。

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.137+-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Vue](https://img.shields.io/badge/Vue-3.5-4FC08D?logo=vue.js)](https://vuejs.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 系统架构

```
Frontend (Vue 3 + Element Plus)
    ↘ SSE / REST
Backend (FastAPI)
    ├── Router (Async LLM Classify → if-else dispatch)
    ├── Knowledge Agent (ReAct: RAG + Web Search + Cite)
    ├── General Agent (ReAct: Web Search)
    ├── Diagnose Agent (VLM multi-modal)
    └── Fact Checker (BM25 entity matching)
Data
    ├── Chroma (Vector DB)
    ├── MySQL (Users / Sessions / Messages)
    └── Tavily (Web Search)
```

## 功能特性

- **农业知识问答** — RAG 本地知识库 + Tavily 网络搜索增强
- **作物病害诊断** — 多模态 VLM 图片识别 + 自动关联防治方案
- **多智能体路由** — Async Router 按意图分类调度（agriculture / general / clarify）
- **事实核查** — BM25 精确匹配，标记回答中无依据的实体
- **SSE 流式对话** — 逐 token 渲染，实时反馈
- **知识库管理** — 增量入库、MD5 去重、交叉编码器重排序
- **用户认证** — JWT + bcrypt，支持游客模式
- **会话管理** — MySQL 持久化，多会话切换

## 快速开始

### 环境要求

- Python 3.12+
- Node.js 18+
- MySQL 8.0+（可选，不配置时自动降级为游客模式）

### 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入 API Key
```

| 变量 | 说明 | 获取地址 |
|------|------|----------|
| `DASHSCOPE_API_KEY` | 阿里云百炼 API Key | [dashscope.aliyun.com](https://dashscope.aliyun.com) |
| `LLM_MODEL` | 对话/诊断模型 | `qwen3-omni-flash` |
| `EMBEDDING_MODEL` | 嵌入模型 | `text-embedding-v4` |
| `TAVILY_API_KEY` | 网络搜索 Key | [tavily.com](https://tavily.com) |
| `DB_HOST/PORT/USER/PASSWORD/NAME` | MySQL 连接（可选） | |

### 2. 启动后端

```bash
pip install -e .                # 安装依赖
uvicorn main:app --reload --port 8000
```

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev                     # 开发模式
npm run build                   # 生产构建
```

访问 `http://localhost:5173/chat/`

### Docker 部署

```bash
docker compose up -d
```

## 项目结构

```
├── agent/              # 智能体核心
│   ├── supervisor.py    # Async Router 调度器
│   ├── knowledge_agent.py   # ReAct Agent: 知识问答
│   ├── general_agent.py     # ReAct Agent: 通用闲聊
│   ├── diagnose.py      # 农业调度器 + 图片诊断
│   ├── critic.py        # BM25 事实核查器
│   └── agent_tools/     # 工具集 (tools.py: web_search, knowledge_cr, source_cite)
├── api/                # REST API 路由
├── auth/               # JWT + bcrypt 认证
├── config/             # Pydantic Settings
├── db/                 # SQLAlchemy 模型
├── service/            # 服务层 (RAG, Cache, Guard, Geo)
├── factory/            # 模型工厂
├── prompt/             # Agent Prompt 模板
├── scripts/            # 工具脚本
├── utils/              # 路径、日志、文件处理
├── data/               # 运行时数据（gitignore）
│   └── eval/           # 评估测试集
└── frontend/           # Vue 3 SPA
```

## 评估

项目内置 20 条农业问答测试集，使用 RAGAS 框架评估：

```bash
pip install ragas
python scripts/evaluate.py
```

## 技术栈

| 层 | 技术 |
|----|------|
| 后端框架 | FastAPI (Python 3.12+) |
| LLM 编排 | LangChain + Async Router |
| 基础模型 | Qwen3-Omni-Flash (DashScope) |
| 嵌入/重排序 | text-embedding-v4 + qwen3-rerank |
| 向量数据库 | Chroma (本地持久化) |
| 网络搜索 | Tavily Search API |
| 关系数据库 | MySQL + SQLAlchemy |
| 认证 | JWT (python-jose) + bcrypt |
| 安全 | slowapi + 自研 Guard 规则引擎 |
| 前端 | Vue 3 + Element Plus + Vite |

## 许可证

MIT License — 详见 [LICENSE](LICENSE)
