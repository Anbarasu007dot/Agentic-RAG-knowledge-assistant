from pathlib import Path
from uuid import uuid4
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, File, HTTPException, UploadFile, status
from .agent import ask_agent,ingest_document
from .schemas import (
    ChatRequest,
    ChatResponse,DocumentUploadResponse



)


app = FastAPI(
    title="Agentic RAG API",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173"
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
        answer = ask_agent(
            question=request.question,
            thread_id=request.thread_id,
        )

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

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The agent failed to process the question.",
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

    try:
        destination.write_bytes(contents)

        indexed_chunks = ingest_document(destination)

    except OSError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The file could not be saved.",
        ) from error

    except (ValueError, FileNotFoundError) as error:
        # Delete the saved file when indexing fails.
        if destination.exists():
            destination.unlink()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except Exception as error:
        # Avoid leaving an unindexed file behind.
        if destination.exists():
            destination.unlink()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The document could not be indexed.",
        ) from error

    finally:
        await file.close()
    return DocumentUploadResponse(
        filename=original_filename,
        saved_filename=unique_filename,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(contents),
        indexed_chunks=indexed_chunks,
        message="Document uploaded and indexed successfully.",
    )