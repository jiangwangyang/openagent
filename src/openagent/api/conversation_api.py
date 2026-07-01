import json

from fastapi import APIRouter, Path, HTTPException

from openagent.repository import conversation_repository
from openagent.repository.database import ConversationEntity

router = APIRouter()


# 获取所有会话列表
@router.get("/list")
async def list_conversation():
    conversations: list[ConversationEntity] = await conversation_repository.get_conversations()
    return [{
        "id": c.id,
        "title": c.title,
        "work_dir": c.work_dir,
        "create_time": c.create_time.strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": c.update_time.strftime("%Y-%m-%d %H:%M:%S"),
    } for c in conversations]


# 获取单个会话详情
@router.get("/{conversation_id}")
async def get_conversation(conversation_id: int = Path(...)):
    conversation: ConversationEntity | None = await conversation_repository.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(404, "NOT FOUND")
    return {
        "id": conversation.id,
        "title": conversation.title,
        "work_dir": conversation.work_dir,
        "create_time": conversation.create_time.strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": conversation.update_time.strftime("%Y-%m-%d %H:%M:%S"),
        "exchanges": [{
            "id": e.id,
            "query": e.query,
            "answer": e.answer,
            "time": e.time.strftime("%Y-%m-%d %H:%M:%S")
        } for e in conversation.exchanges],
        "messages": [{
            "id": msg.id,
            "role": msg.role,
            "content": json.loads(msg.content),
            "time": msg.time.strftime("%Y-%m-%d %H:%M:%S")
        } for msg in conversation.messages]
    }


# 删除会话
@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: int = Path(...)):
    await conversation_repository.delete_conversation(conversation_id)
