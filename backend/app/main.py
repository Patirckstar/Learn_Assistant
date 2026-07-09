from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, face, knowledge, course, quiz, progress, voice, wrongbook
from app.core.config import settings
from app.core.database import init_db

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


@app.get("/")
def root():
    return {"message": f"{settings.APP_NAME} API is running"}
