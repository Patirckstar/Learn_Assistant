"""测验 API 路由"""

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.quiz import QuestionGenerateIn, ExamSubmitIn
from app.services import quiz_svc

router = APIRouter(prefix="/api/quiz", tags=["测验"])


def _q_to_out(q):
    """将 Question ORM 转为输出格式"""
    options = json.loads(q.options) if isinstance(q.options, str) else q.options
    if isinstance(options, dict):
        options_list = [{"key": k, "text": v} for k, v in options.items()]
    else:
        options_list = options
    return {
        "id": q.id,
        "chapter_id": q.chapter_id,
        "type": q.type,
        "difficulty": q.difficulty,
        "stem": q.stem,
        "options": options_list,
        "answer": q.answer,
        "explanation": q.explanation,
        "created_at": q.created_at.isoformat() if q.created_at else "",
    }


@router.post("/generate")
def generate(body: QuestionGenerateIn, db: Session = Depends(get_db)):
    """调用 AI 为章节生成题目"""
    try:
        questions = quiz_svc.generate_questions(db, body.chapter_id, body.count, body.difficulty)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return [_q_to_out(q) for q in questions]


@router.get("/questions/{chapter_id}")
def list_questions(chapter_id: int, db: Session = Depends(get_db)):
    """获取某章节的已有题目（含答案，用于管理端, 前端考试时不调用此接口）"""
    questions = quiz_svc.get_questions(db, chapter_id)
    return [_q_to_out(q) for q in questions]


@router.get("/questions/{chapter_id}/exam")
def get_exam_questions(chapter_id: int, count: int = 5, time_limit: int = 0, db: Session = Depends(get_db)):
    """获取考试题目（不含答案），time_limit=秒数，0=不限时"""
    questions = quiz_svc.get_questions(db, chapter_id)
    if not questions:
        raise HTTPException(status_code=404, detail="该章节暂无题目，请先生成")
    selected = questions[:min(count, len(questions))]
    return {
        "time_limit": time_limit,
        "questions": [
            {k: v for k, v in _q_to_out(q).items() if k not in ("answer", "explanation")}
            for q in selected
        ],
    }


@router.post("/submit")
def submit(body: ExamSubmitIn, user_id: int = 1, db: Session = Depends(get_db)):
    """提交考试答案，批改并返回结果"""
    # 验证时间限制
    if body.time_limit > 0 and body.time_used is not None and body.time_used > body.time_limit:
        raise HTTPException(status_code=400, detail=f"答题超时（限制 {body.time_limit}s，实际 {body.time_used}s）")

    answers_dicts = [{"question_id": a.question_id, "user_answer": a.user_answer} for a in body.answers]
    try:
        result = quiz_svc.submit_exam(
            db, user_id, body.chapter_id, body.question_ids, answers_dicts,
            time_used=body.time_used, time_limit=body.time_limit,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return result


@router.get("/exams")
def list_exams(user_id: int = 1, chapter_id: int | None = None, db: Session = Depends(get_db)):
    """获取考试历史"""
    return quiz_svc.get_exams(db, user_id, chapter_id)


@router.get("/exams/{exam_id}")
def get_exam(exam_id: int, db: Session = Depends(get_db)):
    """获取考试详情"""
    result = quiz_svc.get_exam_detail(db, exam_id)
    if not result:
        raise HTTPException(status_code=404, detail="考试记录不存在")
    return result
