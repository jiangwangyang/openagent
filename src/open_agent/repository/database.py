import pathlib
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List

from sqlalchemy import Index, ForeignKey, event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm import declarative_base

DATABASE_FILE = str(pathlib.Path.home() / ".openagent" / "database.db")
DATABASE_URL = f"sqlite+aiosqlite:///{DATABASE_FILE}"
pathlib.Path(DATABASE_FILE).parent.mkdir(parents=True, exist_ok=True)
async_engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(async_engine, expire_on_commit=False)
Base = declarative_base()


@asynccontextmanager
async def lifespan():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, checkfirst=True)
    yield
    await async_engine.dispose()


# 开启 SQLite 的外键约束支持
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    # 确保数据库层面的 ON DELETE CASCADE 能够正常工作
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# 整个对话
class ConversationEntity(Base):
    __tablename__ = "t_conversation"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(nullable=False)
    work_dir: Mapped[str] = mapped_column(nullable=False)
    create_time: Mapped[datetime] = mapped_column(nullable=False)
    update_time: Mapped[datetime] = mapped_column(nullable=False)

    exchanges: Mapped[List["ExchangeEntity"]] = relationship("ExchangeEntity", back_populates="conversation", cascade="all, delete-orphan")
    messages: Mapped[List["MessageEntity"]] = relationship("MessageEntity", back_populates="conversation", cascade="all, delete-orphan")


# 整个对话中 每一次交互
class ExchangeEntity(Base):
    __tablename__ = "t_exchange"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("t_conversation.id", ondelete="CASCADE"), nullable=False)
    query: Mapped[str] = mapped_column(nullable=False)
    answer: Mapped[str] = mapped_column(nullable=False)
    time: Mapped[datetime] = mapped_column(nullable=False)

    messages: Mapped[List["MessageEntity"]] = relationship("MessageEntity", back_populates="exchange", cascade="all, delete-orphan")
    conversation: Mapped["ConversationEntity"] = relationship("ConversationEntity", back_populates="exchanges")


# 整个对话中 每一次交互中 每一次模型调用细节
class MessageEntity(Base):
    __tablename__ = "t_message"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    exchange_id: Mapped[int] = mapped_column(ForeignKey("t_exchange.id", ondelete="CASCADE"), nullable=False)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("t_conversation.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(nullable=False)
    content: Mapped[str] = mapped_column(nullable=False)
    time: Mapped[datetime] = mapped_column(nullable=False)

    exchange: Mapped["ExchangeEntity"] = relationship("ExchangeEntity", back_populates="messages")
    conversation: Mapped["ConversationEntity"] = relationship("ConversationEntity", back_populates="messages")


# 定义索引
Index("idx_exchange_conversation", ExchangeEntity.conversation_id)
Index("idx_message_conversation", MessageEntity.conversation_id)
