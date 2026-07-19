"""向量数据库服务"""
import os, logging
from pathlib import Path
from langchain_chroma.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config.settings import settings
from factory.model_factory import embedding_model
from utils.logger_handler import app_logger
from utils.path_tool import path_tool
from utils.file_handler import get_file_md5_hex, listdir_with_allowed_types, pdf_loader, txt_loader

logger = logging.getLogger(__name__)

class VectorStoreService:
    def __init__(self):
        self.vector_store = Chroma(
            collection_name=settings.chroma_collection_name,
            persist_directory=settings.chroma_persist_dir,
            embedding_function=embedding_model)
        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            separators=settings.separators
        )
        self.min_chunk_bytes = settings.min_chunk_bytes

    def get_retrieve(self, k: int = 15):
        return self.vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={"k": k, "lambda_mult": 0.7}
        )

    def _check_md5_hex(self, md5: str) -> bool:
        md5_path = Path(settings.md5_hex_path)
        md5_path.parent.mkdir(parents=True, exist_ok=True)
        if not md5_path.exists():
            md5_path.write_text("", encoding="utf-8"); return False
        try:
            with open(md5_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip() == md5: return True
        except (UnicodeDecodeError, OSError):
            app_logger.warning(f"MD5 文件编码异常，重新创建: {md5_path}")
            md5_path.write_text("", encoding="utf-8")
        return False

    def _save_md5_hex(self, md5: str) -> None:
        with open(settings.md5_hex_path, "a", encoding="utf-8") as f:
            f.write(md5 + "\n")

    @staticmethod
    def _get_file_documents(file_path: str) -> list[Document]:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf": return pdf_loader(file_path)
        if ext in (".txt", ".md"): return txt_loader(file_path)
        logger.warning(f"不支持的文件类型: {file_path}")
        return []

    @staticmethod
    def _calculate_total_bytes(documents: list[Document]) -> int:
        return sum(len(doc.page_content.encode("utf-8")) for doc in documents)

    def load_document(self) -> None:
        data_dir = str(path_tool.get_knowledge_dir())
        file_paths = listdir_with_allowed_types(data_dir, tuple(settings.allowed_knowledge_types))
        if not file_paths: return
        for file_path in file_paths:
            md5_hex = get_file_md5_hex(file_path)
            if self._check_md5_hex(md5_hex):
                app_logger.info(f"文件已处理过，跳过: {file_path}"); continue
            try:
                documents = self._get_file_documents(file_path)
            except Exception as e:
                app_logger.error(f"文件加载失败: {file_path}, {e}", exc_info=True); continue
            if not documents:
                app_logger.warning(f"文件无内容，跳过: {file_path}"); continue
            total_bytes = self._calculate_total_bytes(documents)
            sd = documents if total_bytes < self.min_chunk_bytes else self.spliter.split_documents(documents)
            app_logger.info(f"{'直接存储' if total_bytes < self.min_chunk_bytes else '分割'}，共 {len(sd)} 片段: {file_path}")
            if not sd: continue
            try:
                self.vector_store.add_documents(sd)
                self._save_md5_hex(md5_hex)
                app_logger.info(f"入库成功: {file_path}")
            except Exception as e:
                app_logger.error(f"入库失败: {file_path}, {e}", exc_info=True)

    def list_knowledge_files(self) -> list[dict]:
        know_dir = path_tool.get_knowledge_dir()
        if not know_dir.exists(): return []
        r = []
        for f in sorted(know_dir.iterdir(), key=lambda p: p.name):
            if f.suffix.lower() in settings.allowed_knowledge_types:
                r.append({"filename": f.name, "size": f.stat().st_size, "modified_at": f.stat().st_mtime})
        return r

    def delete_knowledge_file(self, filename: str) -> bool:
        know_dir = path_tool.get_knowledge_dir()
        fpath = know_dir / filename
        if not fpath.exists() or fpath.suffix.lower() not in settings.allowed_knowledge_types: return False
        fpath.unlink(); return True

    def clear_processed_records(self) -> None:
        Path(settings.md5_hex_path).write_text("", encoding="utf-8")

    def reload_all(self) -> int:
        self.clear_processed_records(); self.load_document()
        return self.vector_store._collection.count()
