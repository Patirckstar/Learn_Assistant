"""知识库 API 路由"""

from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile, File, Query, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.knowledge import DocumentOut, KnowledgeSearchOut, SearchResult
from app.services import knowledge_svc
from app.utils.embeddings import search_knowledge

router = APIRouter(prefix="/api/knowledge", tags=["知识库"])


@router.post("/upload", response_model=DocumentOut)
def upload_document(
    file: UploadFile = File(...),
    bg_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
):
    """上传文档（支持 pdf / docx / txt / md / ppt / json）"""
    allowed_types = {".pdf", ".docx", ".txt", ".md", ".ppt", ".pptx", ".json"}
    ext = f".{file.filename.rsplit('.', 1)[-1].lower()}" if "." in file.filename else ""
    if ext not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {ext}，支持的格式: {', '.join(allowed_types)}",
        )

    doc, text = knowledge_svc.upload_document(db, file)

    # 后台异步向量化，不阻塞上传响应
    if bg_tasks:
        bg_tasks.add_task(knowledge_svc.vectorize_document, doc.id, doc.filename, text)

    return doc


@router.get("/documents", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db)):
    """获取已上传文档列表"""
    return knowledge_svc.get_documents(db)


@router.delete("/documents/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    """删除文档（同步清理向量索引）"""
    success = knowledge_svc.delete_document(db, doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="文档不存在")
    return {"message": "删除成功"}


@router.get("/search", response_model=KnowledgeSearchOut)
def search(query: str = Query(..., description="搜索关键词"), k: int = Query(5, ge=1, le=20)):
    """语义搜索知识库"""
    results = search_knowledge(query, k=k)
    return KnowledgeSearchOut(
        query=query,
        results=[SearchResult(**r) for r in results],
    )
