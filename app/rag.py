import os
import tempfile
from typing import Dict, List
from app.config import Config

# ============================================================
# 存储用户上传的文档内容
# ============================================================
_user_docs: Dict[str, str] = {}

def read_file_content(file_content: bytes, filename: str) -> str:
    """读取文件内容为纯文本"""
    ext = filename.split('.')[-1].lower()
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
        tmp.write(file_content)
        tmp_path = tmp.name
    
    try:
        if ext == 'pdf':
            from pypdf import PdfReader
            reader = PdfReader(tmp_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
        elif ext == 'docx':
            import docx2txt
            return docx2txt.process(tmp_path)
        else:
            with open(tmp_path, 'r', encoding='utf-8') as f:
                return f.read()
    finally:
        os.unlink(tmp_path)


def add_documents_to_store(file_content: bytes, filename: str, user_id: str) -> int:
    """存储文档全文（直接存，不切分、不向量化）"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("📖 开始读取文档...")
    text = read_file_content(file_content, filename)
    if not text:
        logger.warning("⚠️ 文档内容为空")
        return 0
    
    # 限制长度，防止超 token
    if len(text) > 5000:
        text = text[:5000] + "\n...(文档过长，已截取前5000字符)"
    
    _user_docs[user_id] = text
    logger.info(f"✅ 已存储文档: {filename}，共 {len(text)} 字符")
    return 1


def get_rag_context(query: str, user_id: str) -> str:
    """直接返回用户上传的文档全文"""
    if user_id not in _user_docs:
        return ""
    
    doc_content = _user_docs[user_id]
    return f"""
用户上传了一份文档，全文如下：
---
{doc_content}
---
请严格根据以上文档内容回答用户的问题。
如果文档中没有相关信息，请直接说"文档中未找到相关内容"。
绝对不要说"我无法访问文件"或"我没有看到文档"，因为文档内容已经提供给你了。
"""


def delete_user_store(user_id: str) -> bool:
    """删除用户的文档"""
    if user_id in _user_docs:
        del _user_docs[user_id]
        return True
    return False