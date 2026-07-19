"""FastAPI 依赖注入：认证与授权。"""

from typing import Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from auth.auth_service import auth_service
from db.database import get_db

_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: Optional[HTTPBearer] = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> dict:
    """依赖注入：提取并验证当前用户。无效时返回 401。"""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = auth_service.verify_token(credentials.credentials, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def optional_current_user(
    request: Request,
    credentials: Optional[HTTPBearer] = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> Optional[dict]:
    """依赖注入：已认证返回用户信息，否则返回 None（访客模式）。"""
    if credentials is None:
        return None
    return auth_service.verify_token(credentials.credentials, db)
