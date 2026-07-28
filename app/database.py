import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row


load_dotenv()


class DatabaseConfigurationError(RuntimeError):
    pass


class DatabaseOperationError(RuntimeError):
    pass


SCHEMA_PATH = Path(__file__).resolve().parent.parent / "sql" / "schema.sql"


def _database_url() -> str:
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise DatabaseConfigurationError("DATABASE_URL is missing.")

    return database_url


@contextmanager
def get_connection() -> Iterator[psycopg.Connection[dict[str, Any]]]:
    try:
        with psycopg.connect(
            _database_url(),
            row_factory=dict_row,
        ) as connection:
            yield connection
    except DatabaseConfigurationError:
        raise
    except psycopg.Error as error:
        raise DatabaseOperationError(
            "The database operation failed."
        ) from error


def initialize_database() -> None:
    """Create application tables and indexes when they do not exist."""
    try:
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(schema)
    except OSError as error:
        raise DatabaseConfigurationError(
            f"Database schema could not be read from {SCHEMA_PATH}."
        ) from error


def insert_document(
    filename: str,
    file_path: str,
    collection_name: str,
    source_type: str,
) -> dict[str, Any]:
    query = """
        INSERT INTO documents (
            filename,
            file_path,
            collection_name,
            source_type
        )
        VALUES (%s, %s, %s, %s)
        RETURNING
            id,
            filename,
            file_path,
            upload_time,
            status,
            collection_name,
            source_type,
            error_message
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                query,
                (
                    filename,
                    file_path,
                    collection_name,
                    source_type,
                ),
            )
            row = cursor.fetchone()

    if row is None:
        raise DatabaseOperationError(
            "The document record could not be created."
        )

    return row


def update_document_status(
    document_id: int,
    status: str,
    error_message: str | None = None,
) -> dict[str, Any]:
    if status not in {"processing", "processed", "failed"}:
        raise ValueError(f"Unsupported document status: {status}")

    query = """
        UPDATE documents
        SET
            status = %s,
            error_message = %s
        WHERE id = %s
        RETURNING
            id,
            filename,
            file_path,
            upload_time,
            status,
            collection_name,
            source_type,
            error_message
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                query,
                (status, error_message, document_id),
            )
            row = cursor.fetchone()

    if row is None:
        raise DatabaseOperationError(
            "The document record could not be updated."
        )

    return row


def list_documents() -> list[dict[str, Any]]:
    query = """
        SELECT
            id,
            filename,
            upload_time,
            status,
            collection_name,
            source_type,
            error_message
        FROM documents
        ORDER BY upload_time DESC, id DESC
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()


def get_document(document_id: int) -> dict[str, Any] | None:
    query = """
        SELECT
            id,
            filename,
            file_path,
            upload_time,
            status,
            collection_name,
            source_type,
            error_message
        FROM documents
        WHERE id = %s
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (document_id,))
            return cursor.fetchone()


def delete_document(document_id: int) -> bool:
    query = """
        DELETE FROM documents
        WHERE id = %s
        RETURNING id
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (document_id,))
            return cursor.fetchone() is not None


def insert_user_message(
    session_id: str,
    content: str,
) -> dict[str, Any]:
    create_session_query = """
        INSERT INTO chat_sessions (id)
        VALUES (%s)
        ON CONFLICT (id) DO NOTHING
    """
    insert_message_query = """
        INSERT INTO messages (session_id, role, content)
        VALUES (%s, %s, %s)
        RETURNING id, session_id, role, content, created_at
    """
    update_session_query = """
        UPDATE chat_sessions
        SET updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(create_session_query, (session_id,))
            cursor.execute(
                insert_message_query,
                (session_id, "user", content),
            )
            row = cursor.fetchone()
            cursor.execute(update_session_query, (session_id,))

    if row is None:
        raise DatabaseOperationError(
            "The user message could not be stored."
        )

    return row


def insert_assistant_message(
    session_id: str,
    content: str,
) -> dict[str, Any]:
    insert_message_query = """
        INSERT INTO messages (session_id, role, content)
        VALUES (%s, %s, %s)
        RETURNING id, session_id, role, content, created_at
    """
    update_session_query = """
        UPDATE chat_sessions
        SET updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                insert_message_query,
                (session_id, "assistant", content),
            )
            row = cursor.fetchone()
            cursor.execute(update_session_query, (session_id,))

    if row is None:
        raise DatabaseOperationError(
            "The assistant message could not be stored."
        )

    return row


def list_chat_sessions() -> list[dict[str, Any]]:
    query = """
        SELECT id, created_at, updated_at
        FROM chat_sessions
        ORDER BY updated_at DESC, created_at DESC
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()


def chat_session_exists(session_id: str) -> bool:
    query = """
        SELECT EXISTS (
            SELECT 1
            FROM chat_sessions
            WHERE id = %s
        ) AS exists
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (session_id,))
            row = cursor.fetchone()

    return bool(row and row["exists"])


def list_messages(session_id: str) -> list[dict[str, Any]]:
    query = """
        SELECT id, session_id, role, content, created_at
        FROM messages
        WHERE session_id = %s
        ORDER BY created_at, id
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (session_id,))
            return cursor.fetchall()
