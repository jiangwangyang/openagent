from contextlib import AsyncExitStack

from fastapi import APIRouter
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client

from open_agent.service import setting_service

router = APIRouter()


@router.post("/mcp/tool/list")
async def list_mcp_tool(body: dict):
    proto_type = body.get("type")
    async with AsyncExitStack() as stack:
        if proto_type == "streamable_http":
            transport = await stack.enter_async_context(streamablehttp_client(body["url"], body.get("headers")))
        elif proto_type == "sse":
            transport = await stack.enter_async_context(sse_client(body["url"], body.get("headers")))
        elif proto_type == "stdio":
            transport = await stack.enter_async_context(stdio_client(StdioServerParameters(command=body["command"], args=body["args"])))
        else:
            raise ValueError(f"Unknown proto type: {proto_type}")
        read, write = transport[:2]
        session = await stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        tools_resp = await session.list_tools()
        return [dict(tool) for tool in tools_resp.tools]


@router.get("/mcp/list")
async def list_mcp():
    settings = await setting_service.get_settings()
    mcp_servers = settings.get("mcp_servers", {})
    return [{
        "name": k,
        "type": v.get("type", ""),
        "url": v.get("url", ""),
        "headers": v.get("headers", {}),
        "command": v.get("command", ""),
        "args": v.get("args", [])
    } for k, v in mcp_servers.items()]


@router.post("/mcp/{name}")
async def update_mcp(name: str, body: dict):
    settings = await setting_service.get_settings()
    if not "mcp_servers" in settings:
        settings["mcp_servers"] = {}
    settings["mcp_servers"][name] = body
    await setting_service.save_settings(settings)


@router.delete("/mcp/{name}")
async def delete_mcp(name: str):
    settings = await setting_service.get_settings()
    if "mcp_servers" in settings and name in settings["mcp_servers"]:
        del settings["mcp_servers"][name]
        await setting_service.save_settings(settings)


@router.get("/model/provider/list")
async def list_model_provider():
    settings = await setting_service.get_settings()
    model_providers = settings.get("model_providers", {})
    return [{
        "name": k,
        "base_url": v.get("base_url", ""),
        "api_key": v.get("api_key", ""),
        "models": v.get("models", [])
    } for k, v in model_providers.items()]


@router.post("/model/provider/{name}")
async def update_model_provider(name: str, body: dict):
    settings = await setting_service.get_settings()
    if not "model_providers" in settings:
        settings["model_providers"] = {}
    settings["model_providers"][name] = body
    await setting_service.save_settings(settings)


@router.delete("/model/provider/{name}")
async def delete_model_provider(name: str):
    settings = await setting_service.get_settings()
    if "model_providers" in settings and name in settings["model_providers"]:
        del settings["model_providers"][name]
        await setting_service.save_settings(settings)


@router.get("/model/select")
async def get_model_select():
    settings = await setting_service.get_settings()
    return {
        "model_provider": settings.get("model_provider", ""),
        "model": settings.get("model", "")
    }


@router.post("/model/select")
async def update_model_select(body: dict):
    settings = await setting_service.get_settings()
    settings["model_provider"] = body["model_provider"]
    settings["model"] = body["model"]
    await setting_service.save_settings(settings)
