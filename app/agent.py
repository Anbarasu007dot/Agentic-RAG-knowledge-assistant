

from typing import Any
import os
import requests
from dotenv import load_dotenv


from langchain.agents import create_agent
from langchain_core.tools import tool

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader,PyPDFLoader,Docx2txtLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_chroma import Chroma

from langgraph.checkpoint.memory import InMemorySaver #This itself saves the memory !


load_dotenv()

if not os.getenv("GOOGLE_API_KEY"):
    raise RuntimeError("GOOGLE_API_KEY is missing.")

from pathlib import Path
project_root = Path(__file__).parent.parent

# Load the text document
loader = TextLoader(str(project_root /"documents"/"myfile.txt"), encoding="utf-8")
documents = loader.load()

print(f"Loaded {len(documents)} document(s).")

# Split the document into smaller chunks
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=80,
    separators=["\n\n", "\n", ". ", " ", ""],
)

chunks = splitter.split_documents(documents)

print(f"Created {len(chunks)} chunks.")


# Create the embedding model
embedder = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001"
)


# Set the Chroma database details
database_path = str(project_root /"chroma_db")
collection_name = "my_docs"


# Load the existing database or create a new one
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

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embedder,
        persist_directory=database_path,
        collection_name=collection_name,
    )

    print(
        f"Stored {vectorstore._collection.count()} chunks "
        f"in the database."
    )


# Create the retriever
retriever = vectorstore.as_retriever(
    search_kwargs={"k": 3}
)
def ingest_document(file_path: Path) -> int:
    """
    Load a document, split it into chunks, and add those chunks
    to the existing Chroma collection.

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

    # Add useful metadata to every loaded page/document.
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

# Create the Gemini chat model
llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash",
    temperature=0,
)


# Create a basic calculator tool
@tool
def calculator(expression: str) -> str:
    """Use this tool when the user asks for a mathematical calculation."""

    try:
        return str(eval(expression))

    except Exception as error:
        return f"Calculator error: {error}"


# Create a basic weather tool
@tool
def getWeather(city: str) -> str:
    """Use this tool whenever the user asks for current weather details."""

    try:
        url = f"https://wttr.in/{city}?format=3"
        response = requests.get(url, timeout=10)

        return response.text

    except Exception as error:
        return f"Weather error: {error}"


# Create a minimal document retrieval tool
@tool
def searchDocuments(query: str) -> str:
    """Use this tool when the user asks about information in the documents."""

    docs = retriever.invoke(query)

    if not docs:
        return "No relevant information was found in the documents."

    return "\n\n".join(doc.page_content for doc in docs)


# Store all tools in one list
tools = [
    calculator,
    getWeather,
    searchDocuments,
]


# Create an in-memory checkpointer for conversation history
checkpointer = InMemorySaver()


# Create the agentic RAG agent
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



def ask_agent(question: str,thread_id:str) -> str:
    result = agent.invoke(
        input={"messages": [
            {"role": "user", "content": question}
        ]},
        config={
            "configurable": {
                "thread_id": thread_id
            }
        }
    )
    final_message = result["messages"][-1]
    answer = extract_text(final_message.content)
    return answer









