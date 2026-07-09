from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, face, knowledge, course, quiz, progress, voice, wrongbook
from app.core.config import settings
from app.core.database import init_db
from app.utils.task_queue import task_queue
from app.utils.file_parser import parse_file
from app.utils.embeddings import add_document as vector_add, delete_document as vector_delete


def handle_vectorize_task(payload):
    """处理向量化任务"""
    import logging
    logger = logging.getLogger(__name__)
    
    doc_id = payload["doc_id"]
    file_path = payload["file_path"]
    
    try:
        text = parse_file(file_path)
        chunk_count = vector_add(doc_id, payload["filename"], text)
        
        from app.core.database import SessionLocal
        db = SessionLocal()
        try:
            from app.models.document import Document
            doc = db.query(Document).filter(Document.id == doc_id).first()
            if doc:
                doc.chunk_count = chunk_count
                db.commit()
        finally:
            db.close()
        
        logger.info("向量化完成: doc_id=%d, chunks=%d", doc_id, chunk_count)
        return {"chunk_count": chunk_count}
    except Exception as e:
        logger.error("向量化失败: doc_id=%d, error=%s", doc_id, e)
        raise


app = FastAPI(
    title=settings.APP_NAME,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router)
app.include_router(face.router)
app.include_router(knowledge.router)
app.include_router(course.router)
app.include_router(quiz.router)
app.include_router(progress.router)
app.include_router(voice.router)
app.include_router(wrongbook.router)


@app.on_event("startup")
def on_startup():
    init_db()
    task_queue.start_worker({
        "vectorize": handle_vectorize_task,
    })
    task_queue.cleanup()


@app.on_event("shutdown")
def on_shutdown():
    task_queue.stop_worker()


@app.get("/")
def root():
    return {"message": f"{settings.APP_NAME} API is running"}
