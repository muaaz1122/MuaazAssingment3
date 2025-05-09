from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# User Schema for Registration
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

# User Response Schema
class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True  # Pydantic V2 update

# Login Schema (Added)
class LoginRequest(BaseModel):
    email: str
    password: str

# Task Schema for Creation
class TaskCreate(BaseModel):
    title: str
    description: str
    priority: Optional[int] = 1
    deadline: Optional[datetime] = None

# Task Response Schema
class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    priority: int
    deadline: Optional[datetime]
    is_completed: bool
    owner_id: int

    class Config:
        from_attributes = True
