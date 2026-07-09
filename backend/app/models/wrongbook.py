from sqlalchemy import Column, Integer, DateTime, ForeignKey, func, UniqueConstraint
from app.core.database import Base


class WrongBook(Base):
    __tablename__ = "wrong_book"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    chapter_id = Column(Integer, ForeignKey("chapters.id", ondelete="SET NULL"), nullable=True)
    exam_id = Column(Integer, ForeignKey("exams.id", ondelete="SET NULL"), nullable=True)
    wrong_count = Column(Integer, default=1)
    correct_count = Column(Integer, default=0)
    last_wrong_at = Column(DateTime, nullable=True)
    last_practiced_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "question_id", name="uk_user_question"),
    )
