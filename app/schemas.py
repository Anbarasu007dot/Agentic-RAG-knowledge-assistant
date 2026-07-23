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
    filename: str
    saved_filename: str
    content_type: str
    size_bytes: int
    indexed_chunks: int
    message: str