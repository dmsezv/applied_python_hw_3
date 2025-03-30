from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Optional
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Link schemas
class LinkBase(BaseModel):
    original_url: HttpUrl
    custom_alias: Optional[str] = None
    expires_at: Optional[datetime] = None

class LinkCreate(LinkBase):
    pass

class Link(LinkBase):
    id: int
    short_code: str
    user_id: Optional[int]
    created_at: datetime
    clicks: int
    last_accessed_at: Optional[datetime]

    class Config:
        from_attributes = True

# Link statistics schema
class LinkStats(BaseModel):
    original_url: str
    short_code: str
    created_at: datetime
    clicks: int
    last_accessed_at: Optional[datetime]
    expires_at: Optional[datetime] 