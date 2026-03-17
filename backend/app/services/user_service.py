from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.repositories.user_repository import user_repository
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token
from app.core.config import settings


class UserService:
    """用户业务逻辑层"""

    async def register(
        self,
        db: AsyncSession,
        user_in: UserCreate
    ) -> UserResponse:
        """用户注册"""
        # 检查手机号是否已存在
        existing_user = await user_repository.get_by_phone(db, user_in.phone)
        if existing_user:
            raise ValueError("手机号已注册")

        # 加密密码
        hashed_password = get_password_hash(user_in.password)

        # 创建用户（直接传入加密后的密码）
        user_dict = user_in.model_dump()
        user_dict["hashed_password"] = hashed_password
        del user_dict["password"]
        
        # 使用 repository 创建用户
        db_obj = User(
            phone=user_in.phone,
            email=user_in.email,
            nickname=user_in.nickname,
            hashed_password=hashed_password,
        )
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        
        return UserResponse.model_validate(db_obj)

    async def login(
        self,
        db: AsyncSession,
        phone: str,
        password: str
    ) -> dict:
        """用户登录"""
        # 查找用户
        user = await user_repository.get_by_phone(db, phone)
        if not user:
            raise ValueError("用户不存在")

        # 验证密码
        if not verify_password(password, user.hashed_password):
            raise ValueError("密码错误")

        # 检查用户状态
        if not user.is_active:
            raise ValueError("账号已被禁用")

        # 生成令牌
        access_token = create_access_token(
            data={"sub": user.id, "phone": user.phone}
        )
        refresh_token = create_refresh_token(
            data={"sub": user.id}
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": UserResponse.model_validate(user)
        }

    async def refresh_token(self, refresh_token: str) -> dict:
        """刷新令牌"""
        from app.core.security import decode_token
        from datetime import datetime

        payload = decode_token(refresh_token)
        if not payload or payload.get("exp") < datetime.utcnow().timestamp():
            raise ValueError("刷新令牌已过期")

        user_id = payload.get("sub")
        user = await user_repository.get(None, user_id)  # type: ignore
        if not user:
            raise ValueError("用户不存在")

        # 生成新的访问令牌
        access_token = create_access_token(
            data={"sub": user.id, "phone": user.phone}
        )

        return {
            "access_token": access_token,
            "token_type": "bearer"
        }

    async def get_user(self, db: AsyncSession, user_id: int) -> UserResponse:
        """获取用户信息"""
        user = await user_repository.get(db, user_id)
        if not user:
            raise ValueError("用户不存在")
        return UserResponse.model_validate(user)

    async def update_user(
        self,
        db: AsyncSession,
        user_id: int,
        user_in: UserUpdate
    ) -> UserResponse:
        """更新用户信息"""
        user = await user_repository.get(db, user_id)
        if not user:
            raise ValueError("用户不存在")

        # 检查邮箱是否已被其他用户使用
        if user_in.email:
            existing_user = await user_repository.get_by_email(db, user_in.email)
            if existing_user and existing_user.id != user_id:
                raise ValueError("邮箱已被使用")

        updated_user = await user_repository.update(db, user, user_in)
        return UserResponse.model_validate(updated_user)


# 单例
user_service = UserService()
