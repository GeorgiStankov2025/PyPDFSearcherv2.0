import uuid
from app.agent import invoke_chat_agent
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db import get_async_session, User
from app.db import Prompt
from app.schemas import PromptCreate
from app.v1.users import verify_token
from app.v1.users import get_current_user
from fastapi import Depends, HTTPException
from fastapi import APIRouter

router=APIRouter(dependencies=[Depends(verify_token)])

@router.post("/prompts",tags=["prompts"])
async def create_prompt(request:PromptCreate,session:AsyncSession=Depends(get_async_session),current_user: dict = Depends(get_current_user)):

    query=request.message
    response = await invoke_chat_agent(query)

    username_search = await session.execute(select(User).where(User.username == current_user["username"]))
    user = username_search.scalars().first()

    prompt=Prompt(

        message=request.message,
        response=response,
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