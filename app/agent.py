from typing import Any
import os
import requests
from dotenv import load_dotenv
from pathlib import Path

from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    Docx2txtLoader,
)
from langchain_google_genai import (
    GoogleGenerativeAIEmbeddings,
    ChatGoogleGenerativeAI,
)
from langchain_chroma import Chroma
from langgraph.checkpoint.memory import InMemorySaver



# Environment variables


load_dotenv()

if not os.getenv("GOOGLE_API_KEY"):
    raise RuntimeError("GOOGLE_API_KEY is missing.")


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

project_root = Path(__file__).resolve().parent.parent

document_path = project_root / "documents" / "myfile.txt"
database_path = str(project_root / "chroma_db")
collection_name = "my_docs"



# Text splitter


splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=80,
    separators=["\n\n", "\n", ". ", " ", ""],
)


# ---------------------------------------------------------
# Load initial document only when it exists
# ---------------------------------------------------------

documents = []
chunks = []

if document_path.exists():
    loader = TextLoader(
        str(document_path),
        encoding="utf-8",
    )

    documents = loader.load()

    print(f"Loaded {len(documents)} document(s).")

    chunks = splitter.split_documents(documents)

    print(f"Created {len(chunks)} chunks.")

else:
    print(
        "No initial myfile.txt found. "
        "Starting with an empty knowledge base."
    )



# Embedding model


embedder = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001"
)


# Load or create Chroma

if os.path.exists(database_path):
    print("Loading the existing Chroma database.")

    vectorstore = Chroma(
        persist_directory=database_path,
        embedding_function=embedder,
        collection_name=collection_name,
    )

    print(
        f"Existing collection contains "
        f"{vectorstore._collection.count()} chunks."
    )

else:
    print("Creating a new Chroma database.")

    # Create an empty persistent Chroma collection.
    vectorstore = Chroma(
        persist_directory=database_path,
        embedding_function=embedder,
        collection_name=collection_name,
    )

    # Add the initial document only if it exists.
    if chunks:
        vectorstore.add_documents(chunks)

        print(
            f"Stored {vectorstore._collection.count()} chunks "
            f"in the database."
        )

    else:
        print("Created an empty Chroma collection.")



# Retriever


retriever = vectorstore.as_retriever(
    search_kwargs={"k": 3}
)



# Runtime document ingestion


def ingest_document(file_path: Path) -> int:
    """
    Load a document, split it into chunks, and add those
    chunks to the existing Chroma collection.

    Returns the number of chunks added.
    """

    if not file_path.exists():
        raise FileNotFoundError(
            f"Document does not exist: {file_path}"
        )

    extension = file_path.suffix.lower()

    if extension == ".txt":
        loader = TextLoader(
            str(file_path),
            encoding="utf-8",
        )

    elif extension == ".pdf":
        loader = PyPDFLoader(
            str(file_path)
        )

    elif extension == ".docx":
        loader = Docx2txtLoader(
            str(file_path)
        )

    else:
        raise ValueError(
            f"Unsupported document type: {extension}"
        )

    loaded_documents = loader.load()

    if not loaded_documents:
        raise ValueError(
            "No readable content was found in the document."
        )

    for document in loaded_documents:
        document.metadata["filename"] = file_path.name
        document.metadata["source"] = str(file_path)

    new_chunks = splitter.split_documents(
        loaded_documents
    )

    if not new_chunks:
        raise ValueError(
            "The document did not produce any text chunks."
        )

    vectorstore.add_documents(new_chunks)

    return len(new_chunks)


# ---------------------------------------------------------
# Gemini chat model
# ---------------------------------------------------------

llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash",
    temperature=0,
)





@tool
def calculator(expression: str) -> str:
    """Use this tool when the user asks for a mathematical calculation."""

    try:
        return str(eval(expression))

    except Exception as error:
        return f"Calculator error: {error}"



@tool
def getWeather(city: str) -> str:
    """Use this tool whenever the user asks for current weather details."""

    try:
        url = f"https://wttr.in/{city}?format=3"
        response = requests.get(
            url,
            timeout=10,
        )

        return response.text

    except Exception as error:
        return f"Weather error: {error}"




@tool
def searchDocuments(query: str) -> str:
    """Use this tool when the user asks about information in the documents."""

    docs = retriever.invoke(query)

    if not docs:
        return "No relevant information was found in the documents."

    return "\n\n".join(
        doc.page_content
        for doc in docs
    )



# Agent

tools = [
    calculator,
    getWeather,
    searchDocuments,
]

checkpointer = InMemorySaver()

agent = create_agent(
    model=llm,
    tools=tools,
    checkpointer=checkpointer,
    system_prompt="""
You are a helpful assistant with access to tools.

Use searchDocuments when the user asks about information that may exist in the loaded documents.

Use getWeather when the user asks about current weather.

Use calculator when the user asks for a mathematical calculation.

Use the conversation history to understand follow-up questions.

For follow-up document questions, convert unclear references into a complete search query before using searchDocuments.

For example:

Previous question:
Who built the Taj Mahal?

Follow-up question:
Why did he build it?

Search query:
Why did Shah Jahan build the Taj Mahal?

For document-related questions, answer only using the information returned by searchDocuments.

If the answer is not present in the retrieved documents, say:
"I don't have enough information in the documents to answer this."

Do not use tools when they are not necessary.
""",
)



# Extract agent response

def extract_text(content: Any) -> str:
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts: list[str] = []

        for block in content:
            if isinstance(block, str):
                text_parts.append(block)

            elif isinstance(block, dict):
                text = block.get("text")

                if text:
                    text_parts.append(str(text))

        return "\n".join(text_parts)

    return str(content)



def ask_agent(
    question: str,
    thread_id: str,
) -> str:
    result = agent.invoke(
        input={
            "messages": [
                {
                    "role": "user",
                    "content": question,
                }
            ]
        },
        config={
            "configurable": {
                "thread_id": thread_id
            }
        },
    )

    final_message = result["messages"][-1]

    answer = extract_text(
        final_message.content
    )

    return answer