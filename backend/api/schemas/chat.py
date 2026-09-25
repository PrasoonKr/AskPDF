from pydantic import BaseModel


class ChatRequest(BaseModel):

    session_id: str

    question: str


class SourceResponse(BaseModel):

    source: str

    page: int

    score: float


class ChatResponse(BaseModel):

    answer: str

    sources: list[SourceResponse]
    
    trace: str | None = None