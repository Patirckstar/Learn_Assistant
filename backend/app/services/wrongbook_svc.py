"""错题本服务 — 错题归档、重练、统计"""

import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.wrongbook import WrongBook
from app.models.question import Question
from app.models.chapter import Chapter


# ====================== 错题列表 ======================

def get_wrong_questions(db: Session, user_id: int, chapter_id: int | None = None) -> list[dict]:
    """获取错题列表"""
    q = db.query(WrongBook).filter(WrongBook.user_id == user_id)
    if chapter_id:
        q = q.filter(WrongBook.chapter_id == chapter_id)
    records = q.order_by(WrongBook.last_wrong_at.desc()).all()

    result = []
    for wb in records:
        question = db.query(Question).filter(Question.id == wb.question_id).first()
        if not question:
            continue
        chapter_title = None
        if wb.chapter_id:
            ch = db.query(Chapter).filter(Chapter.id == wb.chapter_id).first()
            chapter_title = ch.title if ch else None

        options = json.loads(question.options) if isinstance(question.options, str) else question.options
        if isinstance(options, dict):
            options_list = [{"key": k, "text": v} for k, v in options.items()]
        else:
            options_list = options

        result.append({
            "id": wb.id,
            "question_id": question.id,
            "chapter_id": wb.chapter_id,
            "chapter_title": chapter_title,
            "type": question.type,
            "difficulty": question.difficulty,
            "stem": question.stem,
            "options": options_list,
            "answer": question.answer,
            "explanation": question.explanation,
            "wrong_count": wb.wrong_count or 0,
            "correct_count": wb.correct_count or 0,
            "last_wrong_at": wb.last_wrong_at.isoformat() if wb.last_wrong_at else None,
            "last_practiced_at": wb.last_practiced_at.isoformat() if wb.last_practiced_at else None,
        })
    return result


# ====================== 错题重练 ======================

def get_practice_questions(db: Session, user_id: int, count: int = 10) -> list[dict]:
    """获取用于重练的错题（不含答案）"""
    records = (
        db.query(WrongBook)
        .filter(WrongBook.user_id == user_id)
        .order_by(WrongBook.last_wrong_at.desc())
        .limit(count)
        .all()
    )

    result = []
    for wb in records:
        question = db.query(Question).filter(Question.id == wb.question_id).first()
        if not question:
            continue
        options = json.loads(question.options) if isinstance(question.options, str) else question.options
        if isinstance(options, dict):
            options_list = [{"key": k, "text": v} for k, v in options.items()]
        else:
            options_list = options

        result.append({
            "wrongbook_id": wb.id,
            "question_id": question.id,
            "chapter_id": wb.chapter_id,
            "type": question.type,
            "difficulty": question.difficulty,
            "stem": question.stem,
            "options": options_list,
        })
    return result


def submit_practice(db: Session, user_id: int, answers: list[dict]) -> dict:
    """提交重练答案"""
    total = len(answers)
    correct_count = 0
    now = datetime.now()

    for a in answers:
        wb = db.query(WrongBook).filter(
            WrongBook.id == a["wrongbook_id"],
            WrongBook.user_id == user_id,
        ).first()
        if not wb:
            continue

        question = db.query(Question).filter(Question.id == wb.question_id).first()
        if not question:
            continue

        user_ans = a.get("user_answer", "").strip().upper()
        correct_ans = question.answer.strip().upper()

        is_correct = user_ans == correct_ans
        if question.type == "true_false":
            true_set = {"对", "正确", "是", "TRUE", "T"}
            false_set = {"错", "错误", "否", "FALSE", "F"}
            is_correct = (user_ans in true_set) == (correct_ans in true_set)

        wb.last_practiced_at = now
        if is_correct:
            wb.correct_count = (wb.correct_count or 0) + 1
            correct_count += 1
        else:
            wb.wrong_count = (wb.wrong_count or 0) + 1

    db.commit()
    return {"total": total, "correct": correct_count, "score": round(correct_count / total * 100, 1) if total > 0 else 0}


# ====================== 错题统计 ======================

def get_wrong_stats(db: Session, user_id: int) -> dict:
    """获取错题统计数据"""
    records = db.query(WrongBook).filter(WrongBook.user_id == user_id).all()

    total_wrong = len(records)
    total_wrong_times = sum(r.wrong_count or 0 for r in records)
    total_correct_times = sum(r.correct_count or 0 for r in records)
    total_attempts = total_wrong_times + total_correct_times

    # 按章节统计
    chapter_stats = {}
    for r in records:
        cid = r.chapter_id or 0
        if cid not in chapter_stats:
            ch = db.query(Chapter).filter(Chapter.id == cid).first() if cid else None
            chapter_stats[cid] = {"chapter_id": cid, "chapter_title": ch.title if ch else "未知", "count": 0}
        chapter_stats[cid]["count"] += 1

    return {
        "total_wrong_questions": total_wrong,
        "total_wrong_times": total_wrong_times,
        "total_correct_times": total_correct_times,
        "total_practice_attempts": total_attempts,
        "correct_rate": round(total_correct_times / total_attempts * 100, 1) if total_attempts > 0 else 0,
        "by_chapter": list(chapter_stats.values()),
    }
