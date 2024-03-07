import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from .base import Database, DatabaseConfig

class DatabasePostgresConfig(DatabaseConfig):
    def __init__(self, username: str = "postgres", password: str = os.getenv("POSTGRES_PASSWORD"), db_name: str = "your_db_name", host: str = "localhost", port: str = "5432"):
        self.username = username
        self.password = password
        self.db_name = db_name
        self.host = host
        self.port = port

    def get_connection_string(self) -> str:
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.db_name}"

class PostgresDatabase(Database):
    def __init__(self, config: DatabaseConfig):
        super().__init__()
        self.config = config

    def setup(self) -> None:
        async_engine = create_async_engine(
            self.config.get_connection_string(),
            echo=True,  # Set to False in production
        )
        self.async_sessionmaker = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)