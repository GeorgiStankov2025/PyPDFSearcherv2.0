# %%
import operator
import uuid
from fastapi import HTTPException
from typing import Annotated, TypedDict, List
from uuid import UUID

from fastapi import APIRouter,Depends
from langchain_experimental.graph_transformers.llm import system_prompt
from langgraph.types import Command
from langchain_openai import OpenAIEmbeddings
import os
from langchain_community.document_loaders import PyPDFDirectoryLoader, TextLoader
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agent import invoke_agent, initialize_agent
from app.db import get_async_session, User
from langchain_core.tools import tool, InjectedToolCallId
from langchain_qdrant import QdrantVectorStore
from fastapi import Request
from app.db import Prompt
from app.schemas import PromptCreate
from app.v1.users import verify_token
from app.v1.users import get_current_user
from fastapi import Depends, HTTPException
from fastapi import APIRouter
from app.agent import initialize_agent
router=APIRouter(dependencies=[Depends(verify_token)])
agent=initialize_agent()

@router.post("/prompts",tags=["prompts"])
async def create_prompt(request:PromptCreate,session:AsyncSession=Depends(get_async_session),current_user: dict = Depends(get_current_user)):

    query={"messages": [("user", request.message)]}

    response = await invoke_agent(agent=agent, query=query)

    username_search = await session.execute(select(User).where(User.username == current_user["username"]))
    user = username_search.scalars().first()

    prompt=Prompt(

        message=request.message,
        response=response["messages"][-1].content,
        user_id=user.id,

    )
    session.add(prompt)
    await session.commit()
    await session.refresh(prompt)
    return prompt

@router.get("/prompts",tags=["prompts"])
async def get_all_prompts(session:AsyncSession=Depends(get_async_session)):
    result = await session.execute(select(Prompt).order_by(Prompt.created_at.desc()).options(selectinload(Prompt.user)))
    prompts = [row[0] for row in result.all()]
    return prompts

@router.get("/prompts/{id}",tags=["prompts"])
async def get_prompt(id:str,session:AsyncSession=Depends(get_async_session),current_user:dict=Depends(get_current_user)):
    try:
        id_uuid=uuid.UUID(id)
        result=await session.execute(select(Prompt).where(Prompt.id == id_uuid))
        prompt=result.scalars().first()

        if prompt is None:
            raise HTTPException(status_code=404,detail="Prompt not found")
        user_result = await session.execute(select(User).where(User.username == current_user["username"]))
        user = user_result.scalars().first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        if user.id!=prompt.user_id:
            raise HTTPException(status_code=403,detail="User cannot perform this action")

        return prompt
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code,detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))

@router.delete("/prompts/{id}",tags=["prompts"])
async def delete_prompt(id:str,session:AsyncSession=Depends(get_async_session),current_user:dict=Depends(get_current_user)):
    try:
        id_uuid=uuid.UUID(id)
        prompt_result=await session.execute(select(Prompt).where(Prompt.id == id_uuid))
        prompt=prompt_result.scalars().first()

        user_result=await session.execute(select(User).where(User.username == current_user["username"]))
        user=user_result.scalars().first()

        if user is None:
            raise HTTPException(status_code=404,detail="User not found")
        if prompt is None:
            raise HTTPException(status_code=404,detail="Prompt not found")
        if user.id!=prompt.user_id:
            raise HTTPException(status_code=403,detail="User cannot perform this action")

        await session.delete(prompt)
        await session.commit()
        return {"message":"Prompt deleted successfully"}
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code,detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))