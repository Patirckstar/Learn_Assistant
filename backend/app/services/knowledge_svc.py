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


def vectorize_document(doc_id: int, filename: str, text: str):
    """后台执行向量化（不阻塞上传请求）"""
    try:
        chunk_count = vector_add(doc_id, filename, text)
        # 注：这里无法直接用 db session，需要在调用方处理
        # 实际可在 API 层开新 session 更新 chunk_count
    except Exception as e:
        pass


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
