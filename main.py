import uuid
from fastapi import Request, FastAPI
from utils.logger_handler import set_session_id
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded

from api import knowledge, supervisor, diagnose
from api import user as user_api
from api.errors import register_error_handlers
from auth import auth_routes
from db.database import init_db

app = FastAPI(
    title="农智助手",
    description="农业知识问答智能助手 | 基于 LangGraph 多智能体架构",
    version="0.3.0",
)

import asyncio
from concurrent.futures import ThreadPoolExecutor


@app.on_event("startup")
async def setup_thread_pool():
    """Increase thread pool for concurrent requests."""
    loop = asyncio.get_running_loop()
    loop.set_default_executor(ThreadPoolExecutor(max_workers=20))
    init_db()


# ---- Rate limiting (slowapi) -----------------------------------------------
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["30/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ---- Middleware -------------------------------------------------------------
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(SlowAPIMiddleware)

# CORS — restrict origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- Routers (public before protected) --------------------------------------
app.include_router(auth_routes.router)       # /api/auth/*
app.include_router(knowledge.router)         # /api/chat/knowledge
app.include_router(supervisor.router)        # /api/chat/supervisor
app.include_router(diagnose.router)
app.include_router(user_api.router)          # /api/diagnose


# ---- Error handlers ---------------------------------------------------------
register_error_handlers(app)


# ---- Middleware: inject request ID / session ID -----------------------------
@app.middleware("http")
async def inject_request_id(request: Request, call_next):
    request_id = uuid.uuid4().hex[:8]
    set_session_id(request_id)
    response = await call_next(request)
    return response


@app.get("/")
async def root():
    return {
        "message": "农智助手服务已启动",
        "version": "0.3.0",
        "endpoints": {
            "auth_register": "/api/auth/register (POST)",
            "auth_login": "/api/auth/login (POST)",
            "auth_me": "/api/auth/me (GET)",
            "supervisor": "/api/chat/supervisor (POST)",
            "diagnose": "/api/diagnose (POST - multipart)",
            "knowledge": "/api/chat/knowledge (POST)",
        },
    }


# ---- Mount frontend SPA -----------------------------------------------------
_frontend_path = Path(__file__).parent / "frontend"
if _frontend_path.exists():
    dist = _frontend_path / "dist"
    if dist.exists():
        app.mount("/chat", StaticFiles(directory=str(dist), html=True), name="frontend")

