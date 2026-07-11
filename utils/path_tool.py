from pathlib import Path


class PathTool:
    """项目路径管理工具类"""

    # 项目根目录：utils/ 的上一级（假设 utils/ 在项目根目录下）
    BASE_DIR = Path(__file__).resolve().parent.parent

    @classmethod
    def get_base_dir(cls) -> Path:
        """获取项目根目录"""
        return cls.BASE_DIR

    @classmethod
    def get_data_dir(cls) -> Path:
        """获取数据存储根目录"""
        return cls.BASE_DIR / "data"

    @classmethod
    def get_records_dir(cls) -> Path:
        """获取处理记录目录"""
        return cls.get_data_dir() / "records"

    @classmethod
    def get_chroma_db_dir(cls) -> Path:
        """获取 Chroma 向量库存储目录"""
        return cls.get_data_dir() / "chroma_db"

    @classmethod
    def get_chat_history_dir(cls) -> Path:
        """获取会话历史存储目录"""
        return cls.get_data_dir() / "chat_history"

    @classmethod
    def get_knowledge_dir(cls) -> Path:
        """获取知识库文件上传目录"""
        return cls.get_data_dir() / "knowledge"

    @classmethod
    def get_upload_dir(cls) -> Path:
        """获取上传文件存储目录"""
        return cls.get_data_dir() / "uploads"

    @classmethod
    def get_logs_dir(cls) -> Path:
        """获取日志存储目录"""
        return cls.BASE_DIR / "logs"

    @classmethod
    def get_cache_dir(cls) -> Path:
        "获取缓存存储目录"
        return cls.get_data_dir() / "cache"

    @classmethod
    def get_prompt_dir(cls) -> Path:
        """获取提示词模板目录"""
        return cls.BASE_DIR / "prompt"


# 创建单例对象
path_tool = PathTool()
