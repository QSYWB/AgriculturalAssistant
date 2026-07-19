"""测试重排效果：对比重排前（原始向量）与重排后（交叉编码器）的结果。"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from service.vector_store_service import VectorStoreService
from factory.model_factory import embedding_model


def get_raw_results(query: str, top_k: int = 10) -> list[dict]:
    """直接从向量库检索，不做任何重排。"""
    from langchain_chroma.vectorstores import Chroma
    from config.settings import settings

    store = Chroma(
        collection_name=settings.chroma_collection_name,
        persist_directory=settings.chroma_persist_dir,
        embedding_function=embedding_model,
    )
    results = store.similarity_search_with_relevance_scores(query, k=top_k)
    out = []
    for doc, score in results:
        out.append({
            "score": round(score, 4),
            "source": doc.metadata.get("source", "unknown"),
            "preview": doc.page_content[:120].replace(chr(10), " "),
        })
    return out


def get_reranked_results(query: str, top_k: int = 10) -> list[dict]:
    """使用 DashScope gte-rerank 交叉编码器重排。"""
    from service.rag_service import _RERANK_MODEL

    vs = VectorStoreService()
    raw_docs = vs.get_retrieve(k=top_k).invoke(query)
    if not raw_docs:
        return []

    import dashscope
    from config.settings import settings
    dashscope.api_key = settings.dashscope_api_key
    resp = dashscope.TextReRank.call(
        model=_RERANK_MODEL,
        query=query,
        documents=[d.page_content for d in raw_docs],
        top_n=top_k,
        return_documents=False,
    )
    if resp.status_code != 200:
        print(f"  [ERROR] Rerank API failed: {resp.status_code} {getattr(resp, 'message', '')}")
        return []

    index_to_doc = {i: raw_docs[i] for i in range(len(raw_docs))}
    out = []
    for item in resp.output.results:
        doc = index_to_doc.get(item.index)
        if not doc:
            continue
        out.append({
            "score": round(item.relevance_score, 4),
            "source": doc.metadata.get("source", "unknown"),
            "preview": doc.page_content[:120].replace(chr(10), " "),
        })
    return out


def print_comparison(query: str, top_k: int = 10):
    sep = "-" * 78
    print(f"\n[Query] {query}\n{sep}")

    print("\n[Before] -- 纯向量余弦相似度 (cosine):")
    raw = get_raw_results(query, top_k)
    if not raw:
        print("  (no results)")
    for i, r in enumerate(raw, 1):
        print(f"  #{i:2d}  score={r['score']:.4f}  [{r['source']}]  {r['preview']}")

    print(f"\n[After]  -- DashScope rerank (cross-encoder):")
    reranked = get_reranked_results(query, top_k)
    if not reranked:
        print("  (no results)")
    for i, r in enumerate(reranked, 1):
        print(f"  #{i:2d}  score={r['score']:.4f}  [{r['source']}]  {r['preview']}")

    if raw and reranked:
        raw_previews = {r['preview'][:60]: i for i, r in enumerate(raw)}
        print(f"\n  Rank changes (old -> new):")
        for new_rank, r in enumerate(reranked, 1):
            key = r['preview'][:60]
            old_rank = raw_previews.get(key, -1) + 1
            delta = old_rank - new_rank
            if delta > 0:
                arrow = "UP"
            elif delta < 0:
                arrow = "DOWN"
            else:
                arrow = "SAME"
            print(f"    #{old_rank:2d} -> #{new_rank:2d}  ({arrow}, shift {abs(delta):2d})")

    print(sep)


if __name__ == "__main__":
    test_queries = [
        "水稻稻瘟病怎么防治",
        "西红柿种植技术",
        "化肥使用注意事项",
    ]
    for q in test_queries:
        print_comparison(q, top_k=8)
        print()
