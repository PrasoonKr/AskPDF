"""
Repository layer — all database CRUD operations in one place.
"""
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.database.models import User, Document, ChatSession, ChatMessage


# ─── Users ────────────────────────────────────────────────────────

def get_or_create_user(db: Session, email: str, name: str = "", picture: str = "") -> User:
    """Find user by email, or create if they don't exist."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email, name=name, picture=picture)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


# ─── Chat Sessions ────────────────────────────────────────────────

def create_chat_session(db: Session, user_id: str, title: str = "New Chat") -> ChatSession:
    session = ChatSession(user_id=user_id, title=title)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_user_sessions(db: Session, user_id: str) -> list[ChatSession]:
    """Get all sessions for a user, most recent first."""
    return (
        db.query(ChatSession)
        .filter(ChatSession.user_id == user_id)
        .order_by(ChatSession.updated_at.desc())
        .all()
    )


def get_session_by_id(db: Session, session_id: str) -> ChatSession | None:
    return db.query(ChatSession).filter(ChatSession.id == session_id).first()


def delete_session(db: Session, session_id: str) -> bool:
    session = get_session_by_id(db, session_id)
    if session:
        db.delete(session)
        db.commit()
        return True
    return False


def update_session_title(db: Session, session_id: str, title: str) -> ChatSession | None:
    session = get_session_by_id(db, session_id)
    if session:
        session.title = title
        session.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(session)
    return session


# ─── Chat Messages ────────────────────────────────────────────────

def add_message(
    db: Session,
    session_id: str,
    role: str,
    content: str,
    sources: list | None = None,
    trace: dict | None = None,
) -> ChatMessage:
    msg = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        sources=sources,
        trace=trace,
    )
    db.add(msg)
    # Also bump the session's updated_at
    session = get_session_by_id(db, session_id)
    if session:
        session.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(msg)
    return msg


def get_session_messages(db: Session, session_id: str) -> list[ChatMessage]:
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )


# ─── Documents ────────────────────────────────────────────────────

def create_document_record(
    db: Session, user_id: str, filename: str, chunk_count: int = 0, status: str = "READY"
) -> Document:
    doc = Document(
        user_id=user_id,
        filename=filename,
        chunk_count=chunk_count,
        status=status,
        processed_at=datetime.now(timezone.utc) if status == "READY" else None,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def delete_document_record(db: Session, user_id: str, filename: str) -> bool:
    doc = (
        db.query(Document)
        .filter(Document.user_id == user_id, Document.filename == filename)
        .first()
    )
    if doc:
        db.delete(doc)
        db.commit()
        return True
    return False

# ─── Document Chunks ──────────────────────────────────────────────

from backend.database.models import DocumentChunk

def add_document_chunks(db: Session, user_id: str, filename: str, chunks_data: list[dict]):
    db.bulk_insert_mappings(DocumentChunk, chunks_data)
    db.commit()

def get_chunks_by_faiss_ids(db: Session, faiss_ids: list[int]) -> list[DocumentChunk]:
    if not faiss_ids: return []
    return db.query(DocumentChunk).filter(DocumentChunk.faiss_id.in_(faiss_ids)).all()

def delete_document_chunks(db: Session, user_id: str, filename: str) -> list[int]:
    chunks = db.query(DocumentChunk).filter_by(user_id=user_id, filename=filename).all()
    faiss_ids = [c.faiss_id for c in chunks]
    for c in chunks:
        db.delete(c)
    db.commit()
    return faiss_ids

def get_all_chunks(db: Session, user_id: str) -> list[DocumentChunk]:
    return db.query(DocumentChunk).filter_by(user_id=user_id).all()
