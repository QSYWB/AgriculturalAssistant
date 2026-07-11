.PHONY: install dev build frontend clean docker-up docker-down

install:                     ## 安装后端依赖
	pip install -e .

dev:                         ## 启动后端开发服务器
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

frontend:                    ## 启动前端开发服务器
	cd frontend && npm run dev

build:                       ## 构建前端
	cd frontend && npm run build

test:                        ## 运行测试
	pytest -v

evaluate:                    ## 运行评估
	python scripts/evaluate.py

docker-up:                   ## Docker 启动
	docker compose up -d

docker-down:                 ## Docker 停止
	docker compose down

clean:                       ## 清理构建产物
	rm -rf frontend/dist
	rm -rf .venv
	rm -rf .pytest_cache
	rm -rf __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

help:                        ## 显示帮助
	@grep -E '^\S+:\s+.*##' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
