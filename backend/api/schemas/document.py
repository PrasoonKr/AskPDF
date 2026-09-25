from pydantic import BaseModel


class UploadResponse(BaseModel):
    documents: int
    chunks: int

class DocumentsResponse(BaseModel):
    documents: list[str]