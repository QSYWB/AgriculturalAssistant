"""农业调度器 + 图片诊断模块"""
import base64, re
from pathlib import Path
from langchain_core.messages import HumanMessage, SystemMessage
from factory.model_factory import ChatModelFactory
from agent.knowledge_agent import invoke_knowledge_agent
from agent.critic import invoke_critic
from utils.logger_handler import app_logger, agent_trace_logger, error_logger
from utils.path_tool import path_tool

MAX_RETRIES = 2

def invoke_agriculture(query: str, feedback: str = "") -> dict:
    agent_trace_logger.info(f"[Agriculture Agent] 开始处理: {query}")
    current_feedback, last_answer = feedback, ""
    for attempt in range(MAX_RETRIES):
        aq = query
        if current_feedback:
            aq = f"{query}\n\n上一轮校验反馈：{current_feedback}\n请根据反馈修正回答。"
        raw = invoke_knowledge_agent(aq)
        validated = invoke_critic(query, raw)
        if "【注意】" not in validated:
            return {"answer": validated, "retry_count": attempt + 1}
        current_feedback, last_answer = validated, validated
    return {"answer": last_answer, "retry_count": MAX_RETRIES}

_diagnose_model = ChatModelFactory(temperature=0.3, streaming=False).create()

def encode_image_to_base64(image_path: str | Path) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def invoke_diagnose(image_data: str, image_format: str = "jpeg", user_description: str = "") -> dict:
    agent_trace_logger.info(f"[Diagnose Agent] 开始图片诊断")
    prompt_path = path_tool.get_prompt_dir() / "diagnose_agent.txt"
    system_prompt = prompt_path.read_text(encoding="utf-8")
    user_text = f"请分析这张作物图片。{user_description}" if user_description else "请分析这张作物图片。"
    content_parts = [{"type": "text", "text": user_text}, {"type": "image_url", "image_url": {"url": f"data:image/{image_format};base64,{image_data}"}}]
    resp = _diagnose_model.invoke([SystemMessage(content=system_prompt), HumanMessage(content=content_parts)])
    diagnosis = resp.content.strip()
    disease_name = _extract_disease_name(diagnosis)
    treatment = ""
    if disease_name and disease_name != "未知":
        try:
            treatment = invoke_knowledge_agent(f"{disease_name}的防治方法")
        except Exception as e:
            error_logger.error(f"诊断后知识检索失败: {e}")
    return {"diagnosis": diagnosis, "disease_name": disease_name, "treatment": treatment}

def _extract_disease_name(diagnosis_text: str) -> str:
    m = re.search(r'【诊断病害】\s*(.+?)(?:\s*（|\s*\(|$)', diagnosis_text)
    return m.group(1).strip() if m else "未知"
