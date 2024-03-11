import pytest

from sqlalchemy.orm import sessionmaker

from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from emilia.settings import Settings
from emilia.database.postgres import PostgresDatabase, DatabasePostgresConfig
from emilia.database.sqlite import SqliteDatabase, DatabaseSqliteConfig

settings = Settings()

@pytest.fixture
async def test_db():
    # Configure test database connection
    test_db_config = DatabasePostgresConfig(
        username=settings.DATABASE_USERNAME,
        password=settings.DATABASE_PASSWORD,
        db_name=settings.DATABASE_NAME,  # Consider using a separate test database
        host=settings.DATABASE_HOST,
        port=settings.DATABASE_PORT
    )
    test_db = PostgresDatabase(config=test_db_config)
    test_db.setup()

    # Create tables
    async with test_db.async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # Create a sessionmaker
    async_session_maker = sessionmaker(
        test_db.async_engine, class_=AsyncSession, expire_on_commit=False
    )

    # Yield a session for testing
    async with async_session_maker() as session:
        yield session

    # Drop tables after tests
    async with test_db.async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    await test_db.async_engine.dispose()

@pytest.fixture(name="sqlite_db")
async def fixture_sqlite_db():
    # Configure test SQLite database
    test_db_config = DatabaseSqliteConfig(db_name="test.db")
    sqlite_db = SqliteDatabase(config=test_db_config)
    sqlite_db.setup()

    # Create async session maker
    async_engine = create_async_engine(test_db_config.get_connection_string())
    async_session_maker = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )

    # Create tables
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # Yield session for testing
    async with async_session_maker() as session:
        yield session

    # Drop tables and dispose engine after tests
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await async_engine.dispose()