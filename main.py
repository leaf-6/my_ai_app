from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response
import os

from app.database import init_db
from app.auth import router as auth_router
from app.sessions import router as sessions_router
from app.chat import router as chat_router
from app.upload import router as upload_router 

# 初始化数据库
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

# 注册路由
app.include_router(auth_router)
app.include_router(sessions_router)
app.include_router(chat_router)
app.include_router(upload_router)  

# 静态文件（禁用缓存）
class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope) -> Response:
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

app.mount("/static", NoCacheStaticFiles(directory="static"), name="static")

# 根页面
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

# 健康检查
@app.get("/ping")
def ping():
    return {"status": "ok", "info": "服务正常运行"}