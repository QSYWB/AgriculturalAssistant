"""多轮对话记忆服务 — 支持访客模式（无持久化）和认证模式（MySQL）。"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from db.models import ChatSession, Message
from utils.logger_handler import app_logger


class ConversationService:
    """处理对话会话。
    
    - Guest mode (user_id=None): sessions are not persisted, in-memory only.
    - Authenticated mode (user_id set): sessions stored in MySQL.
    """

    def create_session(self, db: Session, user_id: Optional[str] = None, title: str = "新会话") -> str:
        """创建新会话。返回 session_id 字符串。"""
        sid = uuid.uuid4().hex[:12]
        if user_id:
            session = ChatSession(
                session_id=sid,
                user_id=user_id,
                title=title,
            )
            db.add(session)
            db.commit()
        return sid

    def delete_session(self, db: Session, sid: str, user_id: Optional[str] = None) -> bool:
        """删除会话。删除成功返回 True。"""
        if not user_id:
            return False
        session = db.query(ChatSession).filter(
            ChatSession.session_id == sid,
            ChatSession.user_id == user_id,
        ).first()
        if not session:
            return False
        db.delete(session)
        db.commit()
        return True

    def get_session(self, db: Session, sid: str, user_id: Optional[str] = None) -> Optional[dict]:
        if not user_id:
            return None
        session = db.query(ChatSession).filter(
            ChatSession.session_id == sid,
            ChatSession.user_id == user_id,
        ).first()
        if not session:
            return None
        return {
            "session_id": session.session_id,
            "title": session.title,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "message_count": session.message_count,
        }

    def list_sessions(self, db: Session, user_id: Optional[str] = None, limit: int = 50) -> List[dict]:
        if not user_id:
            return []
        sessions = (
            db.query(ChatSession)
            .filter(ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "session_id": s.session_id,
                "title": s.title,
                "created_at": s.created_at.isoformat(),
                "updated_at": s.updated_at.isoformat(),
                "message_count": s.message_count,
            }
            for s in sessions
        ]

    def add_user_message(self, db: Session, sid: str, content: str, user_id: Optional[str] = None) -> bool:
        if not user_id:
            return True  # 访客：空操作，假装成功
        return self._add_message(db, sid, content, "user")

    def add_assistant_message(self, db: Session, sid: str, content: str, user_id: Optional[str] = None) -> bool:
        if not user_id:
            return True  # 访客：空操作
        return self._add_message(db, sid, content, "assistant")

    def _add_message(self, db: Session, sid: str, content: str, role: str) -> bool:
        msg = Message(session_id=sid, role=role, content=content)
        db.add(msg)
        # 更新会话元信息
        session = db.query(ChatSession).filter(ChatSession.session_id == sid).first()
        if session:
            session.message_count = (session.message_count or 0) + 1
            session.updated_at = datetime.now(timezone.utc)
            if role == "user" and session.message_count == 1:
                session.title = content[:20] + ("..." if len(content) > 20 else "")
        db.commit()
        return True

    def get_history(self, db: Session, sid: str, user_id: Optional[str] = None) -> List[dict]:
        if not user_id:
            return []
        messages = (
            db.query(Message)
            .filter(Message.session_id == sid)
            .order_by(Message.id.asc())
            .all()
        )
        return [{"role": m.role, "content": m.content} for m in messages]

    def get_history_summary(self, db: Session, sid: str, max_exchanges: int = 3) -> str:
        """获取最近几轮对话的简短摘要，用于上下文注入。"""
        messages = (
            db.query(Message)
            .filter(Message.session_id == sid)
            .order_by(Message.id.asc())
            .all()
        )
        pairs = []
        pair = {}
        for msg in messages:
            if msg.role == "user":
                pair = {"user": msg.content[:100]}
            elif msg.role == "assistant" and pair:
                pair["assistant"] = msg.content[:100]
                pairs.append(pair)
                pair = {}
        recent = pairs[-max_exchanges:]
        return "\n".join(
            f"第{i+1}轮 用户说「{p.get('user', '')[:80]}」，助手回答「{p.get('assistant', '')[:80]}」"
            for i, p in enumerate(recent)
        )

    def get_last_assistant_message(self, db: Session, sid: str) -> str:
        msg = (
            db.query(Message)
            .filter(Message.session_id == sid, Message.role == "assistant")
            .order_by(Message.id.desc())
            .first()
        )
        return msg.content if msg else ""


# 单例 — 供 API 路由使用；方法接受 user_id 参数以支持访客模式
conversation_service = ConversationService()
