"""RAG 检索服务（语义缓存 + 交叉编码器重排序）"""
import re
from typing import List, Optional
from langchain_core.documents import Document
from langchain_core.messages import SystemMessage, HumanMessage
from service.vector_store_service import VectorStoreService
from config.settings import settings
from factory.model_factory import embedding_model, chat_model
from utils.logger_handler import app_logger
from utils.logger_handler import error_logger


# ---- Query Rewriting Prompt ----
_REWRITE_PROMPT = """你是一个查询改写器。将用户的输入改写成更适合知识库检索的查询语句。

规则：
- 提取核心关键词和意图，去掉"帮我"、"搜索一下"、"请问"等口语化前缀
- 保留时间信息（年份、月份等），使用书面语
- 如果输入已经是一个简洁的查询，直接原样输出
- 绝对不要对输入内容做出回应、评价或提问
- 只输出改写后的文本，不要输出任何其他内容

输入：{query}

输出："""

# ---- Reranker: DashScope gte-rerank ----
_RERANK_MODEL = "qwen3-rerank"

def _rerank(query: str, docs: List[Document], top_n: int) -> List[Document]:
    """使用 DashScope TextReRank 交叉编码器对文档重排序，失败时降级返回原始顺序。"""
    if not docs:
        return []
    try:
        import dashscope
        dashscope.api_key = settings.dashscope_api_key
        resp = dashscope.TextReRank.call(
            model=_RERANK_MODEL,
            query=query,
            documents=[d.page_content for d in docs],
            top_n=top_n,
            return_documents=False,
        )
    except Exception as e:
        error_logger.error(f"DashScope Rerank 调用异常: {e}")
        return docs[:top_n]
    if resp.status_code != 200:
        app_logger.warning(f"DashScope Rerank 返回非 200: {resp.status_code} {getattr(resp, 'message', '')}")
        return docs[:top_n]
    ranked: List[Document] = []
    for item in resp.output.results:
        idx = item.index
        if idx < len(docs):
            ranked.append(docs[idx])
    return ranked[:top_n] if ranked else docs[:top_n]

_semantic_cache = None
def _get_cache():
    global _semantic_cache
    if _semantic_cache is None:
        from service.cache_service import semantic_cache
        _semantic_cache = semantic_cache
    return _semantic_cache

class RagService:
    INITIAL_K, FINAL_K = 30, 3
    def __init__(self):
        self.vector_store = VectorStoreService()
        self.retriever = self.vector_store.get_retrieve(k=RagService.INITIAL_K)

    @staticmethod
    def _rewrite_query(query: str) -> str:
        """在RAG检索前，用大模型将用户口语化问题改写为更精准的书面检索表述"""
        try:
            resp = chat_model.invoke([
                SystemMessage(content="你是一个查询改写助手，负责将用户的问题改写成更适合知识库检索的书面表述。"),
                HumanMessage(content=_REWRITE_PROMPT.format(query=query)),
            ])
            rewritten = resp.content.strip()
            # 防护：改写结果必须是简洁查询，不能是对话回应（如"请提供..."）
            _is_valid = (
                rewritten
                and len(rewritten) > 5
                and len(rewritten) < len(query) * 2 + 20
                and not rewritten.startswith("请")
                and not any(rewritten.startswith(w) for w in ["您可以", "建议", "你好", "您好"])
            )
            if _is_valid:
                app_logger.debug(f"[QueryRewrite] 原句: {query[:60]} -> 改写: {rewritten[:60]}")
                return rewritten
            app_logger.debug(f"[QueryRewrite] 改写无效，回退原句: {rewritten[:80] if rewritten else '空'}")
        except Exception as e:
            error_logger.warning(f"[QueryRewrite] 改写失败，使用原句: {e}")
        return query

    def retrieve(self, query: str, k: int = FINAL_K) -> List[Document]:
        k = k or RagService.FINAL_K
        rewritten_query = self._rewrite_query(query)
        cache = _get_cache()
        qe = embedding_model.embed_query(rewritten_query)
        cached = cache.get(qe)
        if cached is not None: return cached[:k]
        raw = self.retriever.invoke(rewritten_query)
        if not raw: return []
        result = _rerank(rewritten_query, raw[:RagService.INITIAL_K], k)
        cache.set(qe, result)
        return result

    def retrieve_as_context(self, query: str, top_k: int = 5) -> str:
        docs = self.retrieve(query, top_k)
        if not docs: return ""
        return "\n\n".join(f"【参考资料{i+1}】（来源：{d.metadata.get('source', '未知')}）\n{d.page_content}" for i, d in enumerate(docs))

