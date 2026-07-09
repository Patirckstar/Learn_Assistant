"""课程相关 Pydantic 模型"""

from datetime import datetime
from pydantic import BaseModel


class ChapterOut(BaseModel):
    id: int
    parent_id: int | None = None
    title: str
    level: int
    sort_order: int = 0
    content: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChapterTreeNode(BaseModel):
    """树形结构的章节节点"""
    id: int
    title: str
    level: int
    sort_order: int
    children: list["ChapterTreeNode"] = []


class OutlineOut(BaseModel):
    id: int
    title: str
    level: int
    sort_order: int
    children: list["OutlineOut"] = []


class ProgressOut(BaseModel):
    chapter_id: int
    status: str
    started_at: datetime | None = None
    completed_at: datetime | None = None


class DashboardOut(BaseModel):
    total_chapters: int
    completed: int
    learning: int
    not_started: int
    percent: float
    detail: list[ProgressOut]
