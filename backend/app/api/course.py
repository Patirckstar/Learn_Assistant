"""课程 API 路由"""

import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.course import ChapterOut, DashboardOut
from app.services import course_svc

router = APIRouter(prefix="/api/course", tags=["课程"])


def _progress_event(current: int, total: int, message: str):
    """生成 SSE 进度事件"""
    percent = int(current / total * 100) if total > 0 else 0
    data = {
        "current": current,
        "total": total,
        "percent": percent,
        "message": message,
    }
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/outline/refresh")
def refresh_outline(db: Session = Depends(get_db)):
    """刷新课程大纲：为知识库中新增的文档生成课程，已有课程不动"""
    try:
        chapters = course_svc.refresh_outline(db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return _build_tree(chapters)


from queue import Queue
import threading

@router.post("/outline/refresh/stream")
def refresh_outline_stream(db: Session = Depends(get_db)):
    """刷新课程大纲（带进度推送）"""
    try:
        q = Queue()

        def progress_callback(current: int, total: int, message: str):
            q.put(_progress_event(current, total, message))

        def worker():
            try:
                chapters = course_svc.refresh_outline(db, progress_callback)
                q.put(f"data: {json.dumps({
                    'current': 100,
                    'total': 100,
                    'percent': 100,
                    'message': '完成',
                    'result': _build_tree(chapters),
                }, ensure_ascii=False)}\n\n")
            except Exception as e:
                q.put(f"data: {json.dumps({
                    'current': 0,
                    'total': 0,
                    'percent': 0,
                    'message': f'错误: {str(e)}',
                    'error': str(e),
                }, ensure_ascii=False)}\n\n")
            finally:
                q.put(None)

        threading.Thread(target=worker, daemon=True).start()

        def generate():
            while True:
                event = q.get()
                if event is None:
                    break
                yield event

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/outline")
def get_outline(db: Session = Depends(get_db)):
    """获取课程大纲树"""
    chapters = course_svc.get_outline_tree(db)
    return _build_tree(chapters)


@router.get("/chapters/{chapter_id}", response_model=ChapterOut)
def get_chapter(chapter_id: int, db: Session = Depends(get_db)):
    """获取章节详情"""
    chapter = course_svc.get_outline_tree(db)
    chapter = next((c for c in chapter if c.id == chapter_id), None)
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    return chapter


@router.post("/chapters/{chapter_id}/regenerate")
def regenerate_chapter(chapter_id: int, db: Session = Depends(get_db)):
    """重新生成某章节的学习内容"""
    try:
        content = course_svc.generate_chapter_content(db, chapter_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"content": content}


@router.get("/progress")
def get_progress(user_id: int = 1, db: Session = Depends(get_db)):
    """获取学习进度"""
    return course_svc.get_progress(db, user_id)


@router.put("/progress/{chapter_id}")
def update_progress(chapter_id: int, status: str, user_id: int = 1, db: Session = Depends(get_db)):
    """更新章节进度"""
    allowed = {"not_started", "learning", "completed"}
    if status not in allowed:
        raise HTTPException(status_code=400, detail=f"状态值无效，可选: {allowed}")
    progress = course_svc.update_progress(db, user_id, chapter_id, status)
    return {
        "chapter_id": progress.chapter_id,
        "status": progress.status,
        "started_at": progress.started_at,
        "completed_at": progress.completed_at,
    }


@router.get("/dashboard", response_model=DashboardOut)
def get_dashboard(user_id: int = 1, db: Session = Depends(get_db)):
    """获取进度看板"""
    return course_svc.get_dashboard(db, user_id)


@router.post("/progress/reset")
def reset_progress(user_id: int = 1, db: Session = Depends(get_db)):
    """重置所有进度"""
    course_svc.reset_progress(db, user_id)
    return {"message": "已重置"}


def _build_tree(chapters: list) -> list[dict]:
    """将扁平章节列表转为树形结构"""
    parents = [c for c in chapters if c.level == 1]
    tree = []
    for p in parents:
        children = [
            {"id": c.id, "title": c.title, "level": c.level, "sort_order": c.sort_order}
            for c in chapters
            if c.parent_id == p.id
        ]
        tree.append({
            "id": p.id,
            "title": p.title,
            "level": p.level,
            "sort_order": p.sort_order,
            "children": children,
        })
    return tree
