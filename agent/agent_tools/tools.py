"""Agent 工具集"""
import re
from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from config.settings import settings
from factory.model_factory import embedding_model
from utils.logger_handler import app_logger


def execute_web_search(query: str, max_results: int = 3) -> str:
    """用用户原文直接搜索，不经 LLM 改写翻译。返回格式化后的文本，失败返回空字符串。"""
    app_logger.info(f"[Web Search Pre-fetch] query={query}")
    try:
        Searcher = TavilySearchResults(tavily_api_key=settings.tavily_api_key, max_results=max_results)
        results = Searcher.invoke(query)
        if not results:
            return ""
        parts = [
            f"【网络搜索结果{i+1}】\n{r.get('content','') if isinstance(r,dict) else str(r)}"
            for i, r in enumerate(results)
        ]
        return "\n\n".join(parts)
    except Exception as e:
        app_logger.error(f"网络搜索失败: {e}")
        return ""


@tool(parse_docstring=True)
def web_search(query: str, max_results: int = 3) -> list:
    """通过网络搜索引擎（Tavily）获取与 query 相关的实时农业信息。

    核心能力：通过 Tavily 搜索引擎获取网络上的实时农业信息，包括最新农业政策、
    市场行情、天气预报、新闻报道、学术文章等时效性较强的内容。
    使用场景：
        1. 本地知识库检索结果不足以回答问题时，调用此工具作为补充；
        2. 需要获取最新农业政策、市场价格、天气预报等实时信息时；
        3. 处理非农业类通用问题时（由 General Agent 调用）。

    Args:
        query: 搜索关键词，建议使用完整的问题句子或关键短语。
        max_results: 返回结果数量，默认为 3。

    Returns:
        网络搜索结果列表，每个元素为包含标题、内容和URL的字典。
        搜索失败时返回空列表。
    """
    app_logger.info(f"[Web Search] query={query}, max_results={max_results}")
    try:
        tool = TavilySearchResults(tavily_api_key=settings.tavily_api_key, max_results=max_results)
        result = tool.invoke(query)
        return result if result else []
    except Exception as e:
        app_logger.error(f"网络搜索失败: {e}")
        return []


@tool(parse_docstring=True)
def knowledge_cr(query: str, documents_text: str) -> str:
    """对检索到的文档做二次相关性过滤（去噪），去除语义不相关的内容。

    使用语义嵌入模型计算 query 与每个文档片段的相关性分数，
    只保留相关性较高的内容，过滤掉低质量的噪声信息。

    Args:
        query: 用户的原始问题或检索关键词，用于计算相关性。
        documents_text: 待过滤的文档文本，多段内容应包含【参考资料N】标记格式。

    Returns:
        过滤后的文档文本，只保留与 query 语义高度相关的内容。
    """
    app_logger.info(f"[Knowledge CR] query={query}, text_length={len(documents_text)}")
    if not documents_text.strip():
        return ""

    sections = re.split(r"(?=【参考资料\d+】)", documents_text)
    sections = [s.strip() for s in sections if s.strip()]
    if not sections:
        return documents_text

    try:
        query_embedding = embedding_model.embed_query(query)
        scored_sections = []
        for section in sections:
            content = re.sub(r"^【参考资料\d+】.*?\n", "", section).strip()
            if not content:
                scored_sections.append((0.0, section))
                continue
            content_embedding = embedding_model.embed_query(content[:500])
            score = sum(a*b for a,b in zip(query_embedding, content_embedding))
            na = sum(a*a for a in query_embedding) ** 0.5
            nb = sum(b*b for b in content_embedding) ** 0.5
            score = score / (na * nb) if na and nb else 0.0
            scored_sections.append((score, section))

        threshold = 0.3
        filtered = [sec for score, sec in scored_sections if score >= threshold]
        if not filtered:
            scored_sections.sort(key=lambda x: x[0], reverse=True)
            filtered = [scored_sections[0][1]]

        return "\n\n".join(filtered)
    except Exception as e:
        app_logger.error(f"Knowledge CR 处理失败: {e}")
        return documents_text


@tool(parse_docstring=True)
def source_cite(answer: str, sources_text: str) -> str:
    """给回答自动标注引用来源编号。

    在回答文本末尾附上引用来源列表，标注【N】格式的引用编号，便于用户溯源。

    Args:
        answer: 需要标注引用的回答文本。
        sources_text: 引用来源信息文本，通常包含【参考资料N】标记格式的输出。

    Returns:
        带引用来源标注的回答文本。
    """
    app_logger.info("[Source Cite] 开始标注引用来源")
    if not sources_text.strip():
        return answer

    source_refs = re.findall(r"【参考资料\d+】[^】]*】\n([^【]*)", sources_text)
    if not source_refs:
        return answer + "\n\n引用来源：\n" + sources_text

    source_lines = []
    for i, ref_text in enumerate(source_refs, 1):
        content_preview = ref_text.strip()[:100]
        source_lines.append(f"【{i}】{content_preview}")

    annotation = "\n\n引用来源：\n" + "\n".join(source_lines)
    return answer + annotation
