from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserRepository:
    """用户数据访问层"""

    async def get(self, db: AsyncSession, user_id: int) -> Optional[User]:
        """根据 ID 获取用户"""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalars().first()

    async def get_by_phone(self, db: AsyncSession, phone: str) -> Optional[User]:
        """根据手机号获取用户"""
        result = await db.execute(
            select(User).where(User.phone == phone)
        )
        return result.scalars().first()

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        result = await db.execute(
            select(User).where(User.email == email)
        )
        return result.scalars().first()

    async def get_multi(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """获取多个用户"""
        result = await db.execute(
            select(User).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def create(self, db: AsyncSession, user_in: UserCreate) -> User:
        """创建用户"""
        db_obj = User(
            phone=user_in.phone,
            email=user_in.email,
            nickname=user_in.nickname,
            hashed_password=user_in.password,  # 注意：密码应该在 service 层加密
        )
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        db_obj: User,
        obj_in: UserUpdate
    ) -> User:
        """更新用户"""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, user_id: int) -> bool:
        """删除用户"""
        user = await self.get(db, user_id)
        if user:
            await db.delete(user)
            return True
        return False

    async def is_active(self, db: AsyncSession, user_id: int) -> bool:
        """检查用户是否激活"""
        user = await self.get(db, user_id)
        return user.is_active if user else False


# 单例
user_repository = UserRepository()
