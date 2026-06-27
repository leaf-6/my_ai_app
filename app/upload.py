from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
import logging
from app.database import get_db
from app.auth import get_current_user_id
from app.rag import add_documents_to_store

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/upload", tags=["upload"])

@router.post("/document")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    logger.info(f"📤 收到上传请求: {file.filename}, 用户: {user_id}")
    
    allowed_extensions = ['pdf', 'docx', 'txt']
    ext = file.filename.split('.')[-1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型，请上传: {', '.join(allowed_extensions)}"
        )
    
    content = await file.read()
    logger.info(f"📄 文件大小: {len(content)} bytes")
    
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件超过 10MB 限制")
    
    try:
        logger.info(f"🔍 开始处理文档...")
        chunk_count = add_documents_to_store(content, file.filename, user_id)
        logger.info(f"✅ 处理完成，共 {chunk_count} 个片段")
        return {
            "status": "ok",
            "message": f"文档 '{file.filename}' 上传成功",
            "chunks": chunk_count
        }
    except Exception as e:
        logger.error(f"❌ 处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理文档失败: {str(e)}")