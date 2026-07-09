"""测验服务 — 出题、考试、批改"""

import json
import re
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.llm import get_llm
from app.models.chapter import Chapter
from app.models.question import Question
from app.models.exam import Exam, ExamDetail
from app.models.wrongbook import WrongBook


# ====================== 出题 ======================

def generate_questions(db: Session, chapter_id: int, count: int = 5, difficulty: str = "medium") -> list[Question]:
    """调用 LLM 为指定章节生成题目"""
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise ValueError("章节不存在")

    # 收集章节上下文（含父章标题）
    context_parts = []
    if chapter.parent_id:
        parent = db.query(Chapter).filter(Chapter.id == chapter.parent_id).first()
        if parent:
            context_parts.append(f"所属章: {parent.title}")
    context_parts.append(f"章节标题: {chapter.title}")
    if chapter.content:
        content = chapter.content[:3000]
        context_parts.append(f"学习内容: {content}")
    context = "\n".join(context_parts)

    diff_map = {"easy": "简单", "medium": "中等", "hard": "困难", "mixed": "混合（简单、中等、困难各约 1/3）"}
    diff_desc = diff_map.get(difficulty, "中等")

    prompt = f"""你是一位出题专家。请根据以下课程内容，生成{count}道测验题。

要求：
1. 题目类型为 single_choice（单选题，4个选项）或 true_false（判断题）
2. 难度: {diff_desc}
3. 每题需包含：题干(stem)、选项(options)、正确答案(answer)、解析(explanation)
4. 单选题的 answer 填选项字母（A/B/C/D），判断题填"对"或"错"
5. 返回严格的 JSON 数组，不要包含 markdown 代码块标记

课程内容：
{context}

返回格式（严格 JSON 数组，不要加其他文字）：
[
  {{
    "type": "single_choice",
    "difficulty": "medium",
    "stem": "题干什么内容？",
    "options": {{"A": "选项A内容", "B": "选项B内容", "C": "选项C内容", "D": "选项D内容"}},
    "answer": "A",
    "explanation": "解析内容"
  }}
]"""

    llm = get_llm()
    response = llm.invoke(prompt)
    raw = response.content.strip()

    # 清理 markdown 代码块标记
    raw = re.sub(r'^```(?:json)?\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)
    raw = raw.strip()

    try:
        questions_data = json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError(f"LLM 返回格式错误，无法解析: {raw[:300]}")

    if not isinstance(questions_data, list):
        raise ValueError("LLM 返回的不是数组格式")

    # 保存到数据库
    saved = []
    for q in questions_data:
        opt = q.get("options", {})
        if isinstance(opt, dict):
            options_str = json.dumps(opt, ensure_ascii=False)
        elif isinstance(opt, list):
            keys = ["A", "B", "C", "D", "E", "F"]
            opt_dict = {keys[i]: t for i, t in enumerate(opt)}
            options_str = json.dumps(opt_dict, ensure_ascii=False)
        else:
            options_str = str(opt)

        question = Question(
            chapter_id=chapter_id,
            type=q.get("type", "single_choice"),
            difficulty=q.get("difficulty", difficulty if difficulty != "mixed" else "medium"),
            stem=q.get("stem", ""),
            options=options_str,
            answer=q.get("answer", ""),
            explanation=q.get("explanation", ""),
        )
        db.add(question)
        saved.append(question)

    db.commit()
    for q in saved:
        db.refresh(q)
    return saved


# ====================== 题库查询 ======================

def get_questions(db: Session, chapter_id: int) -> list[Question]:
    """获取某章节的已有题目"""
    return db.query(Question).filter(Question.chapter_id == chapter_id).order_by(Question.created_at.desc()).all()


def get_question_by_id(db: Session, question_id: int) -> Question | None:
    """获取单个题目"""
    return db.query(Question).filter(Question.id == question_id).first()


# ====================== 提交考试 ======================

def submit_exam(
    db: Session,
    user_id: int,
    chapter_id: int,
    question_ids: list[int],
    answers: list[dict],
    time_used: int | None = None,
) -> dict:
    """提交考试答案，批改并保存"""
    questions = db.query(Question).filter(Question.id.in_(question_ids)).all()
    question_map = {q.id: q for q in questions}
    answer_map = {a["question_id"]: a["user_answer"] for a in answers}

    total_questions = len(question_ids)
    correct_count = 0
    details = []

    for qid in question_ids:
        q = question_map.get(qid)
        if not q:
            continue
        user_ans = answer_map.get(qid, "")
        correct_ans = q.answer.strip()
        is_correct = _check_answer(user_ans, correct_ans, q.type)

        if is_correct:
            correct_count += 1

        options = json.loads(q.options) if isinstance(q.options, str) else q.options
        if isinstance(options, dict):
            options_list = [{"key": k, "text": v} for k, v in options.items()]
        else:
            options_list = options

        details.append({
            "question_id": q.id,
            "stem": q.stem,
            "type": q.type,
            "options": options_list,
            "user_answer": user_ans,
            "correct_answer": correct_ans,
            "is_correct": is_correct,
            "explanation": q.explanation,
            "score": round(100.0 / total_questions, 1) if is_correct else 0,
            "db_obj": q,
        })

    total_score = 100.0
    score = round(correct_count / total_questions * 100.0, 1) if total_questions > 0 else 0

    # 保存考试记录
    exam = Exam(
        user_id=user_id,
        chapter_id=chapter_id,
        total_score=total_score,
        score=score,
        time_used=time_used,
    )
    db.add(exam)
    db.flush()

    # 保存答题明细 + 错题归档
    for d in details:
        det = ExamDetail(
            exam_id=exam.id,
            question_id=d["question_id"],
            user_answer=d["user_answer"],
            is_correct=1 if d["is_correct"] else 0,
            score=d["score"],
        )
        db.add(det)

        # 错题归档
        if not d["is_correct"]:
            _add_to_wrong_book(db, user_id, d["db_obj"], chapter_id, exam.id)

    db.commit()

    return {
        "exam_id": exam.id,
        "total_score": total_score,
        "score": score,
        "time_used": time_used,
        "details": [
            {
                "question_id": d["question_id"],
                "stem": d["stem"],
                "type": d["type"],
                "options": d["options"],
                "user_answer": d["user_answer"],
                "correct_answer": d["correct_answer"],
                "is_correct": d["is_correct"],
                "explanation": d["explanation"],
                "score": d["score"],
            }
            for d in details
        ],
        "created_at": exam.created_at.isoformat() if exam.created_at else "",
    }


# ====================== 考试历史 ======================

def get_exams(db: Session, user_id: int, chapter_id: int | None = None) -> list[dict]:
    """获取考试历史"""
    q = db.query(Exam).filter(Exam.user_id == user_id)
    if chapter_id:
        q = q.filter(Exam.chapter_id == chapter_id)
    exams = q.order_by(Exam.created_at.desc()).all()

    result = []
    for e in exams:
        chapter_title = None
        if e.chapter_id:
            ch = db.query(Chapter).filter(Chapter.id == e.chapter_id).first()
            chapter_title = ch.title if ch else None
        result.append({
            "id": e.id,
            "chapter_id": e.chapter_id,
            "chapter_title": chapter_title,
            "total_score": float(e.total_score),
            "score": float(e.score),
            "time_used": e.time_used,
            "created_at": e.created_at.isoformat() if e.created_at else "",
        })
    return result


def get_exam_detail(db: Session, exam_id: int) -> dict | None:
    """获取考试详情"""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        return None

    details = db.query(ExamDetail).filter(ExamDetail.exam_id == exam_id).all()
    detail_list = []
    for det in details:
        q = db.query(Question).filter(Question.id == det.question_id).first()
        if not q:
            continue
        options = json.loads(q.options) if isinstance(q.options, str) else q.options
        if isinstance(options, dict):
            options_list = [{"key": k, "text": v} for k, v in options.items()]
        else:
            options_list = options

        detail_list.append({
            "question_id": q.id,
            "stem": q.stem,
            "type": q.type,
            "options": options_list,
            "user_answer": det.user_answer,
            "correct_answer": q.answer,
            "is_correct": bool(det.is_correct),
            "explanation": q.explanation,
            "score": float(det.score) if det.score else 0,
        })

    return {
        "exam_id": exam.id,
        "total_score": float(exam.total_score),
        "score": float(exam.score),
        "time_used": exam.time_used,
        "details": detail_list,
        "created_at": exam.created_at.isoformat() if exam.created_at else "",
    }


# ====================== 辅助函数 ======================

def _check_answer(user_answer: str, correct_answer: str, question_type: str) -> bool:
    """检查答案是否正确"""
    ua = user_answer.strip().upper()
    ca = correct_answer.strip().upper()
    if question_type == "true_false":
        true_set = {"对", "正确", "是", "TRUE", "T", "√", "✓", "YES", "Y"}
        false_set = {"错", "错误", "否", "FALSE", "F", "×", "✗", "NO", "N"}
        ua_bool = ua in true_set
        ca_bool = ca in true_set
        return ua_bool == ca_bool
    return ua == ca


def _add_to_wrong_book(db: Session, user_id: int, question: Question, chapter_id: int, exam_id: int):
    """将错题添加到错题本"""
    existing = (
        db.query(WrongBook)
        .filter(WrongBook.user_id == user_id, WrongBook.question_id == question.id)
        .first()
    )
    now = datetime.now()
    if existing:
        existing.wrong_count = (existing.wrong_count or 0) + 1
        existing.last_wrong_at = now
    else:
        wb = WrongBook(
            user_id=user_id,
            question_id=question.id,
            chapter_id=chapter_id,
            exam_id=exam_id,
            wrong_count=1,
            correct_count=0,
            last_wrong_at=now,
        )
        db.add(wb)
