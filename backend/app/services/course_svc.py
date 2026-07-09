"""课程服务 — 大纲生成、学习内容、进度管理"""

import json

from sqlalchemy.orm import Session

from app.core.llm import get_llm
from app.models.chapter import Chapter
from app.models.progress import Progress


# ====================== 大纲生成 ======================


def generate_outline(db: Session) -> list[Chapter]:
    """基于知识库内容，调用 LLM 生成课程大纲"""
    llm = get_llm()

    # 从 ChromaDB 获取知识库概要
    from app.utils.embeddings import get_vector_store
    store = get_vector_store()
    all_docs = store.get()
    texts = all_docs.get("documents", [])
    knowledge_summary = "\n".join(texts[:20]) if texts else "暂无知识库内容"
    # 截断避免超出 token 限制
    if len(knowledge_summary) > 8000:
        knowledge_summary = knowledge_summary[:8000] + "..."

    prompt = f"""你是一位课程设计专家。请根据以下知识库内容，生成一份层级清晰的课程大纲。

要求：
1. 大纲至少包含"章"和"节"两级
2. 章的数量 3-8 章，每章下 2-5 节
3. 章节标题简洁明了
4. 返回 JSON 数组格式，不要包含 markdown 代码块标记

知识库内容：
{knowledge_summary}

返回格式（严格 JSON 数组，不要加其他文字）：
[
  {{
    "title": "第一章标题",
    "children": [
      {{"title": "第一节标题"}},
      {{"title": "第二节标题"}}
    ]
  }}
]"""

    response = llm.invoke(prompt)
    raw = response.content.strip()

    # 清理可能的 markdown 代码块标记
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        raw = raw.rsplit("\n", 1)[0]
        if raw.endswith("```"):
            raw = raw[:-3]
    raw = raw.strip()

    try:
        outline_data = json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError(f"LLM 返回格式错误，无法解析: {raw[:200]}")

    # 清空旧大纲并写入新数据
    db.query(Chapter).delete()
    db.commit()

    chapters = []
    for order, chapter_item in enumerate(outline_data, 1):
        parent = Chapter(
            title=chapter_item["title"],
            level=1,
            sort_order=order,
        )
        db.add(parent)
        db.flush()

        children = chapter_item.get("children", [])
        for sub_order, child_item in enumerate(children, 1):
            child = Chapter(
                parent_id=parent.id,
                title=child_item["title"],
                level=2,
                sort_order=sub_order,
            )
            db.add(child)

    db.commit()
    chapters = db.query(Chapter).order_by(Chapter.sort_order).all()
    return chapters


# ====================== 大纲查询 ======================


def get_outline_tree(db: Session) -> list[Chapter]:
    """获取大纲树（所有章节）"""
    return db.query(Chapter).order_by(Chapter.level, Chapter.sort_order).all()


# ====================== 章节学习内容 ======================


def generate_chapter_content(db: Session, chapter_id: int) -> str:
    """为指定章节生成学习内容"""
    llm = get_llm()
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise ValueError("章节不存在")

    # 获取知识库相关内容
    from app.utils.embeddings import get_vector_store
    store = get_vector_store()
    results = store.similarity_search(chapter.title, k=10)
    related_texts = [doc.page_content for doc in results]
    knowledge = "\n".join(related_texts) if related_texts else "暂无相关知识"
    if len(knowledge) > 6000:
        knowledge = knowledge[:6000] + "..."

    prompt = f"""你是一位课程讲师。请根据以下知识库内容，为课程章节「{chapter.title}」生成详细的学习内容。

要求：
1. 内容要系统、有条理，用 markdown 格式
2. 包含核心知识点、关键概念解释
3. 篇幅适中，500-1500 字
4. 语言简洁清晰，适合自学

相关知识：
{knowledge}

请生成学习内容："""

    response = llm.invoke(prompt)
    content = response.content.strip()

    chapter.content = content
    db.commit()

    return content


# ====================== 学习进度 ======================


def get_progress(db: Session, user_id: int) -> list[Progress]:
    """获取用户所有章节的学习进度"""
    chapters = db.query(Chapter).all()
    chapter_ids = [c.id for c in chapters]

    progress_records = (
        db.query(Progress)
        .filter(Progress.user_id == user_id, Progress.chapter_id.in_(chapter_ids))
        .all()
    )
    progress_map = {p.chapter_id: p for p in progress_records}

    result = []
    for ch in chapters:
        if ch.id in progress_map:
            result.append(progress_map[ch.id])
        else:
            result.append(
                Progress(
                    user_id=user_id,
                    chapter_id=ch.id,
                    status="not_started",
                )
            )
    return result


def update_progress(db: Session, user_id: int, chapter_id: int, status: str):
    """更新章节进度"""
    from datetime import datetime

    progress = (
        db.query(Progress)
        .filter(Progress.user_id == user_id, Progress.chapter_id == chapter_id)
        .first()
    )

    if not progress:
        progress = Progress(
            user_id=user_id,
            chapter_id=chapter_id,
            status=status,
            started_at=datetime.now() if status == "learning" else None,
        )
        db.add(progress)
    else:
        progress.status = status
        if status == "learning" and not progress.started_at:
            progress.started_at = datetime.now()
        if status == "completed":
            progress.completed_at = datetime.now()

    db.commit()
    return progress


def get_dashboard(db: Session, user_id: int) -> dict:
    """获取进度看板数据"""
    chapters = db.query(Chapter).filter(Chapter.level == 2).count()
    if chapters == 0:
        return {
            "total_chapters": 0,
            "completed": 0,
            "learning": 0,
            "not_started": 0,
            "percent": 0,
            "detail": [],
        }

    progress_list = get_progress(db, user_id)
    completed = sum(1 for p in progress_list if p.status == "completed")
    learning = sum(1 for p in progress_list if p.status == "learning")
    not_started = sum(1 for p in progress_list if p.status == "not_started")

    return {
        "total_chapters": len(progress_list),
        "completed": completed,
        "learning": learning,
        "not_started": not_started,
        "percent": round(completed / len(progress_list) * 100, 1) if progress_list else 0,
        "detail": [
            {
                "chapter_id": p.chapter_id,
                "status": p.status,
                "started_at": p.started_at,
                "completed_at": p.completed_at,
            }
            for p in progress_list
        ],
    }


def reset_progress(db: Session, user_id: int):
    """重置所有进度"""
    db.query(Progress).filter(Progress.user_id == user_id).delete()
    db.commit()
