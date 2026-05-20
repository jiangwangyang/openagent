import json
import pathlib

import anyio
from anthropic import AsyncAnthropic, AsyncStream
from anthropic.types.raw_message_stream_event import RawMessageStreamEvent

from open_agent.repository import conversation_repository
from open_agent.service import tool_service

SETTINGS_FILE = str(pathlib.Path.home() / ".openagent" / "settings.json")


async def agent(conversation_id: int, query: str, work_dir: str):
    system_prompt = ""
    for agents_file in [anyio.Path(work_dir) / "AGENTS.md", await anyio.Path.home() / ".openagent" / "AGENTS.md", await anyio.Path.home() / ".agents" / "AGENTS.md"]:
        if await agents_file.exists() and await agents_file.is_file():
            system_prompt = await agents_file.read_text(encoding="utf-8")
            break
    tools = tool_service.get_anthropic_tools()
    messages = []
    if conversation_id:
        conversation = await conversation_repository.get_conversation(conversation_id)
        messages += [msg for e in conversation.exchanges for msg in [{"id": e.id, "role": "user", "content": e.query}, {"id": e.id, "role": "assistant", "content": e.answer}]]
    messages += [{"role": "user", "content": query}]

    # 初始化客户端
    settings_file = anyio.Path(SETTINGS_FILE)
    settings_file_content = await settings_file.read_text(encoding="utf-8") if await settings_file.exists() else ""
    settings = json.loads(settings_file_content) if settings_file_content else {}
    model, model_provider = settings.get("model", ""), settings.get("model_provider", "")
    model_provider_dict = settings.get("model_providers", {}).get(model_provider, {})
    api, base_url, api_key = model_provider_dict.get("api", "anthropic"), model_provider_dict.get("base_url", ""), model_provider_dict.get("api_key", "")
    anthropic_client: AsyncAnthropic = AsyncAnthropic(base_url=base_url, api_key=api_key)

    while True:
        # 1. 发送 anthropic 请求
        response: AsyncStream[RawMessageStreamEvent] = await anthropic_client.messages.create(messages=messages, tools=tools, system=system_prompt, model=model, max_tokens=1 << 14, stream=True)
        model_block_list = []
        async for event in response:
            if event.type == "content_block_start":
                if event.content_block.type == "thinking":
                    model_block_list += [{"type": "thinking", "thinking": "", "signature": ""}]
                    yield f"data: {json.dumps({"type": "thinking", "text": ""}, ensure_ascii=False)}\n\n"
                elif event.content_block.type == "text":
                    model_block_list += [{"type": "text", "text": ""}]
                    yield f"data: {json.dumps({"type": "text", "text": ""}, ensure_ascii=False)}\n\n"
                elif event.content_block.type == "tool_use":
                    model_block_list += [{"type": "tool_use", "id": event.content_block.id, "name": event.content_block.name, "input": ""}]
                    yield f"data: {json.dumps({"type": "tool_use", "id": event.content_block.id, "name": event.content_block.name, "text": ""}, ensure_ascii=False)}\n\n"
            elif event.type == "content_block_delta":
                if event.delta.type == "thinking_delta":
                    model_block_list[-1]["thinking"] += event.delta.thinking
                    yield f"data: {json.dumps({"type": "delta", "text": event.delta.thinking}, ensure_ascii=False)}\n\n"
                elif event.delta.type == "signature_delta":
                    model_block_list[-1]["signature"] += event.delta.signature
                elif event.delta.type == "text_delta":
                    model_block_list[-1]["text"] += event.delta.text
                    yield f"data: {json.dumps({"type": "delta", "text": event.delta.text}, ensure_ascii=False)}\n\n"
                elif event.delta.type == "input_json_delta":
                    model_block_list[-1]["input"] += event.delta.partial_json
                    yield f"data: {json.dumps({"type": "delta", "text": event.delta.partial_json}, ensure_ascii=False)}\n\n"
        for block in [block for block in model_block_list if block["type"] == "tool_use"]:
            block["input"] = json.loads(block["input"]) if block["input"] else {}
        messages += [{"role": "assistant", "content": model_block_list}]

        # 2. 判断结束
        if not [block for block in model_block_list if block["type"] == "tool_use"]:
            answer = model_block_list[-1].get("text", "") or model_block_list[-1].get("thinking", "")
            await conversation_repository.save_conversation(conversation_id, query[:30], work_dir, query, answer, [msg for msg in messages if not "id" in msg])
            break

        # 3. 工具调用
        tool_result_list = []
        for tool_use in [block for block in model_block_list if block["type"] == "tool_use"]:
            tool_content, is_error = await tool_service.execute_tool(tool_use["name"], tool_use["input"], work_dir)
            tool_result_list += [{"type": "tool_result", "tool_use_id": tool_use["id"], "content": tool_content, "is_error": is_error}]
            yield f"data: {json.dumps({"type": "tool_result", "id": tool_use["id"], "text": tool_content, "is_error": is_error}, ensure_ascii=False)}\n\n"
        messages += [{"role": "user", "content": tool_result_list}]
