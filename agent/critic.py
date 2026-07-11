"""事实核查器 — 基于 BM25 的精确匹配，替代 LLM 自我校验"""
import re
from service.rag_service import RagService
from utils.logger_handler import app_logger, agent_trace_logger

_rag = RagService()


def _extract_entities(text: str) -> list[str]:
    """从回答中提取可验证的关键实体（数值、农药名、剂量等）"""
    entities = []
    # 带单位的数值：800倍液, 15kg, 30%, 2毫升
    entities.extend(re.findall(r"\d+(?:\.\d+)?\s*(?:倍液|倍|%|[℃°Ck]?[g克升毫升LMml]+)", text))
    # 农药/化学品名：xx灵，xx唑，xx酮，xx脂（2-4字 + 常见后缀）
    entities.extend(re.findall(r"[\u4e00-\u9fff]{2,4}(?:灵|唑|酮|酯|脲|胺|醇|醚|酚|腈|盐|酸|霉素)", text))
    # 剂量/浓度模式：每公顷30克, 每亩15kg
    entities.extend(re.findall(r"每[亩公顷]\s*(?:\w+\s*){0,2}\d+\s*\S*[g克升毫升kg]", text))
    return list(set(entities))


def invoke_critic(query: str, raw_answer: str) -> str:
    """BM25 事实核查：提取实体 → 检索源文档 → 精确匹配验证"""
    agent_trace_logger.info(f"[FactChecker] 开始核查: {len(raw_answer)} 字")

    entities = _extract_entities(raw_answer)
    if not entities:
        agent_trace_logger.info("[FactChecker] 无待验证实体，直接返回")
        return raw_answer

    # 用 query + answer 关键词检索源文档
    docs = _rag.retrieve(query, k=5)
    if not docs:
        agent_trace_logger.info("[FactChecker] 无参考文档，跳过核查")
        return raw_answer

    source_text = "\n".join(d.page_content for d in docs)
    flags = []

    for ent in entities:
        if ent not in source_text:
            flags.append(ent)

    if not flags:
        agent_trace_logger.info(f"[FactChecker] {len(entities)} 项全部验证通过")
        return raw_answer

    # 在回答末尾附加存疑标注
    note = "\n\n【事实核查】以下内容在参考文档中未找到明确依据：\n" + "\n".join(f"  ⚠ {f}" for f in flags)
    agent_trace_logger.info(f"[FactChecker] {len(flags)}/{len(entities)} 项存疑")
    return raw_answer + note
