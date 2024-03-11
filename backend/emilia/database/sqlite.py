import os
from sqlmodel import SQLModel, create_engine
from emilia.database.base import Database, DatabaseConfig
from emilia.settings import TestSqliteSettings

class DatabaseSqliteConfig(DatabaseConfig):
    def __init__(self, db_name: str = "db.sqlite3"):
        self.db_name = db_name

    def get_connection_string(self) -> str:
        # Note: Adjust the connection string if necessary for your SQLite setup
        return f"sqlite+aiosqlite:///{self.db_name}"

class SqliteDatabase(Database):
    def __init__(self, config: DatabaseSqliteConfig):
        super().__init__()
        self.config = config

    def setup(self) -> None:
        engine = create_engine(
            self.config.get_connection_string(),
            echo=True,  # Set to False in production
            future=True
        )
        SQLModel.metadata.create_all(engine)