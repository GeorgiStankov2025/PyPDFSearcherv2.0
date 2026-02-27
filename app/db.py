import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from fastapi import Depends
from sqlalchemy import Text, String, Column, DateTime, ForeignKey, INT, Boolean,Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship
from app.schemas import UserRole
from sqlalchemy.dialects.postgresql import ENUM as pg_ENUM

DATABASE_URL = "postgresql+asyncpg://postgres:Bit_2024@localhost/pypdfsearcherdb"

user_role_enum = pg_ENUM(
    UserRole,
    name="user_role",      # The name inside Postgres
    create_type=True       # Tells SQLAlchemy to issue CREATE TYPE
)

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
    verification_code = Column(INT,nullable=False)
    user_role = Column(user_role_enum, nullable=False, server_default="USER")
    is_verified=Column(Boolean,nullable=False,default=False)
    prompts=relationship("Prompt",back_populates="user")
    report_requests=relationship("ReportRequest",back_populates="user")

class Prompt(Base):
    __tablename__ = "prompts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id=Column(UUID(as_uuid=True), ForeignKey("users.id"),nullable=False)
    message=Column(Text, nullable=False)
    response=Column(Text, nullable=False)
    created_at = Column(DateTime,nullable=False,default=datetime.now)
    user=relationship("User",back_populates="prompts")

class ReportRequest(Base):
    __tablename__ = "report_requests"
    id=Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id=Column(UUID(as_uuid=True), ForeignKey("users.id"),nullable=False)
    input_message=Column(Text, nullable=False)
    created_at=Column(DateTime,nullable=False,default=datetime.now)
    is_successful=Column(Boolean,nullable=False,default=False)
    user=relationship("User",back_populates="report_requests")

engine = create_async_engine(DATABASE_URL, future=True, echo=True)
async_session_maker=async_sessionmaker(engine,expire_on_commit=False)

async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_async_session()->AsyncGenerator[AsyncSession,None]:
    async with async_session_maker() as session:
        yield session
