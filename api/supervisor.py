"""Supervisor API routes — supports guest (no persistence) and authenticated (MySQL) modes."""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
from sqlalchemy.orm import Session

from agent.supervisor import invoke_supervisor
from service.conversation_service import conversation_service
from service.guard_service import InputGuard, OutputGuard, PathSecurity
from service.geo_service import geo_service
from utils.logger_handler import app_logger, error_logger
from auth.deps import optional_current_user, get_current_user
from db.database import get_db

router = APIRouter(prefix="/api/chat", tags=["supervisor"])


class ChatRequest(BaseModel):
    query: str
    session_id: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class ChatResponse(BaseModel):
    answer: str
    session_id: str  # empty string for guest mode


class SessionInfo(BaseModel):
    session_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int


class SessionListResponse(BaseModel):
    sessions: list[SessionInfo]
    total: int


@router.post("/supervisor", response_model=ChatResponse)
async def post_supervisor(
    body: ChatRequest,
    request: Request,
    current_user: dict = Depends(optional_current_user),
    db: Session = Depends(get_db),
):
    """Chat endpoint — works for both guest and authenticated users."""
    try:
        user_id = current_user["user_id"] if current_user else None
        session_id = body.session_id or ""

        if user_id:
            # Authenticated: use or create session
            if body.session_id:
                s = conversation_service.get_session(db, body.session_id, user_id)
                if not s:
                    raise HTTPException(status_code=404, detail=f"Session {body.session_id} not found")
            else:
                session_id = conversation_service.create_session(db, user_id)

            ireason = InputGuard.check_input(body.query)
            if ireason:
                raise HTTPException(status_code=400, detail=ireason)

            conversation_service.add_user_message(db, session_id, body.query, user_id)
            history_summary = conversation_service.get_history_summary(db, session_id)
            last_turn = conversation_service.get_last_assistant_message(db, session_id)
        else:
            # Guest: no persistence
            ireason = InputGuard.check_input(body.query)
            if ireason:
                raise HTTPException(status_code=400, detail=ireason)
            history_summary = ""
            last_turn = ""

        user_location = ""
        if body.latitude is not None and body.longitude is not None:
            user_location = geo_service.reverse_geocode(body.latitude, body.longitude)
        if not user_location and request.client:
            user_location = geo_service.ip_geolocation(request.client.host)

        answer = await invoke_supervisor(
            query=body.query,
            history_summary=history_summary,
            last_turn_result=last_turn,
            user_location=user_location,
        )
        answer = OutputGuard.sanitize(answer)

        if user_id and session_id:
            conversation_service.add_assistant_message(db, session_id, answer, user_id)

        return ChatResponse(answer=answer, session_id=session_id)

    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Supervisor call failed: {e}", exc_info=True)
        error_logger.error(f"Supervisor call failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Service error")


@router.post("/supervisor/stream")
async def stream_supervisor(
    body: ChatRequest,
    request: Request,
    current_user: dict = Depends(optional_current_user),
    db: Session = Depends(get_db),
):
    """SSE streaming chat — works for both guest and authenticated users."""
    user_id = current_user["user_id"] if current_user else None
    session_id = body.session_id or ""

    if user_id:
        if body.session_id:
            s = conversation_service.get_session(db, body.session_id, user_id)
            if not s:
                raise HTTPException(status_code=404, detail=f"Session {body.session_id} not found")
        else:
            session_id = conversation_service.create_session(db, user_id)

    ireason = InputGuard.check_input(body.query)
    if ireason:
        raise HTTPException(status_code=400, detail=ireason)

    if user_id and session_id:
        conversation_service.add_user_message(db, session_id, body.query, user_id)
        history_summary = conversation_service.get_history_summary(db, session_id)
        last_turn = conversation_service.get_last_assistant_message(db, session_id)
    else:
        history_summary = ""
        last_turn = ""

    user_location = ""
    if body.latitude is not None and body.longitude is not None:
        user_location = geo_service.reverse_geocode(body.latitude, body.longitude)
    if not user_location and request.client:
        user_location = geo_service.ip_geolocation(request.client.host)

    async def generate():
        yield "event: connected\ndata: {}\n\n"
        try:
            answer = await invoke_supervisor(
                query=body.query,
                history_summary=history_summary,
                last_turn_result=last_turn,
                user_location=user_location,
            )
            if user_id and session_id:
                conversation_service.add_assistant_message(db, session_id, answer, user_id)
            for i in range(0, len(answer), 3):
                chunk = answer[i:i+3]
                yield f"event: token\ndata: {chunk}\n\n"
                await asyncio.sleep(0.008)
            yield f"event: done\ndata: {session_id}\n\n"
        except Exception as e:
            app_logger.error(f"SSE failed: {e}", exc_info=True)
            yield "event: error\ndata: Service error\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ---- Session management (authenticated only) --------------------------------

@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sessions = conversation_service.list_sessions(db, current_user["user_id"], limit=limit)
    return SessionListResponse(
        sessions=[SessionInfo(**s) for s in sessions],
        total=len(sessions),
    )


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pr = PathSecurity.check_session_id(session_id)
    if pr:
        raise HTTPException(status_code=400, detail=pr)
    ok = conversation_service.delete_session(db, session_id, current_user["user_id"])
    if not ok:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return {"message": f"Session {session_id} deleted"}


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pr = PathSecurity.check_session_id(session_id)
    if pr:
        raise HTTPException(status_code=400, detail=pr)
    session = conversation_service.get_session(db, session_id, current_user["user_id"])
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    messages = conversation_service.get_history(db, session_id, current_user["user_id"])
    return {
        "session_id": session_id,
        "messages": [{"role": m["role"], "content": m["content"]} for m in messages],
    }

