"""知识库服务 — 文档上传、解析、向量化、CRUD"""

import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document
from app.utils.file_parser import parse_file
from app.utils.embeddings import add_document as vector_add
from app.utils.embeddings import delete_document as vector_delete


def upload_document(db: Session, file) -> tuple[Document, str]:
    """
    上传文档：
    1. 保存文件到本地
    2. 解析文本内容
    3. 记录文档信息到 MySQL
    返回 (文档对象, 解析后的文本)
    """
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename).suffix
    unique_name = f"{uuid.uuid4().hex}{ext}"
    save_path = upload_dir / unique_name

    content = file.file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    file_size = len(content)
    file_type = ext.lower().lstrip(".")

    text = parse_file(str(save_path))

    doc = Document(
        filename=file.filename,
        file_type=file_type,
        file_path=str(save_path),
        file_size=file_size,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return doc, text


def _revectorize_all(db: Session):
    """重新向量化所有文档（逐文档替换，不中断搜索）"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info("触发全量重新向量化")

    docs = db.query(Document).order_by(Document.uploaded_at).all()
    if not docs:
        return

    for doc in docs:
        try:
            # 先清除旧向量 → 再向量化新内容（最多丢失 1 个文档）
            vector_delete(doc.id)
            text = parse_file(doc.file_path)
            chunk_count = vector_add(doc.id, doc.filename, text)
            doc.chunk_count = chunk_count
        except Exception as e:
            logger.warning("文档重新向量化失败: id=%d, filename=%s, error=%s", doc.id, doc.filename, e)
            doc.chunk_count = 0

    db.commit()
    logger.info("全量重新向量化完成，共 %d 个文档", len(docs))


def vectorize_document(doc_id: int, filename: str, text: str):
    """后台执行向量化，完成后更新 chunk_count
    每新增 10 个文档时，自动触发全量重新向量化（清空 + 重建）
    """
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        chunk_count = vector_add(doc_id, filename, text)
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if doc:
            doc.chunk_count = chunk_count
            db.commit()

        # 每 10 个文档触发全量重新向量化
        total_docs = db.query(Document).count()
        if total_docs > 0 and total_docs % 10 == 0:
            _revectorize_all(db)

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error("向量化失败: doc_id=%d, error=%s", doc_id, e)
    finally:
        db.close()


def get_documents(db: Session) -> list[Document]:
    """获取所有已上传文档"""
    return db.query(Document).order_by(Document.uploaded_at.desc()).all()


def delete_document(db: Session, doc_id: int) -> bool:
    """删除文档（同时清理向量库）"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        return False

    if Path(doc.file_path).exists():
        Path(doc.file_path).unlink()

    try:
        vector_delete(doc_id)
    except Exception:
        pass

    db.delete(doc)
    db.commit()
    return True
