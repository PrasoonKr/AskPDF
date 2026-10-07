from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession

from backend.api.dependencies import (
    get_application,
    get_current_user,
)
from backend.database.session import get_db
from backend.database import repository as repo


router = APIRouter(
    prefix="/sessions",
    tags=["Sessions"],
)


class SessionResponse(BaseModel):
    session_id: str


class SessionListItem(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str


class SessionListResponse(BaseModel):
    sessions: list[SessionListItem]


class MessagesResponse(BaseModel):
    messages: list[dict]


class RenameRequest(BaseModel):
    title: str


@router.post("", response_model=SessionResponse)
def create_session(
    application=Depends(get_application),
    current_user=Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    user_email = current_user.get("email", "default")
    user_name = current_user.get("name", "")
    user_picture = current_user.get("picture", "")

    # Ensure user exists in DB
    db_user = repo.get_or_create_user(db, email=user_email, name=user_name, picture=user_picture)

    # Create in-memory session (for RAG pipeline conversation memory)
    memory_session_id = application.assistant_service.create_session()

    # Create persistent DB session
    db_session = repo.create_chat_session(db, user_id=db_user.id, title="New Chat")

    # Store mapping: DB session ID -> in-memory session ID
    # We use the DB session ID as the canonical ID
    application.assistant_service.map_session(db_session.id, memory_session_id)

    return SessionResponse(session_id=db_session.id)


@router.get("", response_model=SessionListResponse)
def list_sessions(
    current_user=Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    user_email = current_user.get("email", "default")
    db_user = repo.get_or_create_user(db, email=user_email)

    sessions = repo.get_user_sessions(db, user_id=db_user.id)
    return SessionListResponse(
        sessions=[
            SessionListItem(
                id=s.id,
                title=s.title,
                created_at=s.created_at.isoformat() + "Z",
                updated_at=s.updated_at.isoformat() + "Z",
            )
            for s in sessions
        ]
    )


@router.get("/{session_id}/messages", response_model=MessagesResponse)
def get_messages(
    session_id: str,
    current_user=Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    messages = repo.get_session_messages(db, session_id)
    return MessagesResponse(
        messages=[
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "sources": m.sources,
                "trace": m.trace,
                "created_at": m.created_at.isoformat() + "Z",
            }
            for m in messages
        ]
    )


@router.patch("/{session_id}")
def rename_session(
    session_id: str,
    body: RenameRequest,
    current_user=Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    session = repo.update_session_title(db, session_id, body.title)
    if not session:
        return {"error": "Session not found"}
    return {"id": session.id, "title": session.title}


@router.delete("/{session_id}")
def delete_session(
    session_id: str,
    application=Depends(get_application),
    current_user=Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    repo.delete_session(db, session_id)
    return {"message": "Session deleted"}