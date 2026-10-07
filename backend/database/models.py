"""
SQLAlchemy ORM models for AskPDF.

Tables:
  - users: Google OAuth / dev-login users
  - documents: PDF metadata and processing status
  - chat_sessions: Conversation sessions per user
  - chat_messages: Individual messages within a session
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Text, Integer, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship

from backend.database.session import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _new_id():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=_new_id)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, default="")
    picture = Column(String, default="")
    created_at = Column(DateTime, default=_utcnow)

    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=_new_id)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String, nullable=False)
    status = Column(String, default="READY")  # UPLOADED, PROCESSING, READY, FAILED
    chunk_count = Column(Integer, default=0)
    uploaded_at = Column(DateTime, default=_utcnow)
    processed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="documents")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, default=_new_id)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, default="New Chat")
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    user = relationship("User", back_populates="sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=_new_id)
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False, index=True)
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    sources = Column(JSON, nullable=True)  # Source chips data for assistant messages
    trace = Column(JSON, nullable=True)    # Retrieval trace data for assistant messages
    created_at = Column(DateTime, default=_utcnow)

    session = relationship("ChatSession", back_populates="messages")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String, primary_key=True, default=_new_id)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String, nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    page = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    faiss_id = Column(Integer, nullable=False, index=True)
