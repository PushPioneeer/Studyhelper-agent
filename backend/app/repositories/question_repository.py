"""
题目数据访问层
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from app.models.question import Question, WrongQuestion


class QuestionRepository:
    """题目 Repository"""

    async def create(
        self,
        db: AsyncSession,
        user_id: int,
        image_url: str,
        question_text: Optional[str] = None,
        question_type: Optional[str] = None,
        subject: Optional[str] = None,
        difficulty: Optional[str] = None,
        analysis: Optional[str] = None,
        knowledge_points: Optional[Dict] = None,
    ) -> Question:
        """
        创建题目

        Args:
            db: 数据库会话
            user_id: 用户 ID
            image_url: 图片 URL
            question_text: 题目文本
            question_type: 题目类型
            subject: 科目
            difficulty: 难度
            analysis: 解析
            knowledge_points: 知识点

        Returns:
            创建的题目对象
        """
        question = Question(
            user_id=user_id,
            image_url=image_url,
            question_text=question_text,
            question_type=question_type,
            subject=subject,
            difficulty=difficulty,
            analysis=analysis,
            knowledge_points=knowledge_points,
        )
        db.add(question)
        await db.flush()
        await db.refresh(question)
        return question

    async def get_by_id(
        self,
        db: AsyncSession,
        question_id: int,
        user_id: Optional[int] = None
    ) -> Optional[Question]:
        """
        根据 ID 获取题目

        Args:
            db: 数据库会话
            question_id: 题目 ID
            user_id: 用户 ID（可选，用于权限验证）

        Returns:
            题目对象，不存在则返回 None
        """
        query = select(Question).where(Question.id == question_id)

        if user_id:
            query = query.where(Question.user_id == user_id)

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_list(
        self,
        db: AsyncSession,
        user_id: int,
        subject: Optional[str] = None,
        question_type: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Question]:
        """
        获取题目列表

        Args:
            db: 数据库会话
            user_id: 用户 ID
            subject: 科目筛选
            question_type: 题目类型筛选
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            题目列表
        """
        query = select(Question).where(Question.user_id == user_id)

        if subject:
            query = query.where(Question.subject == subject)
        if question_type:
            query = query.where(Question.question_type == question_type)

        query = query.order_by(Question.created_at.desc())
        query = query.offset(offset).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def update_analysis(
        self,
        db: AsyncSession,
        question_id: int,
        question_text: str,
        analysis: str,
        knowledge_points: List[Dict],
        question_type: Optional[str] = None,
        subject: Optional[str] = None,
        difficulty: Optional[str] = None,
    ) -> bool:
        """
        更新题目解析

        Args:
            db: 数据库会话
            question_id: 题目 ID
            question_text: 题目文本
            analysis: 解析
            knowledge_points: 知识点列表
            question_type: 题目类型
            subject: 科目
            difficulty: 难度

        Returns:
            是否更新成功
        """
        stmt = update(Question).where(Question.id == question_id).values(
            question_text=question_text,
            analysis=analysis,
            knowledge_points=knowledge_points,
            question_type=question_type,
            subject=subject,
            difficulty=difficulty,
        )
        await db.execute(stmt)
        await db.commit()
        return True

    async def increment_follow_up_count(
        self,
        db: AsyncSession,
        question_id: int
    ) -> Optional[int]:
        """
        增加追问次数

        Args:
            db: 数据库会话
            question_id: 题目 ID

        Returns:
            新的追问次数，失败返回 None
        """
        question = await self.get_by_id(db, question_id)
        if not question:
            return None

        question.follow_up_count += 1
        await db.commit()
        await db.refresh(question)
        return question.follow_up_count

    async def get_follow_up_count(
        self,
        db: AsyncSession,
        question_id: int
    ) -> Optional[int]:
        """
        获取当前追问次数

        Args:
            db: 数据库会话
            question_id: 题目 ID

        Returns:
            追问次数，失败返回 None
        """
        question = await self.get_by_id(db, question_id)
        if not question:
            return None
        return question.follow_up_count

    async def delete(
        self,
        db: AsyncSession,
        question_id: int,
        user_id: Optional[int] = None
    ) -> bool:
        """
        删除题目

        Args:
            db: 数据库会话
            question_id: 题目 ID
            user_id: 用户 ID（可选）

        Returns:
            是否删除成功
        """
        query = delete(Question).where(Question.id == question_id)
        if user_id:
            query = query.where(Question.user_id == user_id)

        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0


class WrongQuestionRepository:
    """错题 Repository"""

    async def create(
        self,
        db: AsyncSession,
        user_id: int,
        question_id: int,
        error_reason: Optional[str] = None,
    ) -> WrongQuestion:
        """
        创建错题记录

        Args:
            db: 数据库会话
            user_id: 用户 ID
            question_id: 题目 ID
            error_reason: 错误原因

        Returns:
            创建的错题对象
        """
        wrong_question = WrongQuestion(
            user_id=user_id,
            question_id=question_id,
            error_reason=error_reason,
        )
        db.add(wrong_question)
        await db.flush()
        await db.refresh(wrong_question)
        return wrong_question

    async def get_by_user(
        self,
        db: AsyncSession,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
    ) -> List[WrongQuestion]:
        """
        获取用户的错题列表

        Args:
            db: 数据库会话
            user_id: 用户 ID
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            错题列表
        """
        query = select(WrongQuestion).where(WrongQuestion.user_id == user_id)
        query = query.order_by(WrongQuestion.created_at.desc())
        query = query.offset(offset).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_question_id(
        self,
        db: AsyncSession,
        user_id: int,
        question_id: int
    ) -> Optional[WrongQuestion]:
        """
        根据题目 ID 获取错题记录

        Args:
            db: 数据库会话
            user_id: 用户 ID
            question_id: 题目 ID

        Returns:
            错题记录，不存在返回 None
        """
        query = select(WrongQuestion).where(
            WrongQuestion.user_id == user_id,
            WrongQuestion.question_id == question_id
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def mark_mastered(
        self,
        db: AsyncSession,
        wrong_question_id: int,
        user_id: int
    ) -> bool:
        """
        标记为已掌握

        Args:
            db: 数据库会话
            wrong_question_id: 错题 ID
            user_id: 用户 ID

        Returns:
            是否操作成功
        """
        stmt = update(WrongQuestion).where(
            WrongQuestion.id == wrong_question_id,
            WrongQuestion.user_id == user_id
        ).values(is_mastered=True)
        await db.execute(stmt)
        await db.commit()
        return True

    async def delete(
        self,
        db: AsyncSession,
        wrong_question_id: int,
        user_id: int
    ) -> bool:
        """
        删除错题记录

        Args:
            db: 数据库会话
            wrong_question_id: 错题 ID
            user_id: 用户 ID

        Returns:
            是否删除成功
        """
        stmt = delete(WrongQuestion).where(
            WrongQuestion.id == wrong_question_id,
            WrongQuestion.user_id == user_id
        )
        await db.execute(stmt)
        await db.commit()
        return True


# 全局单例
question_repository = QuestionRepository()
wrong_question_repository = WrongQuestionRepository()
