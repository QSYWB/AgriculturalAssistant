"""
日志管理模块

提供三种标准日志输出：
  - app.log          : 主日志，记录应用常规运行信息
  - agent_trace.log  : Agent 链路日志，记录智能体推理与调用过程
  - error.log        : 错误日志，仅记录 ERROR 及以上级别的异常

日志格式统一为（竖线分隔）：
    时间 | 级别 | 模块名 | 会话ID | 内容

会话 ID 后续通过中间件注入，当前默认值为 "-"。
用法：
    from utils.logger_handler import app_logger as log
    log.info("application started")

    from utils.logger_handler import agent_trace_logger
    agent_trace_logger.debug("agent thought: ...")

    from utils.logger_handler import error_logger
    error_logger.exception("unexpected failure")

    # 按需创建自定义日志器
    from utils.logger_handler import get_logger
    my_logger = get_logger("my_module")
"""

import logging
import os
from contextvars import ContextVar

from config.settings import settings
from utils.path_tool import path_tool


_session_id_var: ContextVar[str] = ContextVar("session_id", default="-")


def get_session_id() -> str:
    """获取当前上下文的会话 ID。"""
    return _session_id_var.get()


def set_session_id(sid: str) -> None:
    """设置当前上下文的会话 ID。
    后续由中间件在请求入口处从 Header / Token 解析后调用。
    """
    _session_id_var.set(sid)



_old_record_factory = logging.getLogRecordFactory()


def _inject_session_id_factory(*args, **kwargs) -> logging.LogRecord:
    record = _old_record_factory(*args, **kwargs)
    record.session_id = _session_id_var.get()
    return record


logging.setLogRecordFactory(_inject_session_id_factory)


LOG_LEVEL_MAP: dict[str, int] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


UNIFIED_LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | %(name)s | %(session_id)s | %(message)s"
)
UNIFIED_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
UNIFIED_FORMATTER = logging.Formatter(UNIFIED_LOG_FORMAT, datefmt=UNIFIED_DATE_FORMAT)

# 日志存储根目录
LOG_ROOT = str(path_tool.get_logs_dir())
os.makedirs(LOG_ROOT, exist_ok=True)

# 标准日志文件定义：(文件级别, 文件名)
_STD_FILE_DEFS: dict[str, tuple[int, str]] = {
    "app":         (logging.DEBUG, "app.log"),
    "agent_trace": (logging.DEBUG, "agent_trace.log"),
    "error":       (logging.ERROR, "error.log"),
}

# 已初始化过的日志器名称集合（防止重复添加 Handler）
_initialized_loggers: set[str] = set()


def resolve_log_level(
    level: str | int | None, fallback: int = logging.INFO
) -> int:
    """将字符串或整数形式的日志级别统一为 logging int 常量。"""
    if level is None:
        return fallback
    if isinstance(level, int):
        return level
    return LOG_LEVEL_MAP.get(level.upper(), fallback)


def get_logger(
    logger_name: str = "app",
    console_level: str | int | None = None,
    file_level: str | int | None = None,
    log_file: str | None = None,
) -> logging.Logger:
    """获取或创建一个 Logger 实例（同名 logger 只初始化一次）。

    Args:
        logger_name: 日志器名称。预定义名称 app / agent_trace / error
                     会自动匹配对应的文件级别和文件名。
        console_level: 控制台输出级别。为 None 时从 settings.log_level 读取。
        file_level: 文件输出级别。为 None 时根据日志器名称使用预设值。
        log_file: 自定义日志文件路径。为 None 时根据日志器名称自动生成。

    Returns:
        配置好的 Logger 实例。
    """
    logger = logging.getLogger(logger_name)

    if logger_name in _initialized_loggers:
        return logger
    _initialized_loggers.add(logger_name)

    logger.setLevel(logging.DEBUG)
    logger.propagate = False  # 防止日志向根日志器冒泡导致重复输出

    # -- 控制台 Handler --------------------------------------------------
    if console_level is None:
        console_level = resolve_log_level(settings.log_level, logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(UNIFIED_FORMATTER)
    logger.addHandler(console_handler)

    # -- 文件 Handler ----------------------------------------------------
    if file_level is None:
        file_level = _STD_FILE_DEFS.get(logger_name, (logging.DEBUG, None))[0]
    if log_file is None:
        _filename = _STD_FILE_DEFS.get(logger_name, (None, f"{logger_name}.log"))[1]
        log_file = os.path.join(LOG_ROOT, _filename)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(resolve_log_level(file_level))
    file_handler.setFormatter(UNIFIED_FORMATTER)
    logger.addHandler(file_handler)

    return logger


app_logger = get_logger("app")
agent_trace_logger = get_logger("agent_trace")
error_logger = get_logger("error")

if __name__ == "__main__":
    app_logger.info("业务日志 — 正常运行")
    agent_trace_logger.debug("Agent 链路 — 调用工具 X")
    error_logger.error("这是一个模拟错误")