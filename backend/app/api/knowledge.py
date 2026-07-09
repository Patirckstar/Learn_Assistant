"""知识库 API 路由"""

from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.llm import get_llm
from app.schemas.knowledge import DocumentOut, KnowledgeAskOut, KnowledgeSearchOut, SearchResult
from app.services import knowledge_svc
from app.utils.embeddings import search_knowledge
from app.utils.task_queue import task_queue

router = APIRouter(prefix="/api/knowledge", tags=["知识库"])


@router.post("/upload", response_model=DocumentOut)
def upload_document(
    file: UploadFile = File(...),
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

    # 检查文件大小
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    file.file.seek(0, 2)  # 移到末尾
    file_size = file.file.tell()
    file.file.seek(0)  # 重置到开头
    if file_size > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"文件过大（{file_size / 1024 / 1024:.1f}MB），最大允许 {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    doc, text = knowledge_svc.upload_document(db, file)

    # 使用任务队列处理向量化，不阻塞上传响应
    task_queue.enqueue("vectorize", {
        "doc_id": doc.id,
        "filename": doc.filename,
        "file_path": doc.file_path,
    })

    return doc


@router.get("/tasks/{task_id}/status")
def get_task_status(task_id: str):
    """查询任务状态"""
    status = task_queue.get_status(task_id)
    return {"task_id": task_id, "status": status}


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
    """语义搜索知识库，返回匹配的文档片段"""
    results = search_knowledge(query, k=k)
    return KnowledgeSearchOut(
        query=query,
        results=[SearchResult(**r) for r in results],
    )


@router.get("/ask", response_model=KnowledgeAskOut)
def ask(query: str = Query(..., description="提问内容"), k: int = Query(5, ge=1, le=10)):
    """基于知识库的 AI 问答：检索相关内容后由 LLM 总结回答"""
    source_results = search_knowledge(query, k=k)
    sources = [SearchResult(**r) for r in source_results]

    if not sources:
        return KnowledgeAskOut(
            query=query,
            answer="知识库中没有找到与您问题相关的内容，请先上传相关文档。",
            sources=[],
        )

    # 拼接上下文
    context_parts = []
    for i, s in enumerate(sources, 1):
        context_parts.append(f"[来源{i}] {s.filename}:\n{s.content}")

    context = "\n\n".join(context_parts)

    prompt = f"""你是一个学习助手。请根据以下知识库内容回答用户的问题。
如果知识库内容不足以回答问题，请如实告知。

知识库内容：
{context}

用户问题：{query}

请用中文回答，简洁清晰，引用时标注来源编号如 [来源1]。"""

    try:
        llm = get_llm()
        response = llm.invoke(prompt)
        answer = response.content if hasattr(response, "content") else str(response)
    except Exception:
        answer = "AI 回答生成失败，请确保 Ollama 服务正常运行。以下是检索到的相关内容（仅供参考）：\n\n" + context

    return KnowledgeAskOut(
        query=query,
        answer=answer,
        sources=sources,
    )
