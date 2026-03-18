from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class FollowUp(Base):
    """追问记录模型"""

    __tablename__ = "follow_ups"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 对话内容
    message = Column(Text, nullable=False)  # 用户提问
    response = Column(Text, nullable=False)  # AI 回复
    message_type = Column(String(20), nullable=True)  # question, answer, clarification
    
    # 上下文
    parent_id = Column(Integer, ForeignKey("follow_ups.id"), nullable=True)  # 父消息 ID（对话树）
    conversation_order = Column(Integer, nullable=True)  # 对话顺序
    
    # 元数据
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String(50), nullable=True)
    
    # 软删除
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # 关联关系
    # question = relationship("Question", back_populates="follow_ups")
    # user = relationship("User", back_populates="follow_ups")
    # parent = relationship("FollowUp", remote_side=[id], back_populates="children")
    # children = relationship("FollowUp", back_populates="parent")
