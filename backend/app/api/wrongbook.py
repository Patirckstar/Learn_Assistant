"""错题本 API 路由"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services import wrongbook_svc

router = APIRouter(prefix="/api/wrongbook", tags=["错题本"])


@router.get("")
def list_wrong(chapter_id: int | None = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取错题列表"""
    return wrongbook_svc.get_wrong_questions(db, current_user.id, chapter_id)


@router.get("/practice")
def practice(count: int = 10, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取一组错题用于重练（不含答案）"""
    questions = wrongbook_svc.get_practice_questions(db, current_user.id, count)
    if not questions:
        raise HTTPException(status_code=404, detail="暂无错题可练习")
    return questions


@router.post("/practice/submit")
def submit_practice(body: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """提交重练答案
    body: { "answers": [{ "wrongbook_id": 1, "user_answer": "A" }, ...] }
    """
    answers = body.get("answers", [])
    if not answers:
        raise HTTPException(status_code=400, detail="answers 不能为空")
    try:
        return wrongbook_svc.submit_practice(db, current_user.id, answers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
def stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取错题统计数据"""
    return wrongbook_svc.get_wrong_stats(db, current_user.id)
