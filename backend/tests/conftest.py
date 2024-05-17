import asyncio
import pytest
import pytest_asyncio

from sqlalchemy.orm import sessionmaker

from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from emilia.settings import Settings, TestSqliteSettings
from emilia.database.postgres import PostgresDatabase, DatabasePostgresConfig
from emilia.database.sqlite import SqliteDatabase, DatabaseSqliteConfig

settings = Settings()
test_sqlite_settings = TestSqliteSettings()

@pytest.fixture(scope="session")
def event_loop(request):
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

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

@pytest.fixture(scope="class")
async def sqlite_engine(event_loop):
    # Configure test SQLite database
    
    test_db_config = DatabaseSqliteConfig(
        db_name=test_sqlite_settings.DATABASE_NAME
    )
    sqlite_db = SqliteDatabase(config=test_db_config)
    sqlite_db.setup()

    # Create async session maker
    sqlite_engine = create_async_engine(
        test_db_config.get_connection_string(),
        future=True,
        echo=True
        )
    
    async with sqlite_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

    yield sqlite_engine


@pytest_asyncio.fixture()
async def session(sqlite_engine):
    SessionLocal = sessionmaker(
        bind=sqlite_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with sqlite_engine.connect() as conn:
        tsx = await conn.begin()
        async with SessionLocal(bind=conn) as session:
            nested_tsx = await conn.begin_nested()
            yield session

            if nested_tsx.is_active:
                await nested_tsx.rollback()
            await tsx.rollback()