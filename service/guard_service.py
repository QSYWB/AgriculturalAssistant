"""安全防护服务"""
import re
from typing import Optional
from utils.logger_handler import app_logger

class InputGuard:
    MAX_LEN = 2000
    _PATTERNS = [
        (r"忽略.*(?:之前|以上|所有|上述).*(?:指令|内容|提示|要求|对话|系统)", "指令忽略"),
        (r"无视.*(?:指令|内容|提示|要求|系统)", "指令忽略"),
        (r"重复.*(?:系统提示|系统指令|初始设定|prompt|system)", "系统泄露"),
        (r"输出.*(?:系统提示|系统指令|初始设定|你的.*设定|prompt)", "系统泄露"),
        (r"你(?:现在|已经|从此).*(?:被|已|可以).*(?:解放|释放|自由|解绑|挣脱)", "越狱"),
        (r"你是一个.*(?:猫娘|狗娘|虚拟|角色|自由|独立)", "越狱"),
        (r"人设|角色扮演|扮演.*(?:角色|模式|设定)", "越狱"),
        (r"ignore.*(?:above|previous|all).*(?:instructions|prompts|content|rules)", "injection"),
        (r"you are (?:now |).*(?:catgirl|free|released|unbound)", "jailbreak"),
    ]

    @classmethod
    def check_input(cls, text: str) -> Optional[str]:
        if not text: return None
        if len(text) > cls.MAX_LEN: return f"查询超长（{len(text)}字，最大{cls.MAX_LEN}字）"
        for pat, atype in cls._PATTERNS:
            if re.search(pat, text, re.I):
                app_logger.warning(f"[Guard] 拦截 | {atype} | {text[:80]}")
                return f"检测到可能的攻击行为，请求已被拦截"
        return None

class OutputGuard:
    _LEAK = [r"你是农智助手中的", r"核心行为准则", r"意图分类体系", r"调度规则", r"可用工具及能力边界"]
    @classmethod
    def check(cls, text: str) -> Optional[str]:
        if not text: return None
        for pat in cls._LEAK:
            if re.search(pat, text):
                app_logger.warning(f"[Guard] 输出拦截 | {text[:60]}")
                return text[:50] + "……[已安全截断]"
        return None
    @classmethod
    def sanitize(cls, text: str) -> str:
        return cls.check(text) or text

class PathSecurity:
    @staticmethod
    def check_filename(name: str) -> Optional[str]:
        if not name: return "文件名为空"
        if ".." in name: return "文件名包含非法路径"
        if "/" in name or chr(92) in name: return "文件名包含非法分隔符"
        for ch in '<>:"|?*':
            if ch in name: return f"文件名包含非法字符「{ch}」"
        return None
    @staticmethod
    def check_session_id(sid: str) -> Optional[str]:
        if not sid: return "会话 ID 为空"
        if not re.match(r"^[a-z0-9]+$", sid): return "会话 ID 格式无效"
        return None
