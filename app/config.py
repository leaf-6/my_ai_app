import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

class Config:
    """所有配置集中管理"""
    # 密钥
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

    # API Keys
    ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

    # 数据库
    DATABASE_URL = f"sqlite:///{os.path.join(os.path.dirname(os.path.dirname(__file__)), 'chat.db')}"

    # 服务器
    HOST = "127.0.0.1"
    PORT = 8000