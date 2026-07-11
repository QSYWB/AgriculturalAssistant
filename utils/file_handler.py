"""
文件处理工具模块

从另一个项目 (Rag Agent实战) 复用的标准工具：
  - pdf_loader / txt_loader   : 文档加载
  - get_file_md5_hex          : 文件 MD5 计算（用于去重）
  - listdir_with_allowed_types: 按扩展名过滤扫描目录
"""

import hashlib
import logging
import os
from typing import List, Optional

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


def get_file_md5_hex(file_path: str) -> str:
    """计算文件的 MD5 哈希值（十六进制）。"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def listdir_with_allowed_types(
    dir_path: str,
    allowed_types: Optional[tuple[str, ...]] = None,
) -> List[str]:
    """扫描目录，返回所有符合 allowed_types 扩展名的文件完整路径。

    Args:
        dir_path: 目标目录路径。
        allowed_types: 允许的扩展名元组，例如 (".txt", ".pdf")。
                       为 None 时不限制。

    Returns:
        符合条件的文件路径列表（按文件名排序）。
    """
    if not os.path.isdir(dir_path):
        logger.warning(f"目录不存在: {dir_path}")
        return []

    files: List[str] = []
    for filename in sorted(os.listdir(dir_path)):
        full_path = os.path.join(dir_path, filename)
        if not os.path.isfile(full_path):
            continue
        if allowed_types and not filename.lower().endswith(allowed_types):
            continue
        files.append(full_path)

    return files


def pdf_loader(file_path: str) -> List[Document]:
    """加载 PDF 文件，返回 Document 列表。"""
    loader = PyPDFLoader(file_path)
    return loader.load()


def txt_loader(file_path: str) -> List[Document]:
    """加载文本文件（UTF-8），返回单元素 Document 列表。"""
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    return [Document(page_content=text, metadata={"source": file_path})]
