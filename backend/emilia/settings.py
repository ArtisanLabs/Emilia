from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_TYPE: str = "postgres"
    DATABASE_USERNAME: str = "postgres"
    DATABASE_PASSWORD: str = "postgres"
    DATABASE_NAME: str = "postgres"
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: str = "5432"

    class Config:
        env_file = ".env"

class TestSqliteSettings(BaseSettings):
    DATABASE_TYPE: str = "sqlite"
    DATABASE_NAME: str = "db.sqlite3"
    DATABASE_HOST: str = ""
    DATABASE_PORT: str = ""
    DATABASE_USERNAME: str = ""
    DATABASE_PASSWORD: str = ""

    def get_connection_string(self) -> str:
        return f"sqlite+aiosqlite:///{self.DATABASE_NAME}"

