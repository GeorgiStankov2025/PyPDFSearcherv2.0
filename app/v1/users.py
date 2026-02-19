
from datetime import datetime, timezone, timedelta
from fastapi import Header
from typing import Annotated

from fastapi import HTTPException
from fastapi import Depends
from fastapi import APIRouter
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jose import jwt

from app import db
from app.db import User
from app.hasher import Hasher
from app.schemas import UserCreate, UserLogin
from pydantic import ValidationError
from fastapi import Request
router = APIRouter()
hasher = Hasher()


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
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

    authorization= request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        request.state.user = payload
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

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
        if request.password  is None or request.username=="" or  request.password.isspace():
            raise HTTPException(status_code=400,detail="Password is required")
        if request.email is None or request.username=="" or request.email.isspace():
            raise HTTPException(status_code=400,detail="Email is required")

        user = User(

            username=request.username,
            email=request.email,
            password_hash=hasher.hash_password(request.password),
            created_at=datetime.now(),
            modified_at=datetime.now(),
            is_verified = False

        )

        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
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
        token = create_access_token(data={"sub": user.username})
        return {"access_token": token, "token_type": "bearer"}
    except HTTPException as e:
        raise HTTPException(status_code=400,detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))


@router.get("/getcurrentuser", dependencies=[Depends(verify_token)],tags=["users"])
async def get_current_user(request: Request):
    # Retrieve the data we tucked away in the 'state'
    user = request.state.user
    return {"username": user.get("sub")}