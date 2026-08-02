import os
import pytest

from app.database import get_connection


@pytest.mark.skipif(
    not os.getenv("DATABASE_URL"),
    reason="DATABASE_URL is not set"
)
def test_database_connection_works():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 AS result")
            row = cursor.fetchone()

    assert row["result"] == 1