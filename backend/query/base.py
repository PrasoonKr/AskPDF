from abc import ABC, abstractmethod


class QueryRewriter(ABC):
    """
    Base class for all query rewriters.
    """

    @abstractmethod
    def rewrite(
        self,
        query: str,
        recent_turns = None,
        summary: str = ""
    ) -> str:
        """
        Rewrite the user's query.
        """
        pass