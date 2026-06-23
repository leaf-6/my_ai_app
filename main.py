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
from starlette.responses import Response
import time

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

class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope) -> Response:
        response = await super().get_response(path, scope)
        # 强制禁用缓存
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

# 根页面
@app.get("/", response_class=HTMLResponse)
def get_chat_page():
    from fastapi.responses import HTMLResponse
    import time
    html_path = os.path.join("static", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()
        # 加一个随机版本号，强制浏览器刷新
        version = int(time.time())
        return HTMLResponse(
            content=content,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            }
        )
    return HTMLResponse(content="<h1>index.html 未找到</h1>", status_code=404)

# 静态文件挂载（让 /static 可访问）
app.mount("/static", NoCacheStaticFiles(directory="static"), name="static")

# ----- 请求/响应模型 -----
class ChatRequest(BaseModel):
    message: str
    user_id: str = "anonymous"
    model: str = "glm-4-flash"  # 默认使用智谱Flash

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
    db.query(Message).filter(Message.session_id == session_id).delete()
    session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if session:
        db.delete(session)
    db.commit()
    return {"ok": True}

# ============================================================
# 5. 核心聊天接口（支持多模型切换）
# ============================================================
@app.post("/chat")
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    session_id = request.user_id if request.user_id != "anonymous" else "default"
    model_name = request.model  # 从请求中获取模型名称

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
    # 流式生成器（支持智谱 + DeepSeek）
    # ============================================================
    def generate():
        full_reply = ""
        try:
            # ----- 分支1：智谱系列 (glm-4-flash, glm-4-plus) -----
            if model_name.startswith("glm-"):
                api_key = os.getenv("ZHIPU_API_KEY")
                if not api_key:
                    yield f"data: {json.dumps({'content': '❌ 未配置智谱API Key，请在.env中设置 ZHIPU_API_KEY', 'done': True, 'error': True})}\n\n"
                    return
                client = ZhipuAI(api_key=api_key)
                response = client.chat.completions.create(
                    model=model_name,  # 使用前端传过来的模型名
                    messages=messages_for_ai,
                    stream=True,
                    max_tokens=500
                )
                for chunk in response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_reply += content
                        yield f"data: {json.dumps({'content': content, 'done': False})}\n\n"

            # ----- 分支2：DeepSeek系列 (deepseek-chat, deepseek-reasoner) -----
            elif model_name.startswith("deepseek"):
                from openai import OpenAI
                api_key = os.getenv("DEEPSEEK_API_KEY")
                if not api_key:
                    yield f"data: {json.dumps({'content': '❌ 未配置DeepSeek API Key，请在.env中设置 DEEPSEEK_API_KEY', 'done': True, 'error': True})}\n\n"
                    return
                client = OpenAI(
                    api_key=api_key,
                    base_url="https://api.deepseek.com/v1"
                )
                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages_for_ai,
                    stream=True,
                    max_tokens=500
                )
                for chunk in response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_reply += content
                        yield f"data: {json.dumps({'content': content, 'done': False})}\n\n"

            # ----- 未知模型 -----
            else:
                yield f"data: {json.dumps({'content': '❌ 不支持的模型: ' + model_name + '，目前支持 glm-4-flash, glm-4-plus, deepseek-chat, deepseek-reasoner', 'done': True, 'error': True})}\n\n"
                return

            # 发送完成信号
            yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"

            # 保存完整回复到数据库
            if full_reply:
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
            error_msg = f"AI调用失败: {str(e)}"
            yield f"data: {json.dumps({'content': '❌ ' + error_msg, 'done': True, 'error': True})}\n\n"
            print(f"流式错误: {e}")

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# 6. 健康检查
@app.get("/ping")
def ping():
    return {"status": "ok", "info": "服务正常运行"}