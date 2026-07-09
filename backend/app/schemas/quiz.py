"""测验相关 Pydantic 模型"""

from datetime import datetime
from pydantic import BaseModel, Field


# ====================== 题目 ======================

class QuestionGenerateIn(BaseModel):
    """出题请求"""
    chapter_id: int = Field(..., description="章节 ID")
    count: int = Field(default=5, ge=1, le=20, description="题目数量")
    difficulty: str = Field(default="medium", description="难度：easy / medium / hard / mixed")
    time_limit: int = Field(default=0, ge=0, le=3600, description="时间限制（秒），0=不限时")


class QuestionOption(BaseModel):
    """选项（用于前端展示）"""
    key: str
    text: str


class QuestionOut(BaseModel):
    """题目输出（不含答案）"""
    id: int
    chapter_id: int | None = None
    type: str
    difficulty: str
    stem: str
    options: list[QuestionOption]
    created_at: str

    class Config:
        from_attributes = True


class QuestionWithAnswer(QuestionOut):
    """题目输出（含答案，批改后展示）"""
    answer: str
    explanation: str | None = None


# ====================== 考试 ======================

class ExamAnswerIn(BaseModel):
    """单题作答"""
    question_id: int
    user_answer: str


class ExamSubmitIn(BaseModel):
    """提交考试"""
    chapter_id: int
    question_ids: list[int]
    answers: list[ExamAnswerIn]
    time_limit: int = Field(default=0, ge=0, le=3600, description="时间限制（秒），0=不限时")
    time_used: int | None = Field(default=None, description="实际用时（秒）")


class ExamDetailOut(BaseModel):
    """答题明细"""
    question_id: int
    stem: str
    type: str
    options: list[QuestionOption]
    user_answer: str | None = None
    correct_answer: str
    is_correct: bool
    explanation: str | None = None
    score: float

    class Config:
        from_attributes = True


class ExamResultOut(BaseModel):
    """考试结果"""
    exam_id: int
    total_score: float
    score: float
    time_limit: int = 0
    time_used: int | None = None
    details: list[ExamDetailOut]
    created_at: str


class ExamHistoryOut(BaseModel):
    """考试历史"""
    id: int
    chapter_id: int | None = None
    chapter_title: str | None = None
    total_score: float
    score: float
    time_limit: int = 0
    time_used: int | None = None
    created_at: str

    class Config:
        from_attributes = True
