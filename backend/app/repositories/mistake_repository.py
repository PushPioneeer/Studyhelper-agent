"""
错题集数据访问层
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from app.models.mistake import Mistake, MistakeReview
from datetime import datetime


class MistakeRepository:
    """错题集 Repository"""

    async def create(
        self,
        db: AsyncSession,
        user_id: int,
        question_id: int,
        original_text: Optional[str] = None,
        images: Optional[dict] = None,
        subject: Optional[str] = None,
        question_type: Optional[str] = None,
        correct_answer: Optional[str] = None,
        user_answer: Optional[str] = None,
        solution: Optional[str] = None,
        knowledge_points: Optional[list] = None,
        error_type: Optional[str] = None,
        error_analysis: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        source_type: Optional[str] = None,
        source_id: Optional[int] = None,
    ) -> Mistake:
        """创建错题记录"""
        mistake = Mistake(
            user_id=user_id,
            question_id=question_id,
            original_text=original_text,
            images=images,
            subject=subject,
            question_type=question_type,
            correct_answer=correct_answer,
            user_answer=user_answer,
            solution=solution,
            knowledge_points=knowledge_points,
            error_type=error_type,
            error_analysis=error_analysis,
            difficulty_level=difficulty_level,
            source_type=source_type,
            source_id=source_id,
        )
        db.add(mistake)
        await db.flush()
        await db.refresh(mistake)
        return mistake

    async def get_by_id(
        self,
        db: AsyncSession,
        mistake_id: int,
        user_id: int
    ) -> Optional[Mistake]:
        """根据 ID 获取错题"""
        result = await db.execute(
            select(Mistake).where(
                Mistake.id == mistake_id,
                Mistake.user_id == user_id,
                Mistake.deleted_at.is_(None)
            )
        )
        return result.scalars().first()

    async def get_list(
        self,
        db: AsyncSession,
        user_id: int,
        subject: Optional[str] = None,
        status: Optional[str] = None,
        error_type: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Mistake]:
        """获取错题列表"""
        query = select(Mistake).where(
            Mistake.user_id == user_id,
            Mistake.deleted_at.is_(None)
        )
        
        if subject:
            query = query.where(Mistake.subject == subject)
        if status:
            query = query.where(Mistake.status == status)
        if error_type:
            query = query.where(Mistake.error_type == error_type)
        
        query = query.order_by(Mistake.created_at.desc()).offset(offset).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()

    async def update(
        self,
        db: AsyncSession,
        mistake_id: int,
        user_id: int,
        **kwargs
    ) -> Optional[Mistake]:
        """更新错题"""
        mistake = await self.get_by_id(db, mistake_id, user_id)
        if not mistake:
            return None
        
        for key, value in kwargs.items():
            if hasattr(mistake, key):
                setattr(mistake, key, value)
        
        await db.flush()
        await db.refresh(mistake)
        return mistake

    async def update_mastery(
        self,
        db: AsyncSession,
        mistake_id: int,
        user_id: int,
        mastery_level: int
    ) -> Optional[Mistake]:
        """更新掌握程度"""
        return await self.update(db, mistake_id, user_id, mastery_level=mastery_level)

    async def update_status(
        self,
        db: AsyncSession,
        mistake_id: int,
        user_id: int,
        status: str
    ) -> Optional[Mistake]:
        """更新状态"""
        return await self.update(db, mistake_id, user_id, status=status)

    async def increment_review_count(
        self,
        db: AsyncSession,
        mistake_id: int,
        user_id: int
    ) -> Optional[Mistake]:
        """增加复习次数"""
        mistake = await self.get_by_id(db, mistake_id, user_id)
        if not mistake:
            return None
        
        mistake.review_count += 1
        mistake.last_reviewed_at = datetime.utcnow()
        
        await db.flush()
        await db.refresh(mistake)
        return mistake

    async def soft_delete(
        self,
        db: AsyncSession,
        mistake_id: int,
        user_id: int
    ) -> bool:
        """软删除错题"""
        mistake = await self.get_by_id(db, mistake_id, user_id)
        if not mistake:
            return False
        
        mistake.deleted_at = datetime.utcnow()
        await db.flush()
        return True

    async def add_review_record(
        self,
        db: AsyncSession,
        mistake_id: int,
        user_id: int,
        review_result: Optional[str] = None,
        time_spent: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> MistakeReview:
        """添加复习记录"""
        review = MistakeReview(
            mistake_id=mistake_id,
            user_id=user_id,
            review_result=review_result,
            time_spent=time_spent,
            notes=notes,
        )
        db.add(review)
        await db.flush()
        await db.refresh(review)
        return review

    async def get_by_question_id(
        self,
        db: AsyncSession,
        question_id: int,
        user_id: int
    ) -> Optional[Mistake]:
        """根据题目 ID 获取错题（检查是否已经是错题）"""
        result = await db.execute(
            select(Mistake).where(
                Mistake.question_id == question_id,
                Mistake.user_id == user_id,
                Mistake.deleted_at.is_(None)
            )
        )
        return result.scalars().first()


# 全局单例
mistake_repository = MistakeRepository()
