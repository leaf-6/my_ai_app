from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from zhipuai import ZhipuAI
from sqlalchemy.orm import Session
from datetime import datetime
import os
from dotenv import load_dotenv
from fastapi.responses import StreamingResponse
import json

# 导入数据库模块
from database import SessionLocal, Session as DBSession, Message, init_db

load_dotenv()

# 初始化数据库（首次运行建表）
init_db()

app = FastAPI(title="AI聊天机器人")

# 跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 根页面
@app.get("/", response_class=HTMLResponse)
def get_chat_page():
    html_path = os.path.join("static", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return HTMLResponse(content="<h1>index.html 未找到</h1>", status_code=404)

# ----- 请求/响应模型 -----
class ChatRequest(BaseModel):
    message: str
    user_id: str = "anonymous"

class SessionCreate(BaseModel):
    title: str = "新对话"

# ----- 数据库依赖 -----
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================================
# API 接口
# ============================================================

# 1. 获取所有会话列表
@app.get("/api/sessions")
def get_sessions(db: Session = Depends(get_db)):
    sessions = db.query(DBSession).order_by(DBSession.updated_at.desc()).all()
    return [
        {
            "id": s.id,
            "title": s.title,
            "message_count": db.query(Message).filter(Message.session_id == s.id).count(),
            "updated_at": s.updated_at.isoformat()
        }
        for s in sessions
    ]

# 2. 创建新会话
@app.post("/api/sessions")
def create_session(data: SessionCreate, db: Session = Depends(get_db)):
    import time
    import random
    session_id = str(int(time.time() * 1000)) + hex(random.randint(0, 65536))[2:]
    session = DBSession(id=session_id, title=data.title)
    db.add(session)
    db.commit()
    return {"id": session_id, "title": session.title}

# 3. 获取某个会话的所有消息
@app.get("/api/sessions/{session_id}/messages")
def get_messages(session_id: str, db: Session = Depends(get_db)):
    messages = db.query(Message).filter(Message.session_id == session_id).order_by(Message.timestamp).all()
    return [
        {"text": m.text, "sender": m.sender, "timestamp": m.timestamp.isoformat()}
        for m in messages
    ]

# 4. 删除会话（级联删除消息）
@app.delete("/api/sessions/{session_id}")
def delete_session(session_id: str, db: Session = Depends(get_db)):
    # 先删消息
    db.query(Message).filter(Message.session_id == session_id).delete()
    # 再删会话
    session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if session:
        db.delete(session)
    db.commit()
    return {"ok": True}

# 5. 核心聊天接口（同时存入数据库）
@app.post("/chat")
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    session_id = request.user_id if request.user_id != "anonymous" else "default"

    # 检查会话是否存在
    session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if not session:
        session = DBSession(id=session_id, title="新对话")
        db.add(session)
        db.commit()

    # 保存用户消息
    user_msg = Message(session_id=session_id, sender="user", text=request.message)
    db.add(user_msg)
    db.commit()

    # 调用AI（流式）
    api_key = os.getenv("ZHIPU_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="未设置 ZHIPU_API_KEY")

    client = ZhipuAI(api_key=api_key)

    # 获取历史消息（最近10条）
    history = db.query(Message).filter(
        Message.session_id == session_id
    ).order_by(Message.timestamp.desc()).limit(10).all()
    history.reverse()

    messages_for_ai = [
        {"role": "system", "content": "你是一个友好的AI助手，用中文回复。"}
    ]
    for msg in history:
        role = "user" if msg.sender == "user" else "assistant"
        messages_for_ai.append({"role": role, "content": msg.text})

    # ============================================================
    # 流式生成器
    # ============================================================
    def generate():
        full_reply = ""
        try:
            # 调用智谱流式接口
            response = client.chat.completions.create(
                model="glm-4-flash",
                messages=messages_for_ai,
                stream=True,  # 关键：开启流式
                max_tokens=500
            )

            # 逐块返回
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_reply += content
                    # 每个chunk以SSE格式发送
                    yield f"data: {json.dumps({'content': content, 'done': False})}\n\n"

            # 发送完成信号
            yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"

            # 保存完整回复到数据库
            ai_msg = Message(session_id=session_id, sender="ai", text=full_reply)
            db.add(ai_msg)
            db.commit()

            # 更新会话标题
            if session.title == "新对话":
                first_user = db.query(Message).filter(
                    Message.session_id == session_id,
                    Message.sender == "user"
                ).order_by(Message.timestamp).first()
                if first_user:
                    session.title = first_user.text[:20] + ("..." if len(first_user.text) > 20 else "")
                    db.commit()

        except Exception as e:
            # 发生错误时发送错误信息
            error_msg = f"AI调用失败: {str(e)}"
            yield f"data: {json.dumps({'content': '❌ ' + error_msg, 'done': True, 'error': True})}\n\n"
            print(f"流式错误: {e}")

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用nginx缓冲
        }
    )


# 6. 健康检查
@app.get("/ping")
def ping():
    return {"status": "ok", "info": "服务正常运行"}