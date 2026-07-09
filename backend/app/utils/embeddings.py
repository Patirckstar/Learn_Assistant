"""向量化存储工具 — ChromaDB + sentence-transformers"""

import os
import ssl
import urllib3

# Windows SSL 证书问题：多层禁用 SSL 验证
# 1. Python 原生 ssl
ssl._create_default_https_context = ssl._create_unverified_context
# 2. urllib3（requests 底层）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# 3. 环境变量
os.environ.setdefault("HF_HUB_DISABLE_SSL_VERIFICATION", "1")
os.environ.setdefault("CURL_CA_BUNDLE", "")
os.environ.setdefault("REQUESTS_CA_BUNDLE", "")
# 4. 直接 patch requests 的 verify 行为（huggingface_hub 使用 requests）
import requests as _requests
_original_request = _requests.Session.request
def _patched_request(self, method, url, **kwargs):
    kwargs.setdefault("verify", False)
    return _original_request(self, method, url, **kwargs)
_requests.Session.request = _patched_request

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
        model_path = os.path.abspath(settings.EMBEDDING_MODEL)
        _embeddings = HuggingFaceEmbeddings(
            model_name=model_path,
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
    if not text or not text.strip():
        return 0

    docs = split_text(text)
    if not docs:
        return 0

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


def clear_all():
    """清空 ChromaDB 中所有向量数据"""
    store = get_vector_store()
    all_ids = store.get().get("ids", [])
    if all_ids:
        store.delete(ids=all_ids)


def batch_add_documents(docs_list: list[tuple[int, str, str]]) -> int:
    """批量向量化多个文档，返回总块数"""
    store = get_vector_store()
    total = 0
    for file_id, filename, text in docs_list:
        docs = split_text(text)
        for i, doc in enumerate(docs):
            doc.metadata = {
                "file_id": file_id,
                "filename": filename,
                "chunk_index": i,
            }
        store.add_documents(docs)
        total += len(docs)
    return total


def search_knowledge(query: str, k: int = 5) -> list[dict]:
    """语义搜索知识库，返回最相关的 k 个片段（过滤无关结果）"""
    store = get_vector_store()
    results = store.similarity_search_with_score(query, k=k * 2)  # 多捞一些再过滤

    output = []
    for doc, distance in results:
        # 余弦距离 0~2，转换为 0~1 的相关度（1=完全匹配，0=完全不相关）
        relevance = max(0.0, 1.0 - float(distance) / 2.0)
        # 过滤掉相关度 < 30% 的噪音结果
        if relevance < 0.3:
            continue
        output.append({
            "content": doc.page_content,
            "score": round(relevance, 4),
            "file_id": doc.metadata.get("file_id"),
            "filename": doc.metadata.get("filename"),
            "chunk_index": doc.metadata.get("chunk_index"),
        })

    # 截取 top k
    return output[:k]
