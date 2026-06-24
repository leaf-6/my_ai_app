from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import jwt, JWTError
from pydantic import BaseModel
import uuid
import hashlib
import secrets
from app.config import Config
from app.database import get_db
from app.models import User

router = APIRouter(prefix="/api", tags=["auth"])

class AuthRequest(BaseModel):
    username: str
    password: str

# ============================================================
# 密码加密（使用 hashlib，无外部依赖）
# ============================================================
def hash_password(password: str) -> str:
    """生成 盐值:哈希值 格式的密码"""
    salt = secrets.token_hex(16)
    hash_value = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{hash_value}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码是否匹配"""
    try:
        salt, hash_value = hashed_password.split(":")
        return hash_value == hashlib.sha256((salt + plain_password).encode()).hexdigest()
    except ValueError:
        return False

# ============================================================
# JWT 认证
# ============================================================
def create_token(username: str, user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": username, "user_id": user_id, "exp": expire}
    return jwt.encode(payload, Config.SECRET_KEY, algorithm=Config.ALGORITHM)

def decode_token(token: str):
    try:
        return jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.ALGORITHM])
    except JWTError:
        return None

def get_current_user_id(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供认证信息")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="认证格式错误")
    token = parts[1]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效或过期的Token")
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token缺少用户信息")
    return user_id

# ============================================================
# 路由
# ============================================================
@router.post("/register")
def register(auth: AuthRequest, db: Session = Depends(get_db)):
    username = auth.username
    password = auth.password
    
    # 检查用户名是否已存在
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    user_id = str(uuid.uuid4()).replace("-", "")[:16]
    hashed = hash_password(password)
    user = User(id=user_id, username=username, password_hash=hashed)
    db.add(user)
    db.commit()
    
    token = create_token(username, user_id)
    return {"token": token, "user_id": user_id, "username": username}

@router.post("/login")
def login(auth: AuthRequest, db: Session = Depends(get_db)):
    username = auth.username
    password = auth.password
    
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    token = create_token(user.username, user.id)
    return {"token": token, "user_id": user.id, "username": user.username}