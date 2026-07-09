"""向量化存储工具 — ChromaDB + sentence-transformers"""

import os

# Windows SSL 证书问题：禁用 HuggingFace Hub 的 SSL 验证
os.environ.setdefault("HF_HUB_DISABLE_SSL_VERIFICATION", "1")

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

from app.core.config import settings

# 全局 Embedding 模型（单例）
_embeddings = None


def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
        )
    return _embeddings


def get_vector_store(collection_name: str = "knowledge_base") -> Chroma:
    """获取或创建 ChromaDB 集合"""
    return Chroma(
        collection_name=collection_name,
        embedding_function=get_embeddings(),
        persist_directory=settings.CHROMA_PERSIST_DIR,
    )


def split_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[Document]:
    """将文本分割成块，返回 Document 列表"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", ".", " ", ""],
    )
    return splitter.create_documents([text])


def add_document(file_id: int, filename: str, text: str) -> int:
    """将解析后的文本分块、向量化并存入 ChromaDB，返回分块数量"""
    docs = split_text(text)

    # 为每个分块添加元数据
    for i, doc in enumerate(docs):
        doc.metadata = {
            "file_id": file_id,
            "filename": filename,
            "chunk_index": i,
        }

    store = get_vector_store()
    store.add_documents(docs)
    store.persist()

    return len(docs)


def delete_document(file_id: int):
    """从 ChromaDB 中删除指定文档的所有分块"""
    store = get_vector_store()
    # 根据 metadata 中的 file_id 过滤删除
    results = store.get(where={"file_id": file_id})
    if results and results.get("ids"):
        store.delete(ids=results["ids"])


def search_knowledge(query: str, k: int = 5) -> list[dict]:
    """语义搜索知识库，返回最相关的 k 个片段"""
    store = get_vector_store()
    results = store.similarity_search_with_score(query, k=k)

    output = []
    for doc, score in results:
        output.append({
            "content": doc.page_content,
            "score": round(float(score), 4),
            "file_id": doc.metadata.get("file_id"),
            "filename": doc.metadata.get("filename"),
            "chunk_index": doc.metadata.get("chunk_index"),
        })
    return output
