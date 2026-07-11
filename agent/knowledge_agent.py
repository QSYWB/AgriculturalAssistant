"""知识助手"""
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from agent.agent_tools.tools import web_search, knowledge_cr, source_cite, execute_web_search
from factory.model_factory import chat_model
from service.rag_service import RagService
from utils.logger_handler import agent_trace_logger
from utils.path_tool import path_tool

_rag_service = RagService()
knowledge_prompt = path_tool.get_prompt_dir() / "knowledge_agent.txt"
system_prompt = knowledge_prompt.read_text(encoding="utf-8")
knowledge_agent = create_agent(model=chat_model, system_prompt=system_prompt, tools=[web_search, knowledge_cr, source_cite])

def invoke_knowledge_agent(query: str) -> str:
    agent_trace_logger.info(f"[Knowledge Agent] 开始处理: {query}")
    rag_context = _rag_service.retrieve_as_context(query)
    # 预搜索：直接用用户原文查询，不经 LLM 改写
    search_context = execute_web_search(query)
    parts = ["【本地知识库检索结果】\n" + (rag_context or "未找到相关信息。")]
    if search_context:
        parts.append(f"【网络搜索结果】\n{search_context}")
    parts.append("请优先使用本地知识库结果，并参考网络搜索结果回答。如需要可自行调用 web_search 工具补充。")
    parts.append(f"——\n【用户问题】\n{query}")
    result = knowledge_agent.invoke({"messages": [HumanMessage(content="\n\n".join(parts))]})
    answer = result["messages"][-1].content
    agent_trace_logger.info(f"[Knowledge Agent] 回答完成, {len(answer)} 字")
    return answer
