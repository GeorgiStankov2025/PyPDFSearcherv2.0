from datetime import datetime
from enum import Enum
from typing import Optional, List
from fastapi_mail import FastMail,MessageSchema,ConnectionConfig
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    username:str
    password:str
    email:str

class UserLogin(BaseModel):
    username:str
    password:str

class UserVerify(BaseModel):
    username:str
    verification_code:int

class UserChangePassword(BaseModel):
    username:str
    old_password:str
    new_password:str
    confirm_new_password:str

class UserForgottenPassword(BaseModel):
    email:str
    new_password:str
    confirm_new_password:str
    verification_code:int

class UserRole(Enum):
    ADMIN = "ADMIN"
    USER = "USER"

class PromptCreate(BaseModel):
    message:str

class EmailSchema(BaseModel):
    email:List[EmailStr]

class CreateReport(BaseModel):
    message:str

class SessionData(BaseModel):
    username:str
    filename:str
    created_at:datetime