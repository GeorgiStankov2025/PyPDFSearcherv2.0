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

class PromptCreate(BaseModel):
    message:str

class EmailSchema(BaseModel):
    email:List[EmailStr]
