"""
追问记录数据访问层
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.follow_up import FollowUp


class FollowUpRepository:
    """追问记录 Repository"""

    async def create(
        self,
        db: AsyncSession,
        question_id: int,
        user_id: int,
        message: str,
        response: str,
        message_type: Optional[str] = None,
        parent_id: Optional[int] = None,
        conversation_order: Optional[int] = None,
        ip_address: Optional[str] = None,
    ) -> FollowUp:
        """创建追问记录"""
        follow_up = FollowUp(
            question_id=question_id,
            user_id=user_id,
            message=message,
            response=response,
            message_type=message_type,
            parent_id=parent_id,
            conversation_order=conversation_order,
            ip_address=ip_address,
        )
        db.add(follow_up)
        await db.flush()
        await db.refresh(follow_up)
        return follow_up

    async def get_by_id(
        self,
        db: AsyncSession,
        follow_up_id: int,
        user_id: int
    ) -> Optional[FollowUp]:
        """根据 ID 获取追问记录"""
        result = await db.execute(
            select(FollowUp).where(
                FollowUp.id == follow_up_id,
                FollowUp.user_id == user_id,
                FollowUp.deleted_at.is_(None)
            )
        )
        return result.scalars().first()

    async def get_by_question_id(
        self,
        db: AsyncSession,
        question_id: int,
        user_id: int,
        limit: int = 100
    ) -> List[FollowUp]:
        """根据题目 ID 获取追问记录列表"""
        result = await db.execute(
            select(FollowUp)
            .where(
                FollowUp.question_id == question_id,
                FollowUp.user_id == user_id,
                FollowUp.deleted_at.is_(None)
            )
            .order_by(FollowUp.conversation_order.asc())
            .limit(limit)
        )
        return result.scalars().all()

    async def count_by_question_id(
        self,
        db: AsyncSession,
        question_id: int,
        user_id: int
    ) -> int:
        """统计某道题目的追问次数"""
        result = await db.execute(
            select(func.count(FollowUp.id)).where(
                FollowUp.question_id == question_id,
                FollowUp.user_id == user_id,
                FollowUp.deleted_at.is_(None)
            )
        )
        return result.scalar() or 0

    async def get_conversation_tree(
        self,
        db: AsyncSession,
        question_id: int,
        user_id: int
    ) -> List[FollowUp]:
        """获取对话树（按顺序）"""
        return await self.get_by_question_id(db, question_id, user_id)


# 全局单例
follow_up_repository = FollowUpRepository()
