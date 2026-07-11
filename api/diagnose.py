"""图片诊断 API 路由"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
import uuid

from agent.diagnose import invoke_diagnose, encode_image_to_base64
from service.guard_service import InputGuard
from utils.logger_handler import app_logger, error_logger
from utils.path_tool import path_tool

router = APIRouter(prefix="/api", tags=["diagnose"])
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/jpg"}
MAX_FILE_SIZE = 10 * 1024 * 1024


class DiagnoseResponse(BaseModel):
    diagnosis: str
    disease_name: str
    treatment: str
    image_filename: str


@router.post("/diagnose", response_model=DiagnoseResponse)
async def diagnose_image(file: UploadFile = File(...), description: str = Form("")):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="仅支持 JPEG/PNG 格式图片")
    image_bytes = await file.read()
    if len(image_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="图片文件过大，最大支持 10MB")
    ext = "png" if file.content_type == "image/png" else "jpeg"
    filename = f"{uuid.uuid4().hex[:12]}.{ext}"
    save_path = path_tool.get_upload_dir() / filename
    save_path.write_bytes(image_bytes)

    if description:
        ir = InputGuard.check_input(description)
        if ir:
            save_path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail=ir)

    b64_data = encode_image_to_base64(str(save_path))
    try:
        result = invoke_diagnose(image_data=b64_data, image_format=ext, user_description=description)
    except Exception as e:
        error_logger.error(f"图片诊断失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="诊断服务异常")

    return DiagnoseResponse(
        diagnosis=result["diagnosis"],
        disease_name=result["disease_name"],
        treatment=result["treatment"],
        image_filename=filename,
    )
