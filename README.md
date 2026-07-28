Agentic RAG – Intelligent Document Question Answering System
AI-powered Retrieval-Augmented Generation application built with LangGraph, LangChain, FastAPI, React, ChromaDB and Gemini.

An Agentic Retrieval-Augmented Generation (RAG) system that allows users to upload documents (TXT, PDF and DOCX) and ask natural language questions. The application intelligently retrieves the most relevant information from uploaded documents and uses a Large Language Model to generate context-aware responses.

Unlike a traditional chatbot, this system uses an AI Agent capable of deciding when to retrieve documents or use external tools, making responses more accurate and reliable.

Live Demo

Frontend:

https://agentic-rag-knowledge-assistant.netlify.app

Backend:

https://agentic-rag-knowledge-assistant-z1xx.onrender.com

Features
 Upload multiple document formats (TXT, PDF, DOCX)

 Semantic search using vector embeddings

 Agentic RAG powered by LangGraph

Conversation memory for contextual chat

 Tool calling support (Calculator & Weather Tool)

 FastAPI backend with REST APIs

 Modern React frontend

 ChromaDB vector database

 Fully deployed frontend and backend

Real-time document indexing after upload

Source-aware responses based on uploaded documents

PostgreSQL-backed document and conversation history

PostgreSQL

Copy `.env.example` to `.env` and set `GOOGLE_API_KEY`. When the application is
started with Docker Compose, PostgreSQL is created automatically and the schema
in `sql/schema.sql` is applied on first startup. The backend also runs the
idempotent schema at startup, so existing databases receive any missing tables
or indexes.

The persistence API includes:

- `GET /documents`
- `DELETE /documents/{document_id}`
- `GET /chat/sessions`
- `GET /chat/sessions/{session_id}/messages`

Chat requests and document upload status are persisted automatically.

Tech Stack
Backend
Python
FastAPI
LangChain
LangGraph
Google Gemini
ChromaDB
Frontend
React
Vite
JavaScript
CSS
AI Components
Retrieval-Augmented Generation (RAG)
Embeddings
Semantic Search
Tool Calling
Memory
Prompt Engineering
Deployment
Render
Netlify

Architecture

                    User
                      │
                      ▼
             React Frontend
                      │
              REST API Request
                      │
                      ▼
                FastAPI Backend
                      │
          ┌───────────┴────────────┐
          │                        │
          ▼                        ▼
      LangGraph Agent        Document Upload
          │                        │
          │                 Document Loader
          │                        │
          │                 Text Splitter
          │                        │
          │                  Embeddings
          │                        │
          │                  ChromaDB
          │                        │
          └───────────┬────────────┘
                      │
          Decide whether to:
          • Retrieve Documents
          • Use Calculator Tool
          • Use Weather Tool
                      │
                      ▼
                Gemini LLM
                      │
                      ▼
              Final AI Response


Workflow

Document Upload


Upload File
      ↓
Load Document
      ↓
Split into Chunks
      ↓
Generate Embeddings
      ↓
Store in ChromaDB
















              
