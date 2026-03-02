import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import db
from app.db import User, user_role_enum
from app.schemas import UserRole
from app.v1.users import verify_token, get_current_user

router=APIRouter()

@router.get("/users", dependencies=[Depends(verify_token)],tags=["admin"])
async def get_users(session: AsyncSession = Depends(db.get_async_session),current_user:dict=Depends(get_current_user)):

    try:
        admin_search=await session.execute(select(User).where(User.username == current_user["username"]))
        admin=admin_search.scalars().first()
        if admin.user_role != UserRole.ADMIN:
            raise HTTPException(status_code=403,detail="You are not authorized to view this page")

        result = await session.execute(select(User).order_by(User.created_at.desc()).options(selectinload(User.prompts)).options(selectinload(User.report_requests)))
        users = [row[0] for row in result.all()]
        return users
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code,detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))

@router.get("/users/{id}",dependencies=[Depends(verify_token)],tags=["admin"])
async def get_user(id: str,session: AsyncSession = Depends(db.get_async_session),current_user:dict=Depends(get_current_user)):

    try:
        admin_search = await session.execute(select(User).where(User.username == current_user["username"]))
        admin = admin_search.scalars().first()
        if admin.user_role != UserRole.ADMIN:
            raise HTTPException(status_code=403,detail="You are not authorized to view this page")
        user_uuid=uuid.UUID(id)
        result = await session.execute(select(User).where(User.id == user_uuid))
        user=result.scalars().first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code,detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))

@router.patch("/change_user_role_to_admin/{id}", dependencies=[Depends(verify_token)],tags=["admin"])
async def change_user_role_to_admin(id:str,session:AsyncSession=Depends(db.get_async_session),current_user:dict=Depends(get_current_user)):
    try:
        admin_search = await session.execute(select(User).where(User.username == current_user["username"]))
        admin = admin_search.scalars().first()
        if admin.user_role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="You are not authorized to view this page")
        user_uuid = uuid.UUID(id)
        result = await session.execute(select(User).where(User.id == user_uuid))
        user = result.scalars().first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        if user.user_role==UserRole.ADMIN:
            raise HTTPException(status_code=400,detail="User is already admin.")
        user.user_role = UserRole.ADMIN
        await session.commit()
        await session.refresh(user)
        return user
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code,detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))

@router.delete("/users/{id}",dependencies=[Depends(verify_token)],tags=["admin"])
async def delete_user(id:str,session:AsyncSession=Depends(db.get_async_session),current_user:dict=Depends(get_current_user)):
    try:
        admin_search = await session.execute(select(User).where(User.username == current_user["username"]))
        admin = admin_search.scalars().first()
        if admin.user_role != UserRole.ADMIN:
            raise HTTPException(status_code=403,detail="You are not authorized to view this page")
        user_uuid=uuid.UUID(id)
        result = await session.execute(select(User).where(User.id == user_uuid))
        user=result.scalars().first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        await session.delete(user)
        await session.commit()
        return {"message":"User deleted successfully"}

    except HTTPException as e:
        raise HTTPException(status_code=e.status_code,detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))

@router.patch("/demote_admin_to_user/{id}",dependencies=[Depends(verify_token)],tags=["admin"])
async def demote_admin_to_user(id:str,session:AsyncSession=Depends(db.get_async_session),current_user:dict=Depends(get_current_user)):
    admin_search = await session.execute(select(User).where(User.username == current_user["username"]))
    admin = admin_search.scalars().first()
    if admin.user_role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="You are not authorized to view this page")
    user_uuid = uuid.UUID(id)
    result = await session.execute(select(User).where(User.id == user_uuid))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.user_role == UserRole.USER:
        raise HTTPException(status_code=400, detail="User is already with a user role.")
    user.user_role = UserRole.USER
    await session.commit()
    await session.refresh(user)
    return user