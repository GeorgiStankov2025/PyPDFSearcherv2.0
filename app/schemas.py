from typing import Optional

from pydantic import BaseModel

class UserCreate(BaseModel):
    username:str
    password:str
    email:str

class UserLogin(BaseModel):
    username:str
    password:str

class PromptCreate(BaseModel):
    message:str
