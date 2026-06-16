from fastapi import APIRouter
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client

from open_agent.repository import setting_repository

router = APIRouter()


@router.post("/tool/list")
async def list_mcp_tool(body: dict):
    proto_type = body.get("type")
    # 创建客户端
    if proto_type == "streamable_http":
        client = streamablehttp_client(body["url"], body.get("headers"))
    elif proto_type == "sse":
        client = sse_client(body["url"], body.get("headers"))
    elif proto_type == "stdio":
        client = stdio_client(StdioServerParameters(command=body["command"], args=body["args"]))
    else:
        raise ValueError(f"Unknown proto type: {proto_type}")
    # 建立连接
    async with client as streams:
        read, write = streams[:2]
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_resp = await session.list_tools()
            return [dict(tool) for tool in tools_resp.tools]


@router.get("/list")
async def list_mcp():
    settings = await setting_repository.get_settings()
    mcp_servers = settings.get("mcp_servers", {})
    return [{
        "name": k,
        "type": v.get("type", ""),
        "url": v.get("url", ""),
        "headers": v.get("headers", {}),
        "command": v.get("command", ""),
        "args": v.get("args", [])
    } for k, v in mcp_servers.items()]


@router.post("/{name}")
async def update_mcp(name: str, body: dict):
    settings = await setting_repository.get_settings()
    if not "mcp_servers" in settings:
        settings["mcp_servers"] = {}
    settings["mcp_servers"][name] = body
    await setting_repository.save_settings(settings)


@router.delete("/{name}")
async def delete_mcp(name: str):
    settings = await setting_repository.get_settings()
    if "mcp_servers" in settings and name in settings["mcp_servers"]:
        del settings["mcp_servers"][name]
        await setting_repository.save_settings(settings)
