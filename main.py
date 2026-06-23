from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from zhipuai import ZhipuAI
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from starlette.responses import Response
from jose import jwt, JWTError
from passlib.context import CryptContext
import os
import json
import time
import uuid
import random
from dotenv import load_dotenv

from database import SessionLocal, Session as DBSession, Message, init_db, User

load_dotenv()
init_db()

app = FastAPI(title="AI聊天机器人")

# ============================================================
# 认证配置
# ============================================================
SECRET_KEY = "your-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_token(username: str, user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": username, "user_id": user_id, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
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
# 跨域与静态文件
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope) -> Response:
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

@app.get("/", response_class=HTMLResponse)
def get_chat_page():
    html_path = os.path.join("static", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content, headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        })
    return HTMLResponse(content="<h1>index.html 未找到</h1>", status_code=404)

app.mount("/static", NoCacheStaticFiles(directory="static"), name="static")

# ============================================================
# 请求模型
# ============================================================
class ChatRequest(BaseModel):
    message: str
    user_id: str = "anonymous"
    model: str = "glm-4-flash"

class SessionCreate(BaseModel):
    title: str = "新对话"

class AuthRequest(BaseModel):
    username: str
    password: str

# ============================================================
# 数据库依赖
# ============================================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================================
# 认证接口 (关键：参数是 auth: AuthRequest)
# ============================================================
@app.post("/api/register")
def register(auth: AuthRequest, db: Session = Depends(get_db)):
    username = auth.username
    password = auth.password
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

@app.post("/api/login")
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

# ============================================================
# 会话管理接口
# ============================================================
@app.get("/api/sessions")
def get_sessions(db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    sessions = db.query(DBSession).filter(DBSession.user_id == user_id).order_by(DBSession.updated_at.desc()).all()
    return [{"id": s.id, "title": s.title, "message_count": db.query(Message).filter(Message.session_id == s.id).count(), "updated_at": s.updated_at.isoformat()} for s in sessions]

@app.post("/api/sessions")
def create_session(data: SessionCreate, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    session_id = str(int(time.time() * 1000)) + hex(random.randint(0, 65536))[2:]
    session = DBSession(id=session_id, user_id=user_id, title=data.title)
    db.add(session)
    db.commit()
    return {"id": session_id, "title": session.title}

@app.delete("/api/sessions/{session_id}")
def delete_session(session_id: str, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    session = db.query(DBSession).filter(DBSession.id == session_id, DBSession.user_id == user_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在或无权限")
    db.query(Message).filter(Message.session_id == session_id).delete()
    db.delete(session)
    db.commit()
    return {"ok": True}

@app.get("/api/sessions/{session_id}/messages")
def get_messages(session_id: str, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    session = db.query(DBSession).filter(DBSession.id == session_id, DBSession.user_id == user_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在或无权限")
    messages = db.query(Message).filter(Message.session_id == session_id).order_by(Message.timestamp).all()
    return [{"text": m.text, "sender": m.sender, "timestamp": m.timestamp.isoformat()} for m in messages]

# ============================================================
# 核心聊天接口
# ============================================================
@app.post("/chat")
def chat(request: ChatRequest, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    session_id = request.user_id if request.user_id != "anonymous" else user_id
    session = db.query(DBSession).filter(DBSession.id == session_id, DBSession.user_id == user_id).first()
    if not session:
        session = DBSession(id=session_id, user_id=user_id, title="新对话")
        db.add(session)
        db.commit()

    user_msg = Message(session_id=session_id, user_id=user_id, sender="user", text=request.message)
    db.add(user_msg)
    db.commit()

    history = db.query(Message).filter(Message.session_id == session_id).order_by(Message.timestamp.desc()).limit(10).all()
    history.reverse()
    messages_for_ai = [{"role": "system", "content": "你是一个友好的AI助手，用中文回复。"}]
    for msg in history:
        role = "user" if msg.sender == "user" else "assistant"
        messages_for_ai.append({"role": role, "content": msg.text})

    def generate():
        full_reply = ""
        try:
            model_name = request.model
            if model_name.startswith("glm-"):
                api_key = os.getenv("ZHIPU_API_KEY")
                if not api_key:
                    yield f"data: {json.dumps({'content': '❌ 未配置智谱API Key', 'done': True, 'error': True})}\n\n"
                    return
                client = ZhipuAI(api_key=api_key)
                response = client.chat.completions.create(model=model_name, messages=messages_for_ai, stream=True, max_tokens=500)
                for chunk in response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_reply += content
                        yield f"data: {json.dumps({'content': content, 'done': False})}\n\n"
            elif model_name.startswith("deepseek"):
                from openai import OpenAI
                api_key = os.getenv("DEEPSEEK_API_KEY")
                if not api_key:
                    yield f"data: {json.dumps({'content': '❌ 未配置DeepSeek API Key', 'done': True, 'error': True})}\n\n"
                    return
                client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")
                response = client.chat.completions.create(model=model_name, messages=messages_for_ai, stream=True, max_tokens=500)
                for chunk in response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_reply += content
                        yield f"data: {json.dumps({'content': content, 'done': False})}\n\n"
            else:
                yield f"data: {json.dumps({'content': '❌ 不支持的模型', 'done': True, 'error': True})}\n\n"
                return
            yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"
            if full_reply:
                ai_msg = Message(session_id=session_id, user_id=user_id, sender="ai", text=full_reply)
                db.add(ai_msg)
                db.commit()
                if session.title == "新对话":
                    first_user = db.query(Message).filter(Message.session_id == session_id, Message.sender == "user").order_by(Message.timestamp).first()
                    if first_user:
                        session.title = first_user.text[:20] + ("..." if len(first_user.text) > 20 else "")
                        db.commit()
        except Exception as e:
            yield f"data: {json.dumps({'content': '❌ AI调用失败: ' + str(e), 'done': True, 'error': True})}\n\n"
            print(f"流式错误: {e}")

    return StreamingResponse(generate(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"
    })

@app.get("/ping")
def ping():
    return {"status": "ok", "info": "服务正常运行"}