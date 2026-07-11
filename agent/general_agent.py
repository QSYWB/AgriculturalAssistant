"""通用助手"""
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from agent.agent_tools.tools import web_search, execute_web_search
from factory.model_factory import chat_model
from utils.logger_handler import agent_trace_logger
from utils.path_tool import path_tool

prompt_path = path_tool.get_prompt_dir() / "general_agent.txt"
system_prompt = prompt_path.read_text(encoding="utf-8")
general_agent = create_agent(model=chat_model, system_prompt=system_prompt, tools=[web_search])

def invoke_general_agent(query: str, user_location: str = "") -> str:
    agent_trace_logger.info(f"[General Agent] 开始处理: {query}")
    # 预搜索：直接用用户原文查询，不经 LLM 改写
    search_context = execute_web_search(query)
    augmented_input = (
        f"用户问题：{query}\n\n"
        f"用户当前位置：{user_location if user_location else '未知'}\n\n"
        f"【网络搜索结果】\n{search_context if search_context else '未获取到相关网络信息。'}"
    )
    result = general_agent.invoke({"messages": [HumanMessage(content=augmented_input)]})
    answer = result["messages"][-1].content
    agent_trace_logger.info(f"[General Agent] 回答完成, {len(answer)} 字")
    return answer
