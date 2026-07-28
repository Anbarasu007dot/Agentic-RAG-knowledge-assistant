from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, File, HTTPException, UploadFile, status
from .agent import ask_agent, delete_document_chunks, ingest_document
from .database import (
    DatabaseOperationError,
    chat_session_exists,
    delete_document as delete_document_record,
    get_document,
    insert_assistant_message,
    insert_document,
    insert_user_message,
    initialize_database,
    list_chat_sessions,
    list_documents,
    list_messages,
    update_document_status,
)
from .schemas import (
    ChatRequest,
    ChatResponse,
    ChatSessionResponse,
    DocumentResponse,
    DocumentUploadResponse,
    MessageResponse,
)
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="Agentic RAG API",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://agentic-rag-knowledge-assistant.netlify.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCUMENTS_DIRECTORY = PROJECT_ROOT / "documents"

DOCUMENTS_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True,
)


ALLOWED_EXTENSIONS = {
    ".txt",
    ".pdf",
    ".docx",
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@app.get("/")
def root():
    return {
        "message": "Agentic RAG API is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        insert_user_message(request.thread_id, request.question)
        answer = ask_agent(
            question=request.question,
            thread_id=request.thread_id,
        )
        insert_assistant_message(request.thread_id, answer)

        return ChatResponse(
            question=request.question,
            answer=answer,
            thread_id=request.thread_id,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except DatabaseOperationError as error:
        logger.exception("Database failed while processing /chat")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The conversation could not be persisted.",
        ) from error

    except Exception as error:
        logger.exception("Agent failed while processing /chat")

        raise HTTPException(
            status_code=500,
            detail="The agent failed to process the question.",
        ) from error


@app.get("/documents", response_model=list[DocumentResponse])
def documents() -> list[DocumentResponse]:
    try:
        return [DocumentResponse(**row) for row in list_documents()]
    except DatabaseOperationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Document history is unavailable.",
        ) from error


@app.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_document(document_id: int) -> None:
    try:
        document = get_document(document_id)
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found.",
            )

        file_path = Path(document["file_path"]).resolve()
        try:
            file_path.relative_to(DOCUMENTS_DIRECTORY.resolve())
        except ValueError as error:
            logger.error("Refusing to delete path outside documents: %s", file_path)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The stored document path is invalid.",
            ) from error

        delete_document_chunks(file_path)
        if file_path.exists():
            file_path.unlink()
        delete_document_record(document_id)
    except HTTPException:
        raise
    except DatabaseOperationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The document could not be deleted.",
        ) from error
    except OSError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The stored document file could not be deleted.",
        ) from error


@app.get("/chat/sessions", response_model=list[ChatSessionResponse])
def chat_sessions() -> list[ChatSessionResponse]:
    try:
        return [ChatSessionResponse(**row) for row in list_chat_sessions()]
    except DatabaseOperationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Conversation history is unavailable.",
        ) from error


@app.get(
    "/chat/sessions/{session_id}/messages",
    response_model=list[MessageResponse],
)
def chat_messages(session_id: str) -> list[MessageResponse]:
    try:
        if not chat_session_exists(session_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found.",
            )
        return [MessageResponse(**row) for row in list_messages(session_id)]
    except HTTPException:
        raise
    except DatabaseOperationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Conversation messages are unavailable.",
        ) from error


@app.post(
    "/documents/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,)
async def upload_document(file: UploadFile = File(...),) -> DocumentUploadResponse:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file must have a filename.",
        )

    original_filename = Path(file.filename).name
    extension = Path(original_filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Unsupported file type. "
                "Only TXT, PDF and DOCX files are allowed."
            ),
        )

    contents = await file.read()

    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty.",
        )

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="The file is larger than the 10 MB limit.",
        )

    unique_filename = f"{uuid4().hex}_{original_filename}"
    destination = DOCUMENTS_DIRECTORY / unique_filename
    document_record = None

    try:
        destination.write_bytes(contents)
        document_record = insert_document(
            filename=original_filename,
            file_path=str(destination),
            collection_name="my_docs",
            source_type=extension.removeprefix("."),
        )
        indexed_chunks = ingest_document(destination)
        update_document_status(document_record["id"], "processed")

    except OSError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The file could not be saved.",
        ) from error

    except (ValueError, FileNotFoundError) as error:
        if document_record is not None:
            update_document_status(
                document_record["id"],
                "failed",
                str(error),
            )
        if destination.exists():
            destination.unlink()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except DatabaseOperationError as error:
        if destination.exists():
            destination.unlink()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The document metadata could not be persisted.",
        ) from error

    except Exception as error:
        if document_record is not None:
            try:
                update_document_status(
                    document_record["id"],
                    "failed",
                    "Document indexing failed.",
                )
            except DatabaseOperationError:
                logger.exception("Could not mark document upload as failed")
        if destination.exists():
            destination.unlink()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The document could not be indexed.",
        ) from error

    finally:
        await file.close()
    return DocumentUploadResponse(
        id=document_record["id"],
        filename=original_filename,
        saved_filename=unique_filename,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(contents),
        indexed_chunks=indexed_chunks,
        message="Document uploaded and indexed successfully.",
    )
