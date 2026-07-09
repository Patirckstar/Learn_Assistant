import os
from urllib.parse import quote_plus
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "AI学习助手"
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-here"
    API_V1_PREFIX: str = "/api"

    # MySQL 数据库
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "your-password"
    DB_NAME: str = "learn_assistant"

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{quote_plus(self.DB_PASSWORD)}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"

    # Ollama 本地模型
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b"

    # Embedding 模型（本地路径，首次运行需下载到该目录）
    EMBEDDING_MODEL: str = "./models/all-MiniLM-L6-v2"

    # ChromaDB
    CHROMA_PERSIST_DIR: str = "./data/chroma"

    # 文件上传
    UPLOAD_DIR: str = "./data/uploads"
    MAX_UPLOAD_SIZE_MB: int = 50

    # 人脸识别
    FACE_TOLERANCE: float = 0.6
    FACE_STORAGE_DIR: str = "./data/faces"

    # 语音
    VOICE_LANGUAGE: str = "zh-CN"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
