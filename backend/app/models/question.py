from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Question(Base):
    """题目模型"""

    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    image_url = Column(String(500), nullable=False)
    question_text = Column(Text, nullable=True)  # AI 识别后的题目文本
    question_type = Column(String(50), nullable=True)  # 题目类型
    subject = Column(String(50), nullable=True)  # 科目
    difficulty = Column(String(20), nullable=True)  # 难度
    analysis = Column(Text, nullable=True)  # 解析
    knowledge_points = Column(JSON, nullable=True)  # 知识点列表
    follow_up_count = Column(Integer, default=0)  # 追问次数
    max_follow_up = Column(Integer, default=10)  # 最大追问次数
    is_wrong_question = Column(Boolean, default=False)  # 是否错题
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关联关系
    # user = relationship("User", back_populates="questions")
    # answers = relationship("Answer", back_populates="question")


class WrongQuestion(Base):
    """错题集模型"""

    __tablename__ = "wrong_questions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    error_reason = Column(String(200), nullable=True)  # 错误原因
    review_count = Column(Integer, default=0)  # 复习次数
    last_review_at = Column(DateTime(timezone=True), nullable=True)
    is_mastered = Column(Boolean, default=False)  # 是否已掌握
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关联关系
    # user = relationship("User", back_populates="wrong_questions")
    # question = relationship("Question", back_populates="wrong_question")
