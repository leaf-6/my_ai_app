from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
import time
import random
from app.database import get_db
from app.models import Session as DBSession, Message
from app.auth import get_current_user_id

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

class SessionCreate(BaseModel):
    title: str = "新对话"

@router.get("")
def get_sessions(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    sessions = db.query(DBSession).filter(DBSession.user_id == user_id).order_by(DBSession.updated_at.desc()).all()
    return [
        {
            "id": s.id,
            "title": s.title,
            "message_count": db.query(Message).filter(Message.session_id == s.id).count(),
            "updated_at": s.updated_at.isoformat()
        }
        for s in sessions
    ]

@router.post("")
def create_session(
    data: SessionCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    session_id = str(int(time.time() * 1000)) + hex(random.randint(0, 65536))[2:]
    session = DBSession(id=session_id, user_id=user_id, title=data.title)
    db.add(session)
    db.commit()
    return {"id": session_id, "title": session.title}

@router.delete("/{session_id}")
def delete_session(
    session_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    session = db.query(DBSession).filter(DBSession.id == session_id, DBSession.user_id == user_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在或无权限")
    db.query(Message).filter(Message.session_id == session_id).delete()
    db.delete(session)
    db.commit()
    return {"ok": True}

@router.get("/{session_id}/messages")
def get_messages(
    session_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    session = db.query(DBSession).filter(DBSession.id == session_id, DBSession.user_id == user_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在或无权限")
    messages = db.query(Message).filter(Message.session_id == session_id).order_by(Message.timestamp).all()
    return [
        {"text": m.text, "sender": m.sender, "timestamp": m.timestamp.isoformat()}
        for m in messages
    ]