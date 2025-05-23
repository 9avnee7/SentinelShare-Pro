# app/schemas.py
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "user"

class UserInfo(BaseModel):
    email: EmailStr
    role: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class RegisterResponse(BaseModel):
    refresh_token: str
    access_token: str
    totp_uri: str
    user_info: UserInfo
    
class LoginResponse(BaseModel):
    refresh_token: str
    access_token: str
    user_info: UserInfo




class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str

