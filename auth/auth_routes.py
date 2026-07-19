"""认证 API 路由 — 注册、登录、令牌刷新，基于 MySQL。"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth.auth_service import auth_service
from auth.deps import get_current_user
from db.database import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ---- 请求 / 响应模型 ---------------------------------------------------

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)
    nickname: str = Field(default="", max_length=50)
    avatar: str = Field(default="", max_length=200000)

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str
    nickname: str = ""
    avatar: str = ""
    role: str

class UserInfo(BaseModel):
    user_id: str
    username: str
    nickname: str = ""
    avatar: str = ""
    role: str


# ---- 路由 ---------------------------------------------------------------

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: Session = Depends(get_db)):
    user = auth_service.register(body.username, body.password, db, nickname=body.nickname, avatar=body.avatar)
    if not user:
        raise HTTPException(status_code=409, detail="Username already exists or invalid credentials")
    token = auth_service.create_token(user)
    return TokenResponse(access_token=token, user_id=user["user_id"], username=user["username"], nickname=user.get("nickname", ""), role=user["role"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = auth_service.authenticate(body.username, body.password, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = auth_service.create_token(user)
    return TokenResponse(access_token=token, user_id=user["user_id"], username=user["username"], nickname=user.get("nickname", ""), avatar=user.get("avatar", ""), role=user["role"])


@router.get("/me", response_model=UserInfo)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserInfo(**current_user)
