from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.schemas.user import UserResponse

router = APIRouter()


@router.post("/analyze")
async def analyze_question(
    image_url: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """分析题目图片"""
    # TODO: 实现 AI 题目分析
    # 1. 调用硅基流动 API
    # 2. 识别题目内容
    # 3. 返回分析结果
    raise HTTPException(status_code=501, detail="功能开发中")


@router.post("/solve")
async def solve_question(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """解答题目"""
    # TODO: 实现 AI 题目解答
    # 1. 获取题目信息
    # 2. 调用 AI 解答
    # 3. 返回解答过程
    raise HTTPException(status_code=501, detail="功能开发中")
