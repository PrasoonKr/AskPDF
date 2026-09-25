from dataclasses import dataclass


@dataclass(slots=True)
class ConversationTurn:
    """
    Represents one complete conversation turn.

    A turn contains:
    - the user's message
    - the assistant's response
    """

    user: str
    assistant: str