from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime


class QuestionBase(BaseModel):
    """题目基础 Schema"""
    image_url: str = Field(..., description="题目图片 URL")


class QuestionCreate(QuestionBase):
    """创建题目 Schema"""
    pass


class QuestionUpdate(BaseModel):
    """更新题目 Schema"""
    question_text: Optional[str] = None
    question_type: Optional[str] = None
    subject: Optional[str] = None
    difficulty: Optional[str] = None
    analysis: Optional[str] = None
    knowledge_points: Optional[list] = None
    is_wrong_question: Optional[bool] = None


class QuestionResponse(QuestionBase):
    """题目响应 Schema"""
    id: int
    user_id: int
    question_text: Optional[str]
    question_type: Optional[str]
    subject: Optional[str]
    difficulty: Optional[str]
    analysis: Optional[str]
    knowledge_points: Optional[list]
    follow_up_count: int
    max_follow_up: int
    is_wrong_question: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class QuestionAnalysisRequest(BaseModel):
    """题目分析请求"""
    question_id: int
    image_url: str


class FollowUpRequest(BaseModel):
    """追问请求"""
    question_id: int
    question: str = Field(..., max_length=500, description="追问内容")


class WrongQuestionBase(BaseModel):
    """错题基础 Schema"""
    question_id: int
    error_reason: Optional[str] = Field(None, max_length=200)


class WrongQuestionCreate(WrongQuestionBase):
    """创建错题 Schema"""
    pass


class WrongQuestionResponse(WrongQuestionBase):
    """错题响应 Schema"""
    id: int
    user_id: int
    review_count: int
    last_review_at: Optional[datetime]
    is_mastered: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
