from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.schemas.question import QuestionCreate, QuestionResponse, FollowUpRequest
from app.api.dependencies import get_current_user
from app.schemas.user import UserResponse

router = APIRouter()


@router.post("/", response_model=QuestionResponse)
async def create_question(
    question_in: QuestionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """创建题目（上传图片）"""
    # TODO: 实现题目创建逻辑
    # 1. 保存图片
    # 2. 调用 AI 识别题目
    # 3. 返回题目信息
    raise HTTPException(status_code=501, detail="功能开发中")


@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """获取题目详情"""
    # TODO: 实现获取题目逻辑
    raise HTTPException(status_code=501, detail="功能开发中")


@router.post("/{question_id}/follow-up")
async def follow_up_question(
    question_id: int,
    request: FollowUpRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """追问题目"""
    # TODO: 实现追问逻辑
    # 1. 检查追问次数
    # 2. 调用 AI 回答
    # 3. 增加追问计数
    raise HTTPException(status_code=501, detail="功能开发中")
