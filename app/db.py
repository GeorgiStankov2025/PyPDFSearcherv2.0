import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from fastapi import Depends
from sqlalchemy import Text, String, Column, DateTime, ForeignKey, INT, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship
from fastapi_users.db import SQLAlchemyUserDatabase,SQLAlchemyBaseUserTableUUID

DATABASE_URL = "postgresql+asyncpg://postgres:Bit_2024@localhost/pypdfsearcherdb"

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    password_hash = Column(String(100), nullable=False)
    created_at = Column(DateTime,nullable=False)
    modified_at = Column(DateTime,nullable=False)
    is_verified=Column(Boolean,nullable=False,default=False)

class Prompt(Base):
    __tablename__ = "prompts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message=Column(Text, nullable=False)
    response=Column(Text, nullable=False)
    created_at = Column(DateTime,nullable=False,default=datetime.now)


engine = create_async_engine(DATABASE_URL)
async_session_maker=async_sessionmaker(engine,expire_on_commit=False)

async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_async_session()->AsyncGenerator[AsyncSession,None]:
    async with async_session_maker() as session:
        yield session
