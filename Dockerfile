# ===== Build stage: frontend =====
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# ===== Runtime stage: backend =====
FROM python:3.12-slim
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc && rm -rf /var/lib/apt/lists/*

# 复制后端
COPY pyproject.toml README.md ./
COPY agent/ agent/
COPY api/ api/
COPY auth/ auth/
COPY config/ config/
COPY db/ db/
COPY factory/ factory/
COPY prompt/ prompt/
COPY scripts/ scripts/
COPY service/ service/
COPY utils/ utils/
COPY main.py .

# 复制前端构建产物
COPY --from=frontend-builder /app/frontend/dist frontend/dist

# 安装 Python 依赖
RUN pip install --no-cache-dir -e .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
