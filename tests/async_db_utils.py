import asyncpg
from sqlalchemy.engine.url import make_url


async def create_database_async(url: str):
    u = make_url(url)
    database = u.database

    # Connect to the default 'postgres' database to perform administrative tasks
    # asyncpg expects a DSN or connection parameters.
    # We use the provided credentials but connect to 'postgres'

    password = u.password if u.password else ""

    conn = await asyncpg.connect(
        user=u.username, password=password, host=u.host, port=u.port, database="postgres"
    )
    try:
        # Check if database exists
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", database)
        if not exists:
            # CREATE DATABASE cannot be run in a transaction block
            await conn.execute(f'CREATE DATABASE "{database}"')
    finally:
        await conn.close()


async def drop_database_async(url: str):
    u = make_url(url)
    database = u.database

    password = u.password if u.password else ""

    conn = await asyncpg.connect(
        user=u.username, password=password, host=u.host, port=u.port, database="postgres"
    )
    try:
        # Drop the database
        # FORCE is supported in PG 13+ to terminate existing connections
        await conn.execute(f'DROP DATABASE IF EXISTS "{database}" WITH (FORCE)')
    finally:
        await conn.close()
