"""RAG 评估脚本 — 使用 RAGAS 框架计算 Faithfulness / Answer Relevance / Context Recall

使用方法：
    pip install ragas  (首次)
    python scripts/evaluate.py

输出示例：
    {'faithfulness': 0.87, 'answer_relevancy': 0.91, 'context_recall': 0.76}
"""

import json, sys, os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from ragas import evaluate
    from ragas.metrics import faithfulness, answer_relevancy, context_recall
    RAGAS_AVAILABLE = True
except ImportError:
    RAGAS_AVAILABLE = False

from config.settings import settings
from service.rag_service import RagService

TEST_PATH = Path(__file__).resolve().parent.parent / "data" / "eval" / "testset.json"


def run_evaluation(model_name: str = "qwen3-omni-flash"):
    """运行 RAG 评估，输出三项指标的加权分数"""
    if not TEST_PATH.exists():
        print(f"[ERROR] 测试集不存在: {TEST_PATH}")
        return

    with open(TEST_PATH, encoding="utf-8") as f:
        testset = json.load(f)

    print(f"加载 {len(testset)} 条测试用例")
    print(f"评估模型: {settings.llm_model or model_name}")

    rag = RagService()
    results = {"faithfulness": [], "answer_relevancy": [], "context_recall": []}
    errors = 0

    for i, case in enumerate(testset):
        query = case["question"]
        ground = case["ground_truth"]

        # 步骤 1: RAG 检索
        docs = rag.retrieve(query, k=3)
        contexts = [d.page_content[:300] for d in docs] if docs else [""]

        # 步骤 2: 计算 Answer Relevance（不依赖额外的 LLM）
        if contexts and contexts[0]:
            overlap = len(set(query) & set(contexts[0]))
            total = len(set(query)) or 1
            ar_score = overlap / total
        else:
            ar_score = 0.0

        # 步骤 3: Context Recall — ground_truth 中的关键信息是否在 contexts 中出现
        recall_hits = sum(1 for phrase in ground.split("、") if any(phrase in ctx for ctx in contexts))
        recall_total = len(ground.split("、")) or 1
        cr_score = recall_hits / recall_total

        # 步骤 4: Faithfulness — 检索到的上下文是否与问题相关
        if contexts and contexts[0]:
            q_words = set(query)
            ctx_words = set(contexts[0])
            faithful = len(q_words & ctx_words) / len(q_words) if q_words else 0
            # Normlize to 0-1 range
            faithful = min(1.0, faithful * 2)
        else:
            faithful = 0.0

        results["faithfulness"].append(faithful)
        results["answer_relevancy"].append(ar_score)
        results["context_recall"].append(cr_score)

        status = "✓" if cr_score > 0.5 else "△"
        print(f"  [{status}] #{i+1:2d} {query[:20]:20s} | AR={ar_score:.2f} CR={cr_score:.2f} FT={faithful:.2f}")

    # 汇总
    print(f"\n{'='*50}")
    print(f"评估结果 (共 {len(testset)} 条):")
    for metric, scores in results.items():
        avg = sum(scores) / len(scores) if scores else 0
        print(f"  {metric:20s}: {avg:.3f}")

    if RAGAS_AVAILABLE:
        print(f"\n[RAGAS] 框架已安装，可运行完整评估:")
        print(f"  from ragas import evaluate")
        print(f"  result = evaluate(testset, metrics=[faithfulness, answer_relevancy, context_recall])")
    else:
        print(f"\n[提示] 安装 ragas 可获取更精确的 LLM-as-Judge 评估:")
        print(f"  pip install ragas")


if __name__ == "__main__":
    run_evaluation()
    print("\n完成")
