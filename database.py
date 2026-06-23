from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship  # 这里加上了 relationship
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

class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(String(50), primary_key=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    # 一个用户有多个会话
    sessions = relationship("Session", back_populates="user")


class Session(Base):
    """会话表"""
    __tablename__ = "sessions"

    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id"), index=True)
    title = Column(String(200), default="新对话")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联用户
    user = relationship("User", back_populates="sessions")
    # 一个会话有多条消息
    messages = relationship("Message", back_populates="session")


class Message(Base):
    """消息表"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), ForeignKey("sessions.id"), index=True)
    user_id = Column(String(50), ForeignKey("users.id"), index=True)
    sender = Column(String(10))  # user 或 ai
    text = Column(Text)
    timestamp = Column(DateTime, default=datetime.now)

    # 关联会话
    session = relationship("Session", back_populates="messages")


# ============================================================
# 初始化数据库（建表）
# ============================================================

def init_db():
    """创建所有表（如果不存在）"""
    Base.metadata.create_all(engine)
    print("✅ 数据库初始化完成:", DB_PATH)


# 如果直接运行此文件，执行初始化
if __name__ == "__main__":
    init_db()