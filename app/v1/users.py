import random
import time
from datetime import datetime, timezone, timedelta
from email.message import EmailMessage

from fastapi.security import HTTPBearer
from jose import jwt
from fastapi import Header
from typing import Annotated

from fastapi import HTTPException
from fastapi import Depends
from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from email_validator import validate_email, EmailNotValidError
from sqlalchemy.orm import selectinload

from app import db
from app.db import User
from app.emails import send_mail, verify_email, send_forgotten_mail
from app.hasher import Hasher
from app.schemas import UserCreate, UserLogin, EmailSchema, UserVerify, UserChangePassword, UserForgottenPassword
from pydantic import ValidationError, EmailStr
from fastapi import Request
router = APIRouter()
hasher = Hasher()
security_scheme = HTTPBearer(auto_error=False)

SECRET_KEY = "a-string-secret-at-least-256-bits-long"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 5

# --- Utility Functions ---

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(request: Request):
    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    token = authorization.split(" ")[1]
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    request.state.user = payload
    return payload

@router.post("/register",tags=["users"])
async def register(request:UserCreate, session:AsyncSession=Depends(db.get_async_session)):
    try:

        username_search = await session.execute(select(User).where(User.username == request.username))
        user_with_username_taken = username_search.scalars().first()
        email_search = await session.execute(select(User).where(User.email == request.email))
        user_with_email_taken = email_search.scalars().first()

        if user_with_email_taken:
            raise HTTPException(status_code=400,detail="There is already an account with this email")
        if user_with_username_taken:
            raise HTTPException(status_code=400,detail="Username already exists")
        if request.username is None or request.username=="" or request.username.isspace():
            raise HTTPException(status_code=400,detail="Username is required")
        if request.password  is None or request.password=="" or  request.password.isspace():
            raise HTTPException(status_code=400,detail="Password is required")
        if request.email is None or request.email=="" or request.email.isspace():
            raise HTTPException(status_code=400,detail="Email is required")

        user = User(

            username=request.username,
            email=request.email,
            password_hash=hasher.hash_password(request.password),
            created_at=datetime.now(),
            modified_at=datetime.now(),
            user_role="USER",
            is_verified = False,
            verification_code=random.Random(int(time.time())).randint(111111, 999999),

        )

        if await verify_email(request.email) == "valid":
            email_message=EmailSchema(

                email=[request.email]
            )

            await send_mail(email_message,user.verification_code)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user
        else:
            raise HTTPException(status_code=400,detail="Invalid or non-existing email address.")
    except HTTPException as e:
        raise HTTPException(status_code=400,detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))

@router.post("/login",tags=["users"])
async def login(request:UserLogin, session:AsyncSession=Depends(db.get_async_session)):
    try:
        search=await session.execute(select(User).where(User.username==request.username))
        user=search.scalars().first()
        if user is None:
            raise HTTPException(status_code=400,detail="Incorrect username or password")
        if not hasher.verify_password(plain_password=request.password, hashed_password=user.password_hash):
            raise HTTPException(status_code=400,detail="Incorrect username or password")
        if user.is_verified==False:
            raise HTTPException(status_code=400,detail="User is not verified")
        token = create_access_token(data={"sub": user.username})
        return {"access_token": token, "token_type": "bearer"}
    except HTTPException as e:
        raise HTTPException(status_code=400,detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))


@router.get("/getcurrentuser", dependencies=[Depends(verify_token)],tags=["users"])
async def get_current_user(request: Request):
    user = request.state.user
    return {"username": user.get("sub")}

@router.patch("/verify_user",tags=["users"])
async def verify_user(request:UserVerify,session:AsyncSession=Depends(db.get_async_session)):
    username_search = await session.execute(select(User).where(User.username == request.username))
    user = username_search.scalars().first()
    try:
        if user.verification_code == request.verification_code:
            user.is_verified = True
            user.verification_code = 0
            user.modified_at = datetime.now()
            await session.commit()
            await session.refresh(user)
            return user
        else:
            raise HTTPException(status_code=400,detail="Incorrect verification code")
    except HTTPException as e:
        raise HTTPException(status_code=400,detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))

@router.patch("/changepassword",dependencies=[Depends(verify_token)],tags=["users"])
async def change_password(request:UserChangePassword,session:AsyncSession=Depends(db.get_async_session)):
    try:
        if request.old_password =="" or request.old_password.isspace():
            raise HTTPException(status_code=400,detail="Old password field is required")
        if request.new_password =="" or request.new_password.isspace():
            raise HTTPException(status_code=400,detail="New password field is required")
        if request.confirm_new_password =="" or request.confirm_new_password.isspace():
            raise HTTPException(status_code=400,detail="Confirm password field is required")
        if request.old_password == request.new_password:
            raise HTTPException(status_code=400,detail="Old password and new password are the same")
        if request.confirm_new_password != request.new_password:
            raise HTTPException(status_code=400,detail="Confirm password does not match with new password")
        username_search = await session.execute(select(User).where(User.username == request.username))
        user = username_search.scalars().first()
        if user is None:
            raise HTTPException(status_code=400,detail="Incorrect username or old password")
        if not hasher.verify_password(plain_password=request.old_password, hashed_password=user.password_hash):
            raise HTTPException(status_code=400,detail="Incorrect username or old password")
        user.password_hash = hasher.hash_password(request.confirm_new_password)
        user.modified_at = datetime.now()
        await session.commit()
        await session.refresh(user)
        return user
    except HTTPException as e:
        raise HTTPException(status_code=400,detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))

@router.post("/send_forgotten_password_email",tags=["users"])
async def send_forgotten_password_email(email:str,session:AsyncSession=Depends(db.get_async_session)):
    try:
        if email == "" or email.isspace():
            raise HTTPException(status_code=400,detail="Email field is required")
        if await verify_email(email)!="valid":
            raise HTTPException(status_code=400,detail="Incorrect or non-existent email address")

        email_search = await session.execute(select(User).where(User.email == email))
        user = email_search.scalars().first()

        if user is None:
            raise HTTPException(status_code=404,detail="No user found with this email address")

        user.verification_code = random.Random(int(time.time())).randint(111111, 999999)
        user.modified_at = datetime.now()

        email_message=EmailSchema(

            email=[email]

        )
        await send_forgotten_mail(email_message,user.verification_code)
        await session.commit()
        await session.refresh(user)
        return {"message":"Email sent successfully!"}

    except HTTPException as e:
        raise HTTPException(status_code=400,detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))

@router.patch("/forgotten_password_change",tags=["users"])
async def forgotten_password_change(request:UserForgottenPassword,session:AsyncSession=Depends(db.get_async_session)):
   try:
        if request.email =="" or request.email.isspace():
            raise HTTPException(status_code=400,detail="Email field is required")
        if request.verification_code =="" or request.verification_code==0:
            raise HTTPException(status_code=400,detail="Verification code field is required")
        if request.new_password =="" or request.new_password.isspace():
            raise HTTPException(status_code=400,detail="New password field is required")
        if request.confirm_new_password =="" or request.confirm_new_password.isspace():
            raise HTTPException(status_code=400,detail="Confirm password field is required")
        if request.new_password!=request.confirm_new_password:
            raise HTTPException(status_code=400,detail="Passwords do not match")
        if await verify_email(request.email)!="valid":
            raise HTTPException(status_code=400,detail="Incorrect or non-existent email address")

        email_search = await session.execute(select(User).where(User.email == request.email))
        user = email_search.scalars().first()

        if user is None:
            raise HTTPException(status_code=404,detail="No user found with this email address")
        if user.verification_code != request.verification_code:
            raise HTTPException(status_code=400,detail="Incorrect verification code")

        user.verification_code = 0
        user.password_hash = hasher.hash_password(request.confirm_new_password)
        user.modified_at = datetime.now()
        await session.commit()
        await session.refresh(user)
        return user
   except HTTPException as e:
        raise HTTPException(status_code=e.status_code,detail=str(e))
   except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))

@router.get("/user/prompts",dependencies=[Depends(verify_token)],tags=["users"])
async def get_prompts_for_user(session:AsyncSession=Depends(db.get_async_session),current_user:dict=Depends(get_current_user)):
    username_search = await session.execute(select(User).where(User.username==current_user["username"]).options(selectinload(User.prompts)))
    user = username_search.scalars().first()
    if user is None:
        raise HTTPException(status_code=404,detail="No user found with this username")
    return user.prompts

@router.get("/user/report-requests",dependencies=[Depends(verify_token)],tags=["users"])
async def get_prompts_for_user(session:AsyncSession=Depends(db.get_async_session),current_user:dict=Depends(get_current_user)):
    username_search = await session.execute(select(User).where(User.username==current_user["username"]).options(selectinload(User.report_requests)))
    user = username_search.scalars().first()
    if user is None:
        raise HTTPException(status_code=404,detail="No user found with this username")
    return user.report_requests