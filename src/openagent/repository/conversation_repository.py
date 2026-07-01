import json
from datetime import datetime

from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from openagent.repository.database import ConversationEntity, MessageEntity, ExchangeEntity
from openagent.repository.database import async_session


async def get_conversations() -> list[ConversationEntity]:
    async with async_session() as session:
        stmt = (
            select(ConversationEntity)
            .order_by(ConversationEntity.update_time.desc())
        )
        result = await session.execute(stmt)
        conversations = result.scalars().all()
        return conversations


async def get_conversation(conversation_id: int) -> ConversationEntity | None:
    async with async_session() as session:
        stmt = (
            select(ConversationEntity)
            .where(ConversationEntity.id == conversation_id)
            .options(selectinload(ConversationEntity.exchanges))
            .options(selectinload(ConversationEntity.messages))
        )
        result = await session.execute(stmt)
        conversation = result.scalars().first()
        if not conversation:
            return None
        return conversation


async def save_conversation(conversation_id: int, title: str, work_dir: str, query: str, answer: str, messages: list):
    current_time = datetime.now()

    async with async_session() as session:
        # 1. 检查会话是否存在
        conversation = await session.get(ConversationEntity, conversation_id) if conversation_id else None
        if conversation:
            # 如果会话存在，更新时间
            conversation.update_time = current_time
        else:
            # 如果不存在，创建新会话
            conversation = ConversationEntity(
                title=title,
                work_dir=work_dir,
                create_time=current_time,
                update_time=current_time
            )
            session.add(conversation)
            await session.flush()

        # 2. 新增 exchange
        exchange = ExchangeEntity(
            conversation_id=conversation.id,
            query=query,
            answer=answer,
            time=current_time
        )
        session.add(exchange)
        await session.flush()

        # 3. 批量插入 messages
        db_messages = [
            MessageEntity(
                exchange_id=exchange.id,
                conversation_id=conversation.id,
                role=msg["role"],
                content=json.dumps(msg["content"], ensure_ascii=False),
                time=current_time
            )
            for msg in messages
        ]
        session.add_all(db_messages)

        # 提交事务
        await session.commit()


async def delete_conversation(conversation_id: int):
    async with async_session() as session:
        stmt = delete(ConversationEntity).where(ConversationEntity.id == conversation_id)
        await session.execute(stmt)
        await session.commit()
