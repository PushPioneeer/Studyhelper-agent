from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """用户基础 Schema"""
    phone: str = Field(..., min_length=11, max_length=11, description="手机号")
    email: Optional[EmailStr] = None
    nickname: Optional[str] = Field(None, max_length=50, description="昵称")


class UserCreate(UserBase):
    """创建用户 Schema"""
    password: str = Field(..., min_length=6, max_length=20, description="密码")


class UserUpdate(BaseModel):
    """更新用户 Schema"""
    nickname: Optional[str] = Field(None, max_length=50)
    avatar_url: Optional[str] = Field(None, max_length=500)
    email: Optional[EmailStr] = None


class UserResponse(UserBase):
    """用户响应 Schema"""
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    """令牌响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """令牌数据"""
    user_id: Optional[int] = None
    phone: Optional[str] = None


class LoginRequest(BaseModel):
    """登录请求"""
    phone: str = Field(..., min_length=11, max_length=11)
    password: str = Field(..., min_length=6, max_length=20)


class RegisterRequest(UserCreate):
    """注册请求"""
    pass
