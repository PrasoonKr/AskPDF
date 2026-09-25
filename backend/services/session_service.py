from uuid import uuid4

from backend.config import ConversationConfig

from backend.conversation.memory import (
    ConversationMemory,
)


class SessionService:

    def __init__(
        self,
        memory_factory,
    ):
        self.memory_factory = memory_factory

        self.sessions = {}

    def create_session(self) -> str:

        session_id = str(uuid4())

        self.sessions[
            session_id
        ] = self.memory_factory()

        return session_id

    def get_memory(
        self,
        session_id: str,
    ) -> ConversationMemory:

        if session_id not in self.sessions:

            self.sessions[
                session_id
            ] = self.memory_factory()

        return self.sessions[
            session_id
        ]

    def delete_session(
        self,
        session_id: str,
    ):

        self.sessions.pop(
            session_id,
            None,
        )