from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# 数据库文件路径（放在项目根目录）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "chat.db")

# 创建数据库引擎
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

# ============================================================
# 定义数据表
# ============================================================

class Session(Base):
    """会话表：每个对话一个记录"""
    __tablename__ = "sessions"

    id = Column(String(50), primary_key=True)          # 会话ID
    title = Column(String(200), default="新对话")       # 会话标题
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class Message(Base):
    """消息表：每条消息一个记录"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), index=True)         # 关联会话
    sender = Column(String(10))                         # user 或 ai
    text = Column(Text)                                 # 消息内容
    timestamp = Column(DateTime, default=datetime.now)

# ============================================================
# 初始化数据库（建表）
# ============================================================

def init_db():
    """创建所有表（如果不存在）"""
    Base.metadata.create_all(engine)
    print("✅ 数据库初始化完成:", DB_PATH)

# ============================================================
# 数据库操作函数（供 main.py 调用）
# ============================================================

def get_db():
    """获取数据库会话（用于依赖注入）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 如果直接运行此文件，执行初始化
if __name__ == "__main__":
    init_db()