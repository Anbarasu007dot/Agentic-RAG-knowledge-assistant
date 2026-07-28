from datetime import datetime

from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    question: str = Field(
        min_length=1,
        description="Question sent to the Agentic RAG system"
    )
    thread_id: str = Field(
        min_length=1,
        description="Unique ID used to maintain conversation memory"
    )


class ChatResponse(BaseModel):
    question: str
    answer: str
    thread_id:str

class DocumentUploadResponse(BaseModel):
    id: int
    filename: str
    saved_filename: str
    content_type: str
    size_bytes: int
    indexed_chunks: int
    message: str


class DocumentResponse(BaseModel):
    id: int
    filename: str
    upload_time: datetime
    status: str
    collection_name: str | None = None
    source_type: str | None = None
    error_message: str | None = None


class ChatSessionResponse(BaseModel):
    id: str
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    id: int
    session_id: str
    role: str
    content: str
    created_at: datetime
