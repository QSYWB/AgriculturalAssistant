"""Router Supervisor — 替代 LangGraph 调度器，节省推理开销"""
import json
import asyncio
from langchain_core.messages import HumanMessage, SystemMessage
from factory.model_factory import DeepSeekChatModelFactory, chat_model as fallback_chat_model
from agent.diagnose import invoke_agriculture
from agent.general_agent import invoke_general_agent
from utils.logger_handler import app_logger, agent_trace_logger
from utils.path_tool import path_tool
from service.cache_service import llm_cache

# 路由调度器专用 — 优先使用 DeepSeek 模型做意图分类，配置不完整时回退到原 chat_model
try:
    _routing_model = DeepSeekChatModelFactory(temperature=0.3, streaming=False).create()
    # 用一次简单调用来验证配置是否有效（model/api_key/base_url 是否齐全）
    app_logger.info(f"[Router] 使用 DeepSeek 模型: {_routing_model.model}")
except Exception as e:
    app_logger.warning(f"[Router] DeepSeek 配置不可用，回退到默认模型: {e}")
    _routing_model = fallback_chat_model

async def _classify_intent(query: str, history_summary: str = "",
                           last_turn_result: str = "", user_location: str = "") -> dict:
    """调用 LLM 输出结构化 JSON 意图分类"""
    prompt_path = path_tool.get_prompt_dir() / "supervisor_agent.txt"
    system_prompt = prompt_path.read_text(encoding="utf-8").format(
        user_query=query, last_turn_result=last_turn_result,
        history_summary=history_summary, user_location=user_location,
    )
    try:
        resp = await _routing_model.ainvoke(
            [SystemMessage(content=system_prompt),
             HumanMessage(content=f"请分析用户问题：{query}")],
            response_format={"type": "json_object"},
        )
        result = json.loads(resp.content.strip())
        return {
            "intent": result.get("intent", "general"),
            "confidence": float(result.get("confidence", 0.5)),
        }
    except Exception as e:
        app_logger.warning(f"[Router] intent classify failed: {e}")
        return {"intent": "general", "confidence": 0.5}


async def invoke_supervisor(query: str, history_summary: str = "",
                            last_turn_result: str = "", user_location: str = "") -> str:
    """Router 入口：缓存 → 分类 → 路由 → 分发"""
    ctx = f"{history_summary}|{last_turn_result}"
    cached = llm_cache.get(query, ctx)
    if cached:
        return cached

    result = await _classify_intent(query, history_summary, last_turn_result, user_location)
    intent, confidence = result["intent"], result["confidence"]
    agent_trace_logger.info(f"[Router] intent={intent}, confidence={confidence:.2f}")

    if confidence < 0.4:
        answer = f"您的问题「{query}」我暂时无法确定领域。请补充更多信息。"
    elif intent == "agriculture":
        answer = await asyncio.to_thread(invoke_agriculture, query)
    else:
        answer = await asyncio.to_thread(invoke_general_agent, query, user_location)

    llm_cache.set(query, answer, ctx)
    return answer
