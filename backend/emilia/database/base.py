from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import Optional

class DatabaseConfig(ABC):
    @abstractmethod
    def get_connection_string(self) -> str:
        pass

class Database(ABC):
    def __init__(self):
        self.async_sessionmaker: Optional[sessionmaker] = None

    @abstractmethod
    def setup(self) -> None:
        """Setup database connection and sessionmaker."""
        pass

    async def get_session(self) -> AsyncSession:
        """Provide a database session for FastAPI dependency injection."""
        if self.async_sessionmaker is None:
            raise Exception("Database not setup. Call setup() before requesting sessions.")
        async with self.async_sessionmaker() as session:
            yield session