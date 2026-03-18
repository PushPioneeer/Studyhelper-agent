from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Mistake(Base):
    """错题模型"""

    __tablename__ = "mistakes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    
    # 题目内容
    original_text = Column(Text, nullable=True)  # 题目文本
    images = Column(JSON, nullable=True)  # 题目图片
    subject = Column(String(50), nullable=True)  # 学科
    question_type = Column(String(20), nullable=True)  # 题型
    
    # 答案信息
    correct_answer = Column(Text, nullable=True)  # 正确答案
    user_answer = Column(Text, nullable=True)  # 用户答案
    solution = Column(Text, nullable=True)  # 解析（解题过程）
    
    # 知识点
    knowledge_points = Column(JSON, nullable=True)  # 知识点列表
    
    # 错误分析
    error_type = Column(String(50), nullable=True)  # 概念不清，计算错误，理解偏差，粗心
    error_analysis = Column(Text, nullable=True)  # 错误分析
    difficulty_level = Column(String(20), nullable=True)  # 简单，中等，困难
    
    # 状态
    status = Column(String(20), default='new')  # new, reviewing, mastered, archived
    mastery_level = Column(Integer, default=0)  # 掌握程度 0-100
    review_count = Column(Integer, default=0)  # 复习次数
    last_reviewed_at = Column(DateTime(timezone=True), nullable=True)
    
    # 来源
    source_type = Column(String(20), nullable=True)  # photo, practice, exam
    source_id = Column(Integer, nullable=True)  # 来源 ID
    
    # 自定义
    tags = Column(JSON, nullable=True)  # 自定义标签
    notes = Column(Text, nullable=True)  # 用户备注
    
    # 元数据
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 软删除
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # 关联关系
    # user = relationship("User", back_populates="mistakes")
    # question = relationship("Question", back_populates="mistakes")


class MistakeReview(Base):
    """错题复习记录模型"""

    __tablename__ = "mistake_reviews"

    id = Column(Integer, primary_key=True, index=True)
    mistake_id = Column(Integer, ForeignKey("mistakes.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 复习信息
    review_result = Column(String(20), nullable=True)  # correct, wrong, unsure
    time_spent = Column(Integer, nullable=True)  # 花费时间（秒）
    notes = Column(Text, nullable=True)  # 复习笔记
    
    # 元数据
    reviewed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关联关系
    # mistake = relationship("Mistake", back_populates="reviews")
    # user = relationship("User", back_populates="mistake_reviews")
