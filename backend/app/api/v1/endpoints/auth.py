from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.user import LoginRequest, RegisterRequest, Token, UserResponse
from app.services.user_service import user_service

router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register(user_in: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """用户注册"""
    try:
        user = await user_service.register(db, user_in)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """用户登录"""
    try:
        result = await user_service.login(
            db,
            login_data.phone,
            login_data.password
        )
        return Token(**result)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/refresh", response_model=dict)
async def refresh_token(refresh_token: str):
    """刷新访问令牌"""
    try:
        result = await user_service.refresh_token(refresh_token)
        return result
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
