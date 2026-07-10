import ssl

# Windows SSL 证书问题
ssl._create_default_https_context = ssl._create_unverified_context

from langchain_ollama import ChatOllama
from langchain_community.embeddings import HuggingFaceEmbeddings

from app.core.config import settings


def get_llm():
    return ChatOllama(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL,
        temperature=0.1,
    )


def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name=settings.EMBEDDING_MODEL,
    )
