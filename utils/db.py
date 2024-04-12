import os

from psycopg_pool import AsyncConnectionPool

connection_uri = os.getenv("DB_URI")

if connection_uri is None:
    raise Exception("DB_URI environment variable not set")

pool = AsyncConnectionPool(
    conninfo=connection_uri,
    open=False,
    check=AsyncConnectionPool.check_connection,
)
