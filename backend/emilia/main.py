from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv
import os

# Import your database setup
from emilia.database.postgres import PostgresDatabase, DatabasePostgresConfig
from emilia.database.models import User
from emilia.database import crud

# Load environment variables
load_dotenv()

# Database connection details from environment variables
DATABASE_TYPE = os.getenv("DATABASE_TYPE", "postgres")
DATABASE_USERNAME = os.getenv("DATABASE_USERNAME", "postgres")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "postgres")
DATABASE_NAME = os.getenv("DATABASE_NAME", "postgres")
DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
DATABASE_PORT = os.getenv("DATABASE_PORT", "5432")


if DATABASE_TYPE == "postgres":
    # Initialize database configuration
    db_config = DatabasePostgresConfig(
        username=DATABASE_USERNAME,
        password=DATABASE_PASSWORD,
        db_name=DATABASE_NAME,
        host=DATABASE_HOST,
        port=DATABASE_PORT
    )

    # Initialize and setup the database
    db = PostgresDatabase(config=db_config)
    db.setup()

# FastAPI app
app = FastAPI()

# Dependency to get the database session
async def get_db() -> AsyncSession:
    async with db.async_sessionmaker() as session:
        yield session

@app.post("/users/", response_model=User)
async def create_user(user_data: dict, db: AsyncSession = Depends(get_db)):
    user = await crud.create_user(db, user_data=user_data)
    return user

@app.get("/users/{user_id}", response_model=User)
async def read_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await crud.get_user(db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/users/", response_model=list[User])
async def read_users(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    users = await crud.get_users(db, skip=skip, limit=limit)
    return users

@app.put("/users/{user_id}", response_model=User)
async def update_user(user_id: int, update_data: dict, db: AsyncSession = Depends(get_db)):
    user = await crud.update_user(db, user_id=user_id, update_data=update_data)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.delete("/users/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    await crud.delete_user(db, user_id=user_id)
    return {"message": "User deleted successfully"}
