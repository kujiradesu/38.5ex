from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None

class User(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        orm_mode = True

class ItemCreate(BaseModel):
    name: str

class Item(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True
