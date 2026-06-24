import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # 密钥
    SECRET_KEY = os.getenv("SECRET_KEY", "ai_chat_app_2024_secure_key_7f8d9e0a1b2c3d4e5f")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

    # API Keys
    ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

    # 数据库
    DATABASE_URL = f"sqlite:///{os.path.join(os.path.dirname(os.path.dirname(__file__)), 'chat.db')}"

    # 向量数据库（RAG用）
    VECTOR_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vector_db")

    # 服务器
    HOST = "127.0.0.1"
    PORT = 8000