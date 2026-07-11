"""模型工厂"""
from abc import ABC, abstractmethod
from typing import Optional
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from config.settings import settings

class ModelFactory(ABC):
    @abstractmethod
    def create(self) -> Optional[Embeddings | BaseChatModel]:
        pass

class ChatModelFactory(ModelFactory):
    def __init__(self, temperature: float = 0.7, streaming: bool = True):
        self.temperature = temperature
        self.streaming = streaming
    def create(self) -> BaseChatModel:
        return ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.dashscope_api_key,
            base_url=settings.dashscope_base_url,
            temperature=self.temperature,
            streaming=self.streaming,
        )

class EmbeddingModelFactory(ModelFactory):
    def create(self) -> Embeddings:
        return OpenAIEmbeddings(
            model=settings.embedding_model, api_key=settings.dashscope_api_key,
            base_url=settings.dashscope_base_url,
            check_embedding_ctx_length=False, chunk_size=10,
        )

class DeepSeekChatModelFactory(ModelFactory):
    """Router/Supervisor专用 — 使用 DeepSeek 模型进行意图分类"""
    def __init__(self, temperature: float = 0.3, streaming: bool = False):
        self.temperature = temperature
        self.streaming = streaming
    def create(self) -> BaseChatModel:
        return ChatOpenAI(
            model=settings.deepseek_model,
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            temperature=self.temperature,
            streaming=self.streaming,
        )

chat_model = ChatModelFactory().create()
embedding_model = EmbeddingModelFactory().create()
