from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, DECIMAL, func
from app.core.database import Base


class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    chapter_id = Column(Integer, ForeignKey("chapters.id", ondelete="SET NULL"), nullable=True)
    total_score = Column(DECIMAL(5, 1), nullable=False)
    score = Column(DECIMAL(5, 1), nullable=False)
    time_limit = Column(Integer, nullable=True)
    time_used = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now())


class ExamDetail(Base):
    __tablename__ = "exam_details"

    id = Column(Integer, primary_key=True, autoincrement=True)
    exam_id = Column(Integer, ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    user_answer = Column(String(255), nullable=True)
    is_correct = Column(Integer, nullable=True)
    score = Column(DECIMAL(4, 1), nullable=True)
