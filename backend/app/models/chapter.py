"""课程章节模型"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from app.core.database import Base


class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    parent_id = Column(Integer, ForeignKey("chapters.id", ondelete="CASCADE"), nullable=True)
    title = Column(String(255), nullable=False)
    level = Column(Integer, nullable=False, default=1)
    sort_order = Column(Integer, default=0)
    content = Column(Text, nullable=True)
    source_doc_id = Column(Integer, ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=func.now())
