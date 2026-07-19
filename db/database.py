import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError

from config.settings import settings

logger = logging.getLogger(__name__)

_engine = None
_SessionLocal = None
Base = declarative_base()


def _get_engine():
    global _engine
    if _engine is None:
        db_url = (
            f"mysql+pymysql://{settings.db_user}:{settings.db_password}"
            f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
            "?charset=utf8mb4"
        )
        _engine = create_engine(db_url, pool_pre_ping=True, pool_size=5, max_overflow=10)
    return _engine


def get_session_local():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_get_engine())
    return _SessionLocal


def get_db():
    """FastAPI 依赖注入 — 创建数据库会话，请求结束后关闭。"""
    db = get_session_local()()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """创建所有数据表。如果 MySQL 不可用，记录警告后继续。"""
    try:
        Base.metadata.create_all(bind=_get_engine())
        logger.info("Database tables created / verified successfully.")
    except OperationalError as e:
        logger.warning(f"Database not available: {e}")
        logger.warning("App will start in guest-only mode. Auth/persistence features require MySQL.")
