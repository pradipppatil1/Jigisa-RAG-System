from pydantic import BaseModel, EmailStr
from typing import List, Optional


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str
    department: str


class CurrentUser(BaseModel):
    user_id: int
    username: str
    role: str
    department: Optional[str]
    collections: List[str]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: CurrentUser
