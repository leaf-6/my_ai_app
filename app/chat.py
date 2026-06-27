from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from zhipuai import ZhipuAI
from openai import OpenAI
import json
from app.config import Config
from app.database import get_db
from app.models import Session as DBSession, Message
from app.auth import get_current_user_id
# from app.rag import get_rag_context

router = APIRouter(tags=["chat"])

class ChatRequest(BaseModel):
    message: str
    user_id: str = "anonymous"
    model: str = "glm-4-flash"

@router.post("/chat")
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    session_id = request.user_id if request.user_id != "anonymous" else user_id

    session = db.query(DBSession).filter(DBSession.id == session_id, DBSession.user_id == user_id).first()
    if not session:
        session = DBSession(id=session_id, user_id=user_id, title="新对话")
        db.add(session)
        db.commit()

    # 保存用户消息
    user_msg = Message(session_id=session_id, user_id=user_id, sender="user", text=request.message)
    db.add(user_msg)
    db.commit()

    # 获取历史消息
    history = db.query(Message).filter(Message.session_id == session_id).order_by(Message.timestamp.desc()).limit(10).all()
    history.reverse()

    messages_for_ai = [
        {"role": "system", "content": "你是一个友好的AI助手，用中文回复。"}
    ]
    for msg in history:
        role = "user" if msg.sender == "user" else "assistant"
        messages_for_ai.append({"role": role, "content": msg.text})

    # ===== RAG 上下文 =====
    # rag_context = get_rag_context(request.message, user_id)
    # if rag_context:
    #     messages_for_ai[0]["content"] += rag_context


    def generate():
        full_reply = ""
        try:
            model_name = request.model
            
            if model_name.startswith("glm-"):
                api_key = Config.ZHIPU_API_KEY
                if not api_key:
                    yield f"data: {json.dumps({'content': '❌ 未配置智谱API Key', 'done': True, 'error': True})}\n\n"
                    return
                client = ZhipuAI(api_key=api_key)
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

            elif model_name.startswith("deepseek"):
                api_key = Config.DEEPSEEK_API_KEY
                if not api_key:
                    yield f"data: {json.dumps({'content': '❌ 未配置DeepSeek API Key', 'done': True, 'error': True})}\n\n"
                    return
                client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")
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

            else:
                yield f"data: {json.dumps({'content': '❌ 不支持的模型: ' + model_name, 'done': True, 'error': True})}\n\n"
                return

            yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"

            if full_reply:
                ai_msg = Message(session_id=session_id, user_id=user_id, sender="ai", text=full_reply)
                db.add(ai_msg)
                db.commit()
                if session.title == "新对话":
                    first_user = db.query(Message).filter(
                        Message.session_id == session_id, Message.sender == "user"
                    ).order_by(Message.timestamp).first()
                    if first_user:
                        session.title = first_user.text[:20] + ("..." if len(first_user.text) > 20 else "")
                        db.commit()

        except Exception as e:
            yield f"data: {json.dumps({'content': '❌ AI调用失败: ' + str(e), 'done': True, 'error': True})}\n\n"
            print(f"流式错误: {e}")

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"}
    )