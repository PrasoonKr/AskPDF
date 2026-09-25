from backend.config import ConversationConfig
from backend.conversation.turn import ConversationTurn


class ConversationMemory:
    """
    Maintains conversation memory using:

    1. Long-term summarized memory.
    2. Recent complete conversation turns.
    """

    def __init__(
        self,
        summarizer,
        max_recent_turns: int = ConversationConfig.MAX_RECENT_TURNS,
        summarize_turn_count: int = ConversationConfig.SUMMARIZE_TURN_COUNT,
    ):
        if max_recent_turns <= 0:
            raise ValueError(
                "max_recent_turns must be positive."
            )

        if summarize_turn_count <= 0:
            raise ValueError(
                "summarize_turn_count must be positive."
            )

        if summarize_turn_count > max_recent_turns:
            raise ValueError(
                "summarize_turn_count cannot be greater "
                "than max_recent_turns."
            )

        self.summarizer = summarizer

        self.max_recent_turns = (
            max_recent_turns
        )

        self.summarize_turn_count = (
            summarize_turn_count
        )

        self.turns = []

        self.summary = ""

    def add_turn(
        self,
        user: str,
        assistant: str,
    ):
        """
        Add one complete conversation turn.
        """

        turn = ConversationTurn(
            user=user,
            assistant=assistant,
        )

        self.turns.append(turn)

        self._summarize_if_needed()

    def _summarize_if_needed(self):
        """
        Summarize the oldest turns when recent
        conversation memory exceeds its limit.
        """

        if len(self.turns) <= self.max_recent_turns:
            return

        turns_to_summarize = self.turns[
            :self.summarize_turn_count
        ]

        try:
            updated_summary = (
                self.summarizer.summarize(
                    turns=turns_to_summarize,
                    previous_summary=self.summary,
                    )
            )

        except Exception as error:
            print(
                f"Conversation summarization failed: "
                f"{error}"
            )
            return

        self.summary = updated_summary

        self.turns = self.turns[
            self.summarize_turn_count:
        ]

    def get_recent_turns(
        self,
        limit: int | None = None,
    ):
        """
        Return recent conversation turns.
        """

        if limit is None:
            return self.turns.copy()

        if limit <= 0:
            return []

        return self.turns[-limit:].copy()

    def get_summary(self) -> str:
        """
        Return the long-term conversation summary.
        """

        return self.summary

    def clear(self):
        """
        Clear all conversation memory.
        """

        self.turns.clear()
        self.summary = ""