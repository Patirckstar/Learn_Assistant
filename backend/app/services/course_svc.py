"""课程服务 — 大纲刷新、学习内容、进度管理"""

import json
import logging

from sqlalchemy.orm import Session

from app.core.llm import get_llm
from app.models.chapter import Chapter
from app.models.document import Document
from app.models.progress import Progress
from app.utils.file_parser import parse_file

logger = logging.getLogger(__name__)


# ====================== 大纲刷新 ======================


def refresh_outline(db: Session, progress_callback=None) -> list[Chapter]:
    """
    刷新课程大纲：
    - 检测知识库中未制成课程的文档
    - 每份文档生成一个独立课程（一章）
    - 已有课程不动
    
    progress_callback: 进度回调函数，接收参数 (current, total, message)
    """
    llm = get_llm()
    documents = db.query(Document).order_by(Document.uploaded_at).all()
    if not documents:
        raise ValueError("知识库为空，请先上传文档")

    # 找出已处理过的文档 ID
    processed_doc_ids = set()
    existing_chapters = db.query(Chapter).filter(Chapter.source_doc_id.isnot(None)).all()
    for ch in existing_chapters:
        if ch.source_doc_id:
            processed_doc_ids.add(ch.source_doc_id)

    # 需要处理的新文档
    new_docs = [doc for doc in documents if doc.id not in processed_doc_ids]
    total = len(new_docs)
    
    if progress_callback:
        progress_callback(0, total, "开始刷新课程大纲...")

    # 找出最大 sort_order（新课程追加在后面）
    max_order = db.query(Chapter.sort_order).order_by(Chapter.sort_order.desc()).first()
    next_order = (max_order[0] + 1) if max_order and max_order[0] else 1

    new_chapters = []
    for index, doc in enumerate(new_docs):
        current = index + 1
        
        if progress_callback:
            progress_callback(current, total, f"正在处理文档: {doc.filename}")

        logger.info("为新文档生成课程: id=%d, filename=%s", doc.id, doc.filename)

        # 解析文档原文
        try:
            text = parse_file(doc.file_path)
        except Exception as e:
            logger.warning("解析文档失败: id=%d, error=%s", doc.id, e)
            if progress_callback:
                progress_callback(current, total, f"解析文档失败，跳过: {doc.filename}")
            continue

        if not text or not text.strip():
            logger.warning("文档内容为空: id=%d", doc.id)
            if progress_callback:
                progress_callback(current, total, f"文档内容为空，跳过: {doc.filename}")
            continue

        # 截断文本到安全长度
        doc_text = text[:20000] if len(text) > 20000 else text

        if progress_callback:
            progress_callback(current, total, f"正在生成课程内容...")

        prompt = f"""你是一位课程讲师。请根据以下文档内容，生成一份完整的课程。

文档标题：{doc.filename}

要求：
1. 生成一个章（一级标题）和 3-6 个小节（二级标题）
2. 章标题以文档主题命名
3. 每个小节要包含详细的学习内容（使用 markdown 格式）
4. 内容要系统、详尽，包含核心知识点、概念解释、代码示例等
5. 每小节内容 800-2000 字
6. 语言简洁清晰，适合自学

文档内容：
{doc_text}

返回严格的 JSON 格式（不要包含 markdown 代码块标记）：
{{
  "title": "章标题",
  "sections": [
    {{
      "title": "小节标题",
      "content": "小节详细学习内容（markdown 格式）"
    }}
  ]
}}"""

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
            course_data = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("LLM 返回格式错误，跳过: %s", raw[:200])
            if progress_callback:
                progress_callback(current, total, f"生成格式错误，跳过: {doc.filename}")
            continue

        chapter_title = course_data.get("title", doc.filename)
        sections = course_data.get("sections", [])

        # 创建章
        parent = Chapter(
            title=chapter_title,
            level=1,
            sort_order=next_order,
            source_doc_id=doc.id,
        )
        db.add(parent)
        db.flush()

        # 创建节（含详细内容）
        for sub_order, sec in enumerate(sections, 1):
            child = Chapter(
                parent_id=parent.id,
                title=sec.get("title", f"第{sub_order}节"),
                content=sec.get("content", ""),
                level=2,
                sort_order=sub_order,
                source_doc_id=doc.id,
            )
            db.add(child)

        next_order += 1
        new_chapters.append(parent)

        if progress_callback:
            progress_callback(current, total, f"课程生成完成: {chapter_title}")

    db.commit()
    
    if progress_callback:
        progress_callback(total, total, f"大纲刷新完成，新增 {len(new_chapters)} 个课程")

    logger.info("大纲刷新完成，新增 %d 个课程", len(new_chapters))

    result = db.query(Chapter).order_by(Chapter.level, Chapter.sort_order).all()
    return result


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
    results = store.similarity_search(chapter.title, k=30)
    related_texts = [doc.page_content for doc in results]
    knowledge = "\n".join(related_texts) if related_texts else "暂无相关知识"
    if len(knowledge) > 18000:
        knowledge = knowledge[:18000] + "..."

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
