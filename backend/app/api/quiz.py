"""测验 API 路由 — 试卷管理、考试"""

import json
import time
import threading
from queue import Queue

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db, SessionLocal
from app.core.security import get_current_user
from app.models.user import User
from app.services import quiz_svc

router = APIRouter(prefix="/api/quiz", tags=["测验"])


@router.get("/papers")
def list_papers(db: Session = Depends(get_db)):
    """获取试卷列表"""
    return quiz_svc.get_papers(db)


@router.get("/papers/{paper_id}")
def get_paper(paper_id: int, db: Session = Depends(get_db)):
    """获取试卷详情"""
    result = quiz_svc.get_paper(db, paper_id)
    if not result:
        raise HTTPException(status_code=404, detail="试卷不存在")
    return result


@router.post("/papers/refresh")
def refresh_papers_stream():
    """刷新所有试卷（流式返回进度）"""
    q = Queue()
    
    def progress_callback(current, total, message):
        progress = int(current / total * 100) if total > 0 else 0
        q.put(f"data: {json.dumps({'current': current, 'total': total, 'progress': progress, 'message': message}, ensure_ascii=False)}\n\n")
    
    def worker():
        local_db = None
        try:
            local_db = SessionLocal()
            # 获取章节总数，用于计算 skipped_count
            from app.models.chapter import Chapter
            total_chapters = local_db.query(Chapter).filter(Chapter.level == 1).count()
            papers = quiz_svc.refresh_all_papers(local_db, progress_callback=progress_callback)
            q.put(f"data: {json.dumps({'status': 'completed', 'generated_count': len(papers), 'skipped_count': total_chapters - len(papers), 'total_count': total_chapters}, ensure_ascii=False)}\n\n")
        except Exception as e:
            q.put(f"data: {json.dumps({'status': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n")
        finally:
            if local_db:
                local_db.close()
            q.put(None)
    
    threading.Thread(target=worker, daemon=True).start()
    
    def generate():
        while True:
            event = q.get()
            if event is None:
                break
            yield event
            time.sleep(0.1)
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/papers/{paper_id}/exam")
def get_exam_questions(paper_id: int, db: Session = Depends(get_db)):
    """获取试卷的考试题目（不含答案）"""
    result = quiz_svc.get_exam_questions_for_paper(db, paper_id)
    if not result:
        raise HTTPException(status_code=404, detail="试卷不存在或暂无题目")
    return result


@router.post("/papers/{paper_id}/submit")
def submit_exam(paper_id: int, answers: list[dict], time_used: int | None = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """提交试卷答案，批改并返回结果"""
    try:
        result = quiz_svc.submit_exam_for_paper(db, current_user.id, paper_id, answers, time_used)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return result


@router.get("/exams")
def list_exams(chapter_id: int | None = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取考试历史"""
    return quiz_svc.get_exams(db, current_user.id, chapter_id)


@router.get("/exams/{exam_id}")
def get_exam(exam_id: int, db: Session = Depends(get_db)):
    """获取考试详情"""
    result = quiz_svc.get_exam_detail(db, exam_id)
    if not result:
        raise HTTPException(status_code=404, detail="考试记录不存在")
    return result