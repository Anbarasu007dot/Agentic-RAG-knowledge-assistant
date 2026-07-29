# Agentic RAG Assistant

Agentic RAG Assistant is a full-stack AI application that allows users to upload documents and ask questions based on their content.

The application uses Retrieval-Augmented Generation (RAG) to find relevant information from uploaded documents before generating an answer. It also includes persistent document metadata, chat sessions and message history using PostgreSQL.

## Live Application

- **Frontend:** [Open Agentic RAG Assistant](https://agentic-rag-knowledge-assistant.netlify.app/)
- **Backend API:** [Open Backend](https://agentic-rag-knowledge-assistant-z1xx.onrender.com/)
- **API Documentation:** [Open Swagger Documentation](https://agentic-rag-knowledge-assistant-z1xx.onrender.com/docs)

> The backend is hosted on Render, so the first request may take a short time if the service is inactive.

---

## Features

- Upload PDF, TXT and DOCX documents
- Split uploaded documents into smaller chunks
- Generate embeddings for document chunks
- Store and search embeddings using ChromaDB
- Ask questions based on uploaded documents
- Agent-based question handling using LangGraph
- Persistent chat sessions
- Persistent user and assistant message history
- View previous conversations
- List uploaded documents
- Delete uploaded documents
- Remove related document vectors from ChromaDB
- Store document metadata and processing status in PostgreSQL
- Run the application using Docker Compose
- Responsive React frontend

---

## Tech Stack

### Frontend

- React
- Vite
- JavaScript
- CSS
- Netlify

### Backend

- Python
- FastAPI
- LangChain
- LangGraph
- Google Gemini
- Psycopg
- Uvicorn

### Databases

- PostgreSQL for structured and persistent application data
- ChromaDB for embeddings and semantic search

### Development and Deployment

- Docker
- Docker Compose
- Git
- GitHub
- Render
- Netlify

---

## Application Architecture

```text
                   React Frontend
                         |
                         |
                    FastAPI API
                         |
                   LangGraph Agent
                         |
              ┌──────────┴──────────┐
              |                     |
         PostgreSQL              ChromaDB
              |                     |
     Documents and Chats       Embeddings and
       Message History        Semantic Retrieval
```

PostgreSQL and ChromaDB have different responsibilities in this project.

### PostgreSQL stores

- Uploaded document metadata
- Document processing status
- Chat sessions
- User messages
- Assistant messages

### ChromaDB stores

- Document embeddings
- Chunk metadata
- Vector search data

This allows PostgreSQL to manage structured application data while ChromaDB handles semantic document retrieval.

---

## How the Application Works

### Document Upload Flow

```text
Upload document
       ↓
Save the uploaded file
       ↓
Create document metadata in PostgreSQL
       ↓
Split the document into chunks
       ↓
Generate embeddings
       ↓
Store vectors in ChromaDB
       ↓
Update document status as processed
```

If document processing fails, its status is stored as `failed` in PostgreSQL.

### Question-Answering Flow

```text
User enters a question
       ↓
Save the user message in PostgreSQL
       ↓
Search relevant document chunks in ChromaDB
       ↓
Pass the retrieved context to the AI model
       ↓
Generate an answer
       ↓
Save the assistant response in PostgreSQL
       ↓
Display the answer in the frontend
```

---

## Main API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Checks whether the backend is running |
| `POST` | `/chat` | Sends a message to the assistant |
| `POST` | `/documents/upload` | Uploads and processes a document |
| `GET` | `/documents` | Returns uploaded documents |
| `DELETE` | `/documents/{document_id}` | Deletes a document and its vectors |
| `GET` | `/chat-history` | Returns previous chat sessions |
| `GET` | `/chat-history/{session_id}` | Returns messages from a chat session |

The complete API can be tested using the FastAPI Swagger documentation:

[https://agentic-rag-knowledge-assistant-z1xx.onrender.com/docs](https://agentic-rag-knowledge-assistant-z1xx.onrender.com/docs)

---

## Project Structure

```text
AgenticRAG_API/
│
├── app/
│   ├── main.py
│   ├── agent.py
│   ├── database.py
│   └── schemas.py
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── App.jsx
│   │   └── api.js
│   ├── package.json
│   └── vite.config.js
│
├── sql/
│   └── schema.sql
│
├── documents/
│
├── chroma_db/
│
├── .env.example
├── compose.yaml
├── Dockerfile
├── requirements.txt
├── pyproject.toml
└── README.md
```

Some generated folders may appear only after running the application.

---

## Running the Project Locally

### Prerequisites

Install the following tools:

- Python
- Node.js
- Git
- Docker Desktop

Using Docker Compose is the easiest way to run the complete application because PostgreSQL, the backend and the frontend can be started together.

### 1. Clone the repository

```bash
git clone <your-github-repository-url>
cd AgenticRAG_API
```

Replace `<your-github-repository-url>` with the actual URL of this repository.

### 2. Create the environment file

On PowerShell:

```powershell
Copy-Item .env.example .env
```

On Command Prompt, Linux or macOS:

```bash
cp .env.example .env
```

### 3. Add environment variables

Open `.env` and provide the required values.

```env
GOOGLE_API_KEY=your_google_api_key

POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_postgres_password
POSTGRES_DB=agentic_rag

DATABASE_URL=postgresql://postgres:your_postgres_password@postgres:5432/agentic_rag
```

Do not commit the real `.env` file to GitHub.

### 4. Start the application

Make sure Docker Desktop is running.

```bash
docker compose up --build
```

After the containers start, open the frontend URL shown in the terminal or Docker Compose configuration.

The backend is normally available at:

```text
http://localhost:8000
```

The API documentation is available at:

```text
http://localhost:8000/docs
```

### 5. Stop the application

```bash
docker compose down
```

To stop the containers and remove their stored volumes:

```bash
docker compose down -v
```

> Using `-v` removes persisted PostgreSQL and ChromaDB data.

---

## Environment Variables

| Variable | Purpose |
|---|---|
| `GOOGLE_API_KEY` | Used to access the Gemini model and embeddings |
| `DATABASE_URL` | PostgreSQL connection string |
| `POSTGRES_USER` | PostgreSQL username used by Docker |
| `POSTGRES_PASSWORD` | PostgreSQL password used by Docker |
| `POSTGRES_DB` | PostgreSQL database name |
| `VITE_API_BASE_URL` | Backend URL used by the React frontend |

Example frontend environment value:

```env
VITE_API_BASE_URL=http://localhost:8000
```

For deployment, this should point to the deployed backend URL.

---

## Document Deletion

Deleting a document removes it from all related storage locations:

1. The document metadata is removed from PostgreSQL.
2. The uploaded file is removed from the server.
3. The matching document vectors are removed from ChromaDB.

This prevents deleted documents from appearing in future retrieval results.

---

## Persistence

PostgreSQL and ChromaDB use persistent storage.

This means the following data remains available after restarting the application:

- Uploaded document metadata
- Chat sessions
- User and assistant messages
- Uploaded files
- Document vectors

---

## Testing Completed

The following operations were tested successfully:

- PostgreSQL health and connection
- FastAPI health endpoint
- Database schema creation
- Document upload
- Document metadata storage
- ChromaDB vector creation
- Document listing
- User message persistence
- Assistant message persistence
- Chat-session retrieval
- Message-history retrieval
- Data persistence after container restart
- Document deletion
- Uploaded-file cleanup
- ChromaDB vector cleanup

---

## What I Learned

While building this project, I learned and practised:

- Creating a RAG pipeline
- Splitting documents into chunks
- Generating and storing embeddings
- Performing semantic search
- Building APIs with FastAPI
- Creating an agent workflow with LangGraph
- Connecting a React frontend to a FastAPI backend
- Using PostgreSQL from Python with Psycopg
- Writing parameterised SQL queries
- Persisting chat sessions and messages
- Managing PostgreSQL and ChromaDB together
- Containerising an application with Docker
- Running multiple services using Docker Compose
- Deploying a frontend and backend separately
- Managing environment variables securely
- Using Git and GitHub for version control

---

## Possible Future Improvements

- Add user authentication
- Associate documents and conversations with individual users
- Process large document uploads in the background
- Add support for more document formats
- Improve retrieval evaluation
- Add application logging and monitoring
- Store uploaded files using cloud object storage

---

## Purpose of the Project

This project was created as a learning and portfolio project to understand how a full-stack RAG application can be built using AI, backend development, databases, vector search and deployment tools.

It demonstrates both AI development concepts and general backend engineering concepts such as APIs, persistence, database design, Docker and frontend integration.
