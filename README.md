# 农智助手 | Agricultural Assistant

<p align="center">
  <em>基于 LangChain Multi-Agent 架构的农业知识问答与作物病虫害诊断系统</em>
</p>

<p align="center">
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.12+-3776AB?logo=python" alt="Python"></a>
  <a href="https://fastapi.tiangolo.com"><img src="https://img.shields.io/badge/FastAPI-0.137+-009688?logo=fastapi" alt="FastAPI"></a>
  <a href="https://vuejs.org"><img src="https://img.shields.io/badge/Vue-3.5-4FC08D?logo=vue.js" alt="Vue"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow" alt="License"></a>
</p>

---

## 项目概述

农智助手是一个**面向农业领域的大模型问答与诊断系统**，核心围绕以下问题设计：

- **农户/农技员**如何用自然语言获取精准的农业技术知识？
- **作物病虫害**如何通过拍照快速识别并获取防治方案？
- **大模型幻觉**问题如何在实际农业场景中被有效遏制？

系统采用 **Supervisor + 多子 Agent** 的调度架构，串联 RAG 检索增强生成、Qwen-VLM 多模态诊断、Tavily 实时网络搜索，并以 BM25 事实校验模块对 LLM 输出做二次验证，构建了从"提问 → 检索 → 诊断 → 校验 → 回答"的完整链路。

---

## 功能特性

### Supervisor 路由调度
采用 **LLM-as-Classifier** 模式，用 DeepSeek 模型对用户提问做意图分类（农业知识 / 通用闲聊 / 模糊请求），配置不完整时自动降级到主模型。避免单一 Agent 处理多领域问题的精度瓶颈，同时减少不必要的模型调用开销。

### RAG 检索增强生成
完整的 RAG 管线包含 5 个步骤：

```
用户问题 → 查询改写（LLM 口语 → 书面）
  → text-embedding-v4 向量化
  → ChromaDB MMR 检索 (top-30)
  → qwen3-rerank 交叉编码器重排序 (top-3)
  → LLM 带上下文生成回答
```

关键设计决策：
- **查询改写**：去除"帮我""请问"等口语化前缀，保留时间/实体等关键信息
- **检索策略**：MMR（最大边际相关性），平衡相关性与多样性
- **重排序**：交叉编码器对初筛结果精排，准确度优于纯向量检索
- **语义缓存**：Embedding 余弦相似度阈值 0.92，TTL 5 分钟，减少重复检索

### Qwen-VLM 病害诊断
用户上传作物叶片照片 → Qwen-VL 多模态模型识别病害种类 → 自动提取病害名称 → 调用 Knowledge Agent 检索对应防治方案 → 返回"诊断 + 防治"完整回复。打通了**看图 → 诊断 → 给药**的业务闭环。

### BM25 事实校验（反幻觉模块）
针对 LLM 的幻觉问题，实现了一个**不依赖 LLM** 的事实验证器：

1. 从回答中用正则提取数值（浓度/剂量）、农药名、化学成分等可验证实体
2. 用 BM25 检索源知识库文档
3. 逐项匹配实体是否在源文档中出现
4. 无依据的实体在回答末尾附上 ⚠️ 标注

相比依赖 LLM 自检的方案，这种方式零额外 Token 消耗，且结果可溯源。

### 安全防护
- **InputGuard**：检测 prompt 注入、越狱攻击、系统提示泄露（中英文混合规则）
- **OutputGuard**：拦截模型输出中泄露的系统提示词
- **Rate Limiting**：slowapi 30 次/分钟限流
- **路径安全**：对文件上传/知识库操作做路径穿越检测

### 用户与会话管理
- JWT + bcrypt 双 Token 认证（Access + Refresh）
- 游客模式（跳过 MySQL，本地会话存储）
- MySQL 持久化聊天记录，支持多会话切换

---

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 后端框架 | FastAPI (Python 3.12+) | 异步高性能 |
| LLM 编排 | LangChain (ReAct Agent) | 工具调用 + 记忆 |
| 路由模型 | DeepSeek（可选降级到主模型） | 意图分类 |
| 对话/诊断模型 | Qwen3-Omni-Flash (DashScope) | 文本 + 多模态 |
| 嵌入模型 | text-embedding-v4 | 语义向量化 |
| 重排序 | qwen3-rerank | 交叉编码器精排 |
| 向量数据库 | ChromaDB | 本地持久化 + MMR 检索 |
| 关系数据库 | MySQL 8.0 + SQLAlchemy | ORM + 连接池 |
| 网络搜索 | Tavily Search API | 实时信息补充 |
| 认证 | python-jose + bcrypt | JWT 双 Token |
| 安全 | slowapi + 自研 Guard 规则 | 限流 + 防注入 |
| 前端 | Vue 3 + Element Plus + Vite | SPA |
| 部署 | Docker Compose | 一键启动 |

---

## 快速开始

### 前置条件

- Python 3.12+
- Node.js 18+
- MySQL 8.0+（可选，不配置时自动降级为游客模式）

### 1. 配置环境变量

```bash
cp .env.example .env
```

| 变量 | 必填 | 说明 | 获取地址 |
|------|------|------|----------|
| `DASHSCOPE_API_KEY` | ✅ | 阿里云百炼 API Key | [dashscope.aliyun.com](https://dashscope.aliyun.com) |
| `TAVILY_API_KEY` | ✅ | 网络搜索 Key | [tavily.com](https://tavily.com) |
| `LLM_MODEL` | | 对话/诊断模型（默认 qwen3-omni-flash） | |
| `EMBEDDING_MODEL` | | 嵌入模型（默认 text-embedding-v4） | |
| `DB_HOST/PORT/USER/PASSWORD/NAME` | | MySQL 连接（不配则用游客模式） | |

### 2. 本地开发

```bash
# 终端 1：启动后端
pip install -e .
uvicorn main:app --reload --port 8000

# 终端 2：启动前端
cd frontend
npm install
npm run dev
```

访问 `http://localhost:5173/chat/`

### 3. Docker 部署

```bash
docker compose up -d
```

---

## API 接口一览

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 用户注册 |
| POST | `/api/auth/login` | 用户登录 |
| GET | `/api/auth/me` | 获取当前用户 |
| POST | `/api/chat/supervisor` | 路由调度（自动分发） |
| POST | `/api/chat/knowledge` | 知识问答 |
| POST | `/api/diagnose` | 图片诊断（multipart） |
| GET | `/` | 服务状态 |

完整 API 文档在 `http://localhost:8000/docs`（Swagger UI）。

---

## 项目结构

```
AgriculturalAssistant/
├── agent/                  # 智能体核心
│   ├── supervisor.py       # 意图分类路由调度器
│   ├── knowledge_agent.py  # ReAct Agent: RAG 知识问答
│   ├── general_agent.py    # ReAct Agent: 通用闲聊
│   ├── diagnose.py         # VLM 多模态诊断
│   ├── critic.py           # BM25 事实校验器
│   └── agent_tools/        # 工具集
├── api/                    # FastAPI 路由层
├── auth/                   # JWT + bcrypt 认证
├── config/                 # Pydantic Settings
├── db/                     # SQLAlchemy ORM 模型
├── service/                # 服务层
│   ├── rag_service.py      # RAG 检索管线
│   ├── vector_store_service.py  # ChromaDB 管理
│   ├── cache_service.py    # 语义缓存 + LLM 缓存
│   ├── guard_service.py    # 安全防护
│   └── conversation_service.py  # 会话管理
├── factory/                # 模型工厂
├── prompt/                 # Agent 系统提示词
├── scripts/                # 工具脚本
├── utils/                  # 工具函数
├── data/                   # 运行时数据
│   ├── knowledge/          # 农业知识库源文件
│   └── eval/               # 评估测试集
├── frontend/               # Vue 3 SPA
├── main.py                 # 应用入口
├── pyproject.toml          # 项目元数据
├── docker-compose.yml      # Docker 编排
└── Dockerfile              # 容器镜像
```

---

## 项目亮点

- **反幻觉工程**：BM25 实体匹配做事实校验，零额外 Token 开销，结果可溯源验证
- **多级降级策略**：意图分类模型降级、RAG 检索降级（无结果 → 纯网络搜索）、MySQL 降级（游客模式），每个环节都有 Fallback
- **缓存体系**：语义缓存 + LLM 响应缓存双层缓存，减少重复 API 调用开销
- **安全性设计**：从输入过滤、输出过滤、速率限制到路径安全，面向生产环境的防护
- **工程规范**：Docker Compose 一键部署、Makefile 构建命令、环境变量配置管理



