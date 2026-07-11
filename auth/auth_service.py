"""Authentication service — JWT tokens, password hashing with database storage."""

import os
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from sqlalchemy.orm import Session

from config.settings import settings
from db.models import User
from utils.logger_handler import app_logger

import bcrypt as _bcrypt

def _hash_password(password: str) -> str:
    """bcrypt hash，截断到 72 字节兼容 bcrypt>=5.x 的限制。"""
    return _bcrypt.hashpw(password.encode("utf-8")[:72], _bcrypt.gensalt()).decode("utf-8")

def _verify_password(password: str, password_hash: str) -> bool:
    pwd_bytes = password.encode("utf-8")[:72]
    return _bcrypt.checkpw(pwd_bytes, password_hash.encode("utf-8"))

# JWT signing key — regenerated on every restart (tokens invalidated)
# In production, persist this in environment variable JWT_SECRET_KEY
_jwt_secret = settings.jwt_secret_key or os.urandom(32).hex()


class AuthService:
    """Handles authentication: register, login, token lifecycle using MySQL."""

    def register(self, username: str, password: str, db: Session, nickname: str = "", avatar: str = "") -> Optional[dict]:
        if not username or len(username) < 2:
            return None
        if not password or len(password) < 6:
            return None
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            return None
        # Generate unique 9-digit numeric user_id
        for _ in range(100):
            user_id = str(random.randint(100000000, 999999999))
            if not db.query(User).filter(User.user_id == user_id).first():
                break
        else:
            return None
        display_name = nickname or username
        user = User(
            user_id=user_id,
            username=username,
            nickname=display_name,
            avatar=avatar or None,
            password_hash=_hash_password(password),
            role="user",
        )
        db.add(user)
        db.commit()
        app_logger.info(f"[Auth] Registered user: {username} (ID: {user_id})")
        return {"user_id": user_id, "username": username, "nickname": display_name, "avatar": avatar, "role": "user"}

    def authenticate(self, username: str, password: str, db: Session) -> Optional[dict]:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None
        if not _verify_password(password, user.password_hash):
            return None
        return {"user_id": user.user_id, "username": username, "nickname": user.nickname or username, "avatar": user.avatar or "", "role": user.role}

    # ---- JWT tokens -------------------------------------------------------

    def create_token(self, user_info: dict, expires_delta: Optional[timedelta] = None) -> str:
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=settings.jwt_expire_hours))
        payload = {
            "sub": user_info["user_id"],
            "username": user_info["username"],
            "role": user_info.get("role", "user"),
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": uuid.uuid4().hex[:16],
        }
        return jwt.encode(payload, _jwt_secret, algorithm=settings.jwt_algorithm)

    def verify_token(self, token: str, db: Session) -> Optional[dict]:
        try:
            payload = jwt.decode(token, _jwt_secret, algorithms=[settings.jwt_algorithm])
            user_id = payload["sub"]
            user = db.query(User).filter(User.user_id == user_id).first()
            if not user:
                return None
            return {"user_id": user.user_id, "username": user.username, "nickname": user.nickname or username, "role": user.role}
        except JWTError:
            return None


# Singleton
auth_service = AuthService()

