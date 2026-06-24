from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader
from app.config import Config
import os
import tempfile

# 使用 HuggingFace 的免费 embedding 模型
# 首次使用时会自动下载（约 100MB）
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

def get_vector_store(collection_name: str):
    """获取向量数据库实例"""
    return Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=Config.VECTOR_DB_PATH
    )

def process_document(file_content: bytes, filename: str) -> list:
    """
    处理上传的文档，返回文本内容
    支持 PDF、Word、TXT
    """
    # 获取文件扩展名
    ext = filename.split('.')[-1].lower()
    
    # 保存为临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
        tmp.write(file_content)
        tmp_path = tmp.name
    
    try:
        # 根据文件类型加载
        if ext == 'pdf':
            loader = PyPDFLoader(tmp_path)
        elif ext == 'docx':
            loader = Docx2txtLoader(tmp_path)
        else:  # txt 或其他
            loader = TextLoader(tmp_path, encoding='utf-8')
        
        documents = loader.load()
        return documents
    finally:
        # 删除临时文件
        os.unlink(tmp_path)

def split_documents(documents, chunk_size=500, chunk_overlap=50):
    """将文档切成小块，便于检索"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", "！", "？", "，", " ", ""]
    )
    return text_splitter.split_documents(documents)

def add_documents_to_store(file_content: bytes, filename: str, user_id: str) -> int:
    """处理并添加文档到向量数据库"""
    # 1. 加载文档
    documents = process_document(file_content, filename)
    
    # 2. 切成小块
    chunks = split_documents(documents)
    
    # 3. 存入向量数据库（按用户隔离）
    collection_name = f"user_{user_id}"
    vector_store = get_vector_store(collection_name)
    
    # 添加文档
    vector_store.add_documents(chunks)
    vector_store.persist()
    
    return len(chunks)

def search_similar(query: str, user_id: str, k: int = 5) -> list:
    """搜索与查询相关的文档片段"""
    collection_name = f"user_{user_id}"
    vector_store = get_vector_store(collection_name)
    
    # 检查是否有数据
    try:
        results = vector_store.similarity_search(query, k=k)
        return results
    except Exception:
        return []

def get_rag_context(query: str, user_id: str) -> str:
    """获取 RAG 上下文（用于提示词）"""
    results = search_similar(query, user_id, k=5)
    if not results:
        return ""
    
    context_parts = ["以下是从文档中检索到的相关信息：\n"]
    for i, doc in enumerate(results, 1):
        context_parts.append(f"{i}. {doc.page_content}\n")
    
    return "\n".join(context_parts)