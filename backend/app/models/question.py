from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from app.core.database import Base


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id", ondelete="SET NULL"), nullable=True)
    type = Column(String(20), nullable=False)
    difficulty = Column(String(10), default="medium")
    stem = Column(Text, nullable=False)
    options = Column(String(1000), nullable=False)
    answer = Column(String(255), nullable=False)
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
