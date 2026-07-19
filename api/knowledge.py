"""知识问答 + 知识文件管理 API — 管理端点需要认证。"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from pydantic import BaseModel

from agent.knowledge_agent import invoke_knowledge_agent
from config.settings import settings
from utils.logger_handler import app_logger, error_logger
from utils.path_tool import path_tool
from service.vector_store_service import VectorStoreService
from auth.deps import get_current_user

router = APIRouter(prefix="/api/chat/knowledge", tags=["knowledge"])
_knowledge_vs = VectorStoreService()


class KnowledgeQuery(BaseModel):
    query: str

class KnowledgeResponse(BaseModel):
    answer: str

class KnowledgeFileItem(BaseModel):
    filename: str
    size: int
    modified_at: float

class KnowledgeFilesResponse(BaseModel):
    files: list[KnowledgeFileItem]


@router.post("", response_model=KnowledgeResponse)
async def post_knowledge(body: KnowledgeQuery):
    """知识问答 — 对所有用户开放（访客和已认证用户均可使用）。"""
    try:
        answer = invoke_knowledge_agent(body.query)
        return KnowledgeResponse(answer=answer)
    except Exception as e:
        app_logger.error(f"Knowledge Agent failed: {e}", exc_info=True)
        error_logger.error(f"Knowledge Agent failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Knowledge service error")


# ---- Management endpoints — require authentication -----------------------

@router.get("/files", response_model=KnowledgeFilesResponse)
async def list_knowledge_files(current_user: dict = Depends(get_current_user)):
    files = _knowledge_vs.list_knowledge_files()
    return KnowledgeFilesResponse(files=[KnowledgeFileItem(**f) for f in files])


@router.post("/upload")
async def upload_knowledge_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if f".{ext}" not in settings.allowed_knowledge_types:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: .{ext}")
    know_dir = path_tool.get_knowledge_dir()
    know_dir.mkdir(parents=True, exist_ok=True)
    save_path = know_dir / file.filename
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    save_path.write_bytes(content)
    app_logger.info(f"Knowledge file uploaded: {file.filename} ({len(content)} bytes) by {current_user['username']}")
    _knowledge_vs.load_document()
    count = _knowledge_vs.vector_store._collection.count()
    return {"message": f"File {file.filename} uploaded", "total_chunks": count}


@router.delete("/files/{filename}")
async def delete_knowledge_file(
    filename: str,
    current_user: dict = Depends(get_current_user),
):
    ok = _knowledge_vs.delete_knowledge_file(filename)
    if not ok:
        raise HTTPException(status_code=404, detail=f"File {filename} not found")
    count = _knowledge_vs.reload_all()
    return {"message": f"File {filename} deleted", "total_chunks": count}


@router.post("/reload")
async def reload_knowledge(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    app_logger.info(f"Knowledge reload triggered by {current_user['username']}")
    def _bg_reload():
        count = _knowledge_vs.reload_all()
        app_logger.info(f"Knowledge reload complete, {count} chunks")
    background_tasks.add_task(_bg_reload)
    return {"message": "Knowledge reload started", "status": "running"}
