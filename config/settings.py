from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from utils.path_tool import path_tool


class Settings(BaseSettings):
    """应用配置，全部从 .env 文件加载"""

    # ===== 通义千问 (阿里云百炼) =====
    dashscope_api_key: Optional[str] = None
    dashscope_base_url: Optional[str] = None
    llm_model: Optional[str] = None
    embedding_model: Optional[str] = None
    tavily_api_key: Optional[str] = None

    # ===== DeepSeek (路由/调度器专用) =====
    deepseek_api_key: Optional[str] = None
    deepseek_base_url: Optional[str] = None
    deepseek_model: Optional[str] = None

    # ===== 本地存储路径 =====
    chroma_collection_name: str = "AgricultureAssistant"
    chroma_persist_dir: str = str(path_tool.get_chroma_db_dir())
    chat_history_dir: str = str(path_tool.get_chat_history_dir())
    upload_dir: str = str(path_tool.get_upload_dir())
    md5_hex_path: str = str(path_tool.get_records_dir() / "processed_files.txt")
    data_dir: str = str(path_tool.get_data_dir())
    allowed_knowledge_types: List[str] = [".txt", ".md", ".pdf"]

    # ===== 文本分割器配置 =====
    chunk_size: int = 512
    chunk_overlap: int = 128
    separators: List[str] = ["\n\n", "\n", "\u3002", ".", " ", ""]
    min_chunk_bytes: int = 5000

    # ===== 日志与通用设置 =====
    log_level: str = "INFO"
    retriever_k: int = 3
    max_context_tokens: int = 4000
    rag_cache_ttl: int = 300
    rag_cache_threshold: float = 0.92
    llm_cache_ttl: int = 3600
    llm_cache_enabled: bool = True

    # ===== 认证与安全 =====
    jwt_secret_key: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24
    rate_limit_per_minute: int = 30
    rate_limit_per_minute_auth: int = 60

    # ===== MySQL 数据库 =====
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "agricultural_assistant"

    model_config = SettingsConfigDict(
        env_file=path_tool.get_base_dir() / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Global singleton
settings = Settings()
