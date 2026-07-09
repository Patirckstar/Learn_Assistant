"""测验服务 — 题目刷新、试卷管理、考试批改、AI反馈"""

import json
import re
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.llm import get_llm
from app.models.chapter import Chapter
from app.models.question import Question
from app.models.exam import Exam, ExamDetail
from app.models.wrongbook import WrongBook
from app.models.paper import Paper


def get_parent_chapters(db: Session) -> list[Chapter]:
    """获取所有父章节（level=1 的章节）"""
    return db.query(Chapter).filter(Chapter.level == 1).order_by(Chapter.sort_order).all()


def calculate_question_count(content_length: int) -> int:
    """根据内容长度计算题目数量（5-15题）"""
    if content_length < 1500:
        return 5
    elif content_length < 3000:
        return 8
    elif content_length < 5000:
        return 10
    elif content_length < 8000:
        return 12
    else:
        return 15


def generate_questions_for_chapter(db: Session, chapter: Chapter) -> list[Question]:
    """为某章节生成题目"""
    sections = db.query(Chapter).filter(Chapter.parent_id == chapter.id).order_by(Chapter.sort_order).all()
    print(f"DEBUG: 章节「{chapter.title}」有 {len(sections)} 个小节")
    
    context_parts = []
    context_parts.append(f"章节标题: {chapter.title}")
    
    total_content = ""
    if chapter.content:
        total_content += chapter.content
        context_parts.append(f"章节内容: {chapter.content}")
    else:
        print(f"DEBUG: 章节「{chapter.title}」内容为空")
    
    for sec in sections:
        if sec.content:
            total_content += "\n" + sec.content
            context_parts.append(f"小节 {sec.title}: {sec.content}")
        else:
            print(f"DEBUG: 小节「{sec.title}」内容为空")
    
    context = "\n".join(context_parts)
    
    print(f"DEBUG: 章节「{chapter.title}」总内容长度: {len(total_content)}")
    
    question_count = calculate_question_count(len(total_content))
    
    easy_count = (question_count * 2) // 5
    medium_count = (question_count * 2) // 5
    hard_count = question_count - easy_count - medium_count
    
    if easy_count == 0:
        easy_count = 1
    if medium_count == 0:
        medium_count = 1
    hard_count = max(1, question_count - easy_count - medium_count)
    
    prompt = f"""你是一位经验丰富的教育测评专家，擅长根据课程内容设计高质量的测验题目。你的任务是：根据以下课程内容，生成{question_count}道严谨、科学、有效的测验题。

=== 角色定位 ===
- 你是一位专业的课程出题专家
- 你熟悉教育测量理论，能够设计区分度良好的题目
- 你严格依据提供的课程内容出题，不添加外部知识

=== 难度等级定义 ===
严格按照以下比例生成：easy={easy_count}道、medium={medium_count}道、hard={hard_count}道

1. easy（简单）
   - 考察：课程中明确陈述的基本概念、定义、事实、规则
   - 特征：答案直接在原文中可以找到，不需要推理
   - 示例："课程中提到的命名规则是什么？"

2. medium（中等）
   - 考察：概念之间的关系、规则的应用、简单的推理判断
   - 特征：需要理解内容含义，进行简单分析或计算
   - 示例："根据命名规则，以下哪个变量名是正确的？"

3. hard（困难）
   - 考察：综合运用多个知识点、深度分析、批判性思维
   - 特征：需要跨段落理解，或应用多个规则进行判断
   - 示例："当多个命名规则发生冲突时，应优先遵循哪个？"

=== 题目质量标准 ===
1. 内容相关性：题目必须紧密围绕课程内容，题干和选项都要来源于课程中的具体知识点
2. 准确性：正确答案必须是课程内容明确支持的，不能有歧义
3. 区分度：干扰选项（错误选项）要有迷惑性，基于常见误解或混淆点设计
4. 多样性：题目要覆盖课程的主要知识点，避免重复考察同一内容
5. 清晰性：题干表述清晰，选项无语法错误，避免模糊不清的表述

=== 题目类型规范 ===
1. single_choice（单选题）
   - 必须有4个选项，标记为A、B、C、D
   - 选项内容要简洁明了，避免过长
   - 正确答案只有一个

2. true_false（判断题）
   - 选项固定为{{"A": "对", "B": "错"}}
   - 题干是一个明确的陈述
   - 答案必须是"对"或"错"

=== 输出格式要求 ===
1. 返回严格的 JSON 数组格式，不要包含任何其他文字
2. 不要包含 markdown 代码块标记（如 ```json）
3. 每个题目必须包含以下字段：
   - type: "single_choice" 或 "true_false"
   - difficulty: "easy"、"medium" 或 "hard"
   - stem: 题干内容，必须引用课程内容
   - options: 选项对象，键为"A"、"B"、"C"、"D"，值为选项内容
   - answer: 正确答案（单选题填字母，判断题填"对"或"错"）
   - explanation: 解析，说明答案依据，引用课程原文内容

=== 自我检查清单 ===
输出前请检查：
- [ ] 难度分布是否符合要求（easy={easy_count}, medium={medium_count}, hard={hard_count}）
- [ ] 所有题目是否都来源于课程内容
- [ ] 正确答案是否有课程内容支持
- [ ] 干扰选项是否有迷惑性
- [ ] JSON格式是否正确，无语法错误
- [ ] 题目数量是否为{question_count}道

=== 课程内容 ===
{context}

=== 输出示例 ===
[
  {{
    "type": "single_choice",
    "difficulty": "easy",
    "stem": "根据课程内容，变量命名应使用哪种风格？",
    "options": {{"A": "全大写字母", "B": "驼峰式命名", "C": "下划线分隔", "D": "随机命名"}},
    "answer": "B",
    "explanation": "课程中明确指出：'变量名应采用驼峰式命名，首字母小写，后续单词首字母大写'。"
  }},
  {{
    "type": "true_false",
    "difficulty": "medium",
    "stem": "根据课程内容，常量命名应使用全大写字母并以下划线分隔单词。",
    "options": {{"A": "对", "B": "错"}},
    "answer": "对",
    "explanation": "课程中提到：'常量命名规范为全大写，单词之间用下划线分隔，例如 MAX_SIZE'。"
  }},
  {{
    "type": "single_choice",
    "difficulty": "hard",
    "stem": "当一个变量既是常量又是类成员时，应优先遵循哪种命名规则？",
    "options": {{"A": "全大写常量规则", "B": "驼峰式成员变量规则", "C": "下划线前缀规则", "D": "匈牙利命名法"}},
    "answer": "A",
    "explanation": "课程中说明：'常量规则优先级高于成员变量规则，类常量应使用全大写命名，如类中的 PI = 3.14'。"
  }}
]"""

    print(f"DEBUG: 开始调用LLM生成{question_count}道题目...")
    llm = get_llm()
    try:
        response = llm.invoke(prompt)
        raw = response.content.strip()
        print(f"DEBUG: LLM调用完成，返回长度: {len(raw)}")
    except Exception as e:
        print(f"ERROR: LLM调用失败: {str(e)}")
        raise

    raw = re.sub(r'^```(?:json)?\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)
    raw = raw.strip()

    try:
        questions_data = json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError(f"LLM 返回格式错误，无法解析: {raw[:300]}")

    if not isinstance(questions_data, list):
        raise ValueError("LLM 返回的不是数组格式")

    difficulty_counts = {"easy": 0, "medium": 0, "hard": 0}
    for q in questions_data:
        diff = q.get("difficulty", "medium").lower()
        if diff in difficulty_counts:
            difficulty_counts[diff] += 1

    if (difficulty_counts["easy"] != easy_count or 
        difficulty_counts["medium"] != medium_count or 
        difficulty_counts["hard"] != hard_count):
        print(f"警告: 难度分布不符 - 期望(easy:{easy_count}, medium:{medium_count}, hard:{hard_count}), "
              f"实际(easy:{difficulty_counts['easy']}, medium:{difficulty_counts['medium']}, hard:{difficulty_counts['hard']})")

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
            chapter_id=None,
            parent_chapter_id=chapter.id,
            type=q.get("type", "single_choice"),
            difficulty=q.get("difficulty", "medium"),
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


def refresh_paper_for_chapter(db: Session, chapter: Chapter, progress_callback=None) -> Paper:
    """刷新某章节的试卷"""
    existing_paper = db.query(Paper).filter(Paper.chapter_id == chapter.id).first()
    
    if progress_callback:
        progress_callback(f"正在删除章节「{chapter.title}」的旧题目...")
    
    db.query(Question).filter(Question.parent_chapter_id == chapter.id).delete()
    
    if progress_callback:
        progress_callback(f"正在分析章节「{chapter.title}」内容...")
    
    questions = generate_questions_for_chapter(db, chapter)
    
    if progress_callback:
        progress_callback(f"章节「{chapter.title}」生成了 {len(questions)} 道题目")
    
    if existing_paper:
        existing_paper.question_count = len(questions)
        existing_paper.is_ready = 1
        existing_paper.updated_at = datetime.now()
    else:
        existing_paper = Paper(
            chapter_id=chapter.id,
            title=f"{chapter.title} - 测验",
            description=f"根据章节「{chapter.title}」内容生成的测验题",
            question_count=len(questions),
            time_limit=len(questions) * 180,
            is_ready=1,
        )
        db.add(existing_paper)
    
    db.commit()
    db.refresh(existing_paper)
    return existing_paper


def refresh_all_papers(db: Session, progress_callback=None) -> list[Paper]:
    """刷新试卷：检测没有试卷的章节并生成题目，已有试卷的章节保持不变"""
    chapters = get_parent_chapters(db)
    print(f"DEBUG: 找到 {len(chapters)} 个父章节")
    
    chapters_without_paper = []
    chapters_with_paper = []
    
    for chapter in chapters:
        existing_paper = db.query(Paper).filter(Paper.chapter_id == chapter.id).first()
        
        sections = db.query(Chapter).filter(Chapter.parent_id == chapter.id).all()
        total_content_len = 0
        if chapter.content:
            total_content_len += len(chapter.content)
        for sec in sections:
            if sec.content:
                total_content_len += len(sec.content)
        
        if existing_paper:
            chapters_with_paper.append(chapter)
            print(f"DEBUG: 章节「{chapter.title}」(ID:{chapter.id}) 已有试卷")
        else:
            chapters_without_paper.append(chapter)
            print(f"DEBUG: 章节「{chapter.title}」(ID:{chapter.id}) 需要生成试卷，内容长度:{total_content_len}")
    
    total_to_process = len(chapters_without_paper)
    results = []
    
    if progress_callback:
        progress_callback(0, total_to_process, 
            f"检测到 {len(chapters)} 个章节，其中 {total_to_process} 个章节需要生成试卷，{len(chapters_with_paper)} 个已有试卷")
    
    if total_to_process == 0:
        if progress_callback:
            progress_callback(100, 1, "所有章节都已有试卷，无需刷新")
        return results
    
    for i, chapter in enumerate(chapters_without_paper):
        if progress_callback:
            progress_callback(i, total_to_process, f"正在为章节「{chapter.title}」生成试卷...")
        
        try:
            def inner_progress(msg):
                if progress_callback:
                    progress_callback(i, total_to_process, msg)
            
            paper = refresh_paper_for_chapter(db, chapter, inner_progress)
            results.append(paper)
            
            if progress_callback:
                progress_callback(i + 1, total_to_process, f"章节「{chapter.title}」试卷生成完成，共 {paper.question_count} 题")
        except Exception as e:
            if progress_callback:
                progress_callback(i + 1, total_to_process, f"章节「{chapter.title}」生成失败: {str(e)}")
    
    if progress_callback:
        progress_callback(total_to_process, total_to_process, 
            f"试卷刷新完成，共为 {len(results)} 个章节生成了试卷")
    
    return results


def get_papers(db: Session) -> list[dict]:
    """获取所有试卷列表"""
    papers = db.query(Paper).order_by(Paper.chapter_id).all()
    result = []
    for p in papers:
        chapter = db.query(Chapter).filter(Chapter.id == p.chapter_id).first()
        result.append({
            "id": p.id,
            "chapter_id": p.chapter_id,
            "chapter_title": chapter.title if chapter else "",
            "title": p.title,
            "description": p.description,
            "question_count": p.question_count,
            "time_limit": p.time_limit,
            "is_ready": bool(p.is_ready),
            "created_at": p.created_at.isoformat() if p.created_at else "",
            "updated_at": p.updated_at.isoformat() if p.updated_at else "",
        })
    return result


def get_paper(db: Session, paper_id: int) -> dict | None:
    """获取试卷详情"""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        return None
    
    questions = db.query(Question).filter(Question.parent_chapter_id == paper.chapter_id).all()
    chapter = db.query(Chapter).filter(Chapter.id == paper.chapter_id).first()
    
    return {
        "id": paper.id,
        "chapter_id": paper.chapter_id,
        "chapter_title": chapter.title if chapter else "",
        "title": paper.title,
        "description": paper.description,
        "question_count": paper.question_count,
        "time_limit": paper.time_limit,
        "is_ready": bool(paper.is_ready),
        "created_at": paper.created_at.isoformat() if paper.created_at else "",
        "updated_at": paper.updated_at.isoformat() if paper.updated_at else "",
        "questions": [_q_to_dict(q) for q in questions],
    }


def get_exam_questions_for_paper(db: Session, paper_id: int) -> dict | None:
    """获取试卷的考试题目（不含答案）"""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        return None
    
    questions = db.query(Question).filter(Question.parent_chapter_id == paper.chapter_id).all()
    if not questions:
        return None
    
    return {
        "paper_id": paper.id,
        "paper_title": paper.title,
        "time_limit": paper.time_limit,
        "question_count": len(questions),
        "questions": [
            {k: v for k, v in _q_to_dict(q).items() if k not in ("answer", "explanation")}
            for q in questions
        ],
    }


def submit_exam_for_paper(
    db: Session,
    user_id: int,
    paper_id: int,
    answers: list[dict],
    time_used: int | None = None,
) -> dict:
    """提交试卷答案，批改并保存"""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise ValueError("试卷不存在")
    
    questions = db.query(Question).filter(Question.parent_chapter_id == paper.chapter_id).all()
    question_map = {q.id: q for q in questions}
    answer_map = {a["question_id"]: a["user_answer"] for a in answers}

    total_questions = len(questions)
    correct_count = 0
    details = []

    for q in questions:
        user_ans = answer_map.get(q.id, "")
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
            "difficulty": q.difficulty,
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

    exam = Exam(
        user_id=user_id,
        chapter_id=paper.chapter_id,
        total_score=total_score,
        score=score,
        time_limit=paper.time_limit,
        time_used=time_used,
    )
    db.add(exam)
    db.flush()

    for d in details:
        det = ExamDetail(
            exam_id=exam.id,
            question_id=d["question_id"],
            user_answer=d["user_answer"],
            is_correct=1 if d["is_correct"] else 0,
            score=d["score"],
        )
        db.add(det)

        if not d["is_correct"]:
            _add_to_wrong_book(db, user_id, d["db_obj"], paper.chapter_id, exam.id)

    db.commit()
    
    feedback = _generate_feedback(chapter_title=paper.title, score=score, details=details)

    return {
        "exam_id": exam.id,
        "paper_id": paper_id,
        "paper_title": paper.title,
        "total_score": total_score,
        "score": score,
        "time_limit": paper.time_limit,
        "time_used": time_used,
        "feedback": feedback,
        "details": [
            {
                "question_id": d["question_id"],
                "stem": d["stem"],
                "type": d["type"],
                "difficulty": d["difficulty"],
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


def _generate_feedback(chapter_title: str, score: float, details: list[dict]) -> str:
    """生成AI反馈"""
    wrong_count = sum(1 for d in details if not d["is_correct"])
    easy_wrong = sum(1 for d in details if not d["is_correct"] and d["difficulty"] == "easy")
    medium_wrong = sum(1 for d in details if not d["is_correct"] and d["difficulty"] == "medium")
    hard_wrong = sum(1 for d in details if not d["is_correct"] and d["difficulty"] == "hard")
    
    wrong_questions = [d for d in details if not d["is_correct"]]
    
    if not wrong_questions:
        return "太棒了！你全部答对了，继续保持！"
    
    wrong_stems = "\n".join([f"- {d['stem'][:100]}..." for d in wrong_questions[:5]])
    
    prompt = f"""你是一位学习导师。请根据以下考试结果，给出简洁、鼓励性的反馈。

考试信息：
- 章节：{chapter_title}
- 得分：{score}分
- 错题数：{wrong_count}道
  - 简单题错：{easy_wrong}道
  - 中等题错：{medium_wrong}道
  - 困难题错：{hard_wrong}道

错题题干：
{wrong_stems}

请给出：
1. 总体评价（鼓励为主）
2. 薄弱环节分析
3. 学习建议

回复不要超过200字，语气友好。"""

    llm = get_llm()
    response = llm.invoke(prompt)
    return response.content.strip()


def _q_to_dict(q):
    """将 Question ORM 转为字典"""
    options = json.loads(q.options) if isinstance(q.options, str) else q.options
    if isinstance(options, dict):
        options_list = [{"key": k, "text": v} for k, v in options.items()]
    else:
        options_list = options
    return {
        "id": q.id,
        "chapter_id": q.chapter_id,
        "parent_chapter_id": q.parent_chapter_id,
        "type": q.type,
        "difficulty": q.difficulty,
        "stem": q.stem,
        "options": options_list,
        "answer": q.answer,
        "explanation": q.explanation,
        "created_at": q.created_at.isoformat() if q.created_at else "",
    }


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