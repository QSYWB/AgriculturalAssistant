"""用户资料与反馈 API 路由。"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
import json

from db.database import get_db
from db.models import User, Feedback
from auth.deps import get_current_user
from utils.logger_handler import app_logger
from utils.path_tool import path_tool

router = APIRouter(prefix="/api/user", tags=["user"])


class UpdateProfileRequest(BaseModel):
    nickname: Optional[str] = None


@router.get("/profile")
async def get_profile(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.user_id == current_user["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "user_id": user.user_id,
        "username": user.username,
        "nickname": user.nickname or user.username,
        "avatar": user.avatar or "",
        "role": user.role,
    }


@router.put("/profile")
async def update_profile(
    body: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.user_id == current_user["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if body.nickname is not None:
        if len(body.nickname) < 1 or len(body.nickname) > 50:
            raise HTTPException(status_code=400, detail="昵称长度应在1-50字符之间")
        user.nickname = body.nickname
    db.commit()
    return {"message": "Profile updated", "nickname": user.nickname or user.username}


@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if file.content_type not in ("image/jpeg", "image/png", "image/jpg"):
        raise HTTPException(status_code=400, detail="仅支持 JPEG/PNG 格式")
    content = await file.read()
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件过大，最大 2MB")
    upload_dir = path_tool.get_upload_dir() / "avatars"
    upload_dir.mkdir(parents=True, exist_ok=True)
    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
    fname = f"{current_user['user_id']}_{current_user['username']}.{ext}"
    save_path = upload_dir / fname
    save_path.write_bytes(content)
    user = db.query(User).filter(User.user_id == current_user["user_id"]).first()
    if user:
        user.avatar = f"/uploads/avatars/{fname}"
        db.commit()
    return {"avatar": user.avatar if user else ""}


# ---- 反馈 ----

class FeedbackRequest(BaseModel):
    content: str


@router.post("/feedback")
async def submit_feedback(
    body: FeedbackRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not body.content or len(body.content.strip()) < 1:
        raise HTTPException(status_code=400, detail="反馈内容不能为空")
    fb = Feedback(
        user_id=current_user["user_id"],
        content=body.content.strip(),
        images="",
    )
    db.add(fb)
    db.commit()
    app_logger.info(f"[Feedback] User {current_user['username']} submitted feedback")
    return {"message": "反馈已提交", "id": fb.id}


@router.post("/feedback/image")
async def upload_feedback_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    if file.content_type not in ("image/jpeg", "image/png", "image/jpg"):
        raise HTTPException(status_code=400, detail="仅支持 JPEG/PNG 格式")
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件过大，最大 5MB")
    upload_dir = path_tool.get_upload_dir() / "feedback"
    upload_dir.mkdir(parents=True, exist_ok=True)
    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
    import uuid
    fname = f"{uuid.uuid4().hex[:12]}.{ext}"
    save_path = upload_dir / fname
    save_path.write_bytes(content)
    return {"url": f"/uploads/feedback/{fname}"}


@router.get("/feedback")
async def list_feedback(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = (
        db.query(Feedback)
        .filter(Feedback.user_id == current_user["user_id"])
        .order_by(Feedback.created_at.desc())
        .limit(50)
        .all()
    )
    return {
        "items": [
            {
                "id": fb.id,
                "content": fb.content,
                "images": (json.loads(fb.images) if fb.images else []),
                "created_at": fb.created_at.isoformat(),
            }
            for fb in items
        ]
    }
