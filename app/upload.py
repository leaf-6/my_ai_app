from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user_id
from app.rag import add_documents_to_store

router = APIRouter(prefix="/api/upload", tags=["upload"])

@router.post("/document")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """上传文档到知识库"""
    # 检查文件类型
    allowed_extensions = ['pdf', 'docx', 'txt']
    ext = file.filename.split('.')[-1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型，请上传: {', '.join(allowed_extensions)}"
        )
    
    # 检查文件大小（限制 10MB）
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件超过 10MB 限制")
    
    try:
        chunk_count = add_documents_to_store(content, file.filename, user_id)
        return {
            "status": "ok",
            "message": f"文档 '{file.filename}' 上传成功",
            "chunks": chunk_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理文档失败: {str(e)}")