import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Conversation, get_async_session, User
from app.v1.users import verify_token, get_current_user

router=APIRouter(dependencies=[Depends(verify_token)])

@router.post("/conversation",tags=["conversations"])
async def create_conversation(session:AsyncSession=Depends(get_async_session),current_user: dict = Depends(get_current_user)):
    username_search = await session.execute(select(User).where(User.username == current_user["username"]))
    user = username_search.scalars().first()

    conversation=Conversation(

        user_id=user.id,
        topic ="",
        created_at =datetime.now(),
        modified_at =datetime.now(),

    )

    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)
    return conversation

@router.get("/conversations",tags=["conversations"])
async def get_conversations(session:AsyncSession=Depends(get_async_session)):
    conversations=await session.execute(select(Conversation).order_by(Conversation.created_at))
    return [row[0] for row in conversations.all()]

@router.get("/conversations/{conversation_id}",tags=["conversations"])
async def get_conversation(conversation_id:str,session:AsyncSession=Depends(get_async_session)):
    conversation_uuid=uuid.UUID(conversation_id)
    conversation_search=await session.execute(select(Conversation).where(Conversation.id == conversation_uuid))
    conversation=conversation_search.scalars().first()
    return conversation

@router.delete("/conversations/{conversation_id}",tags=["conversations"])
async def delete_conversation(conversation_id:str,session:AsyncSession=Depends(get_async_session)):
    conversation_uuid = uuid.UUID(conversation_id)
    conversation_search = await session.execute(select(Conversation).where(Conversation.id ==conversation_uuid))
    conversation = conversation_search.scalars().first()
    await session.delete(conversation)
    await session.commit()
    return "Conversation deleted!"