import json
import logging
from contextlib import asynccontextmanager, AsyncExitStack

from mcp import ClientSession, StdioServerParameters, Tool
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client

from open_agent.repository import setting_repository

# {servername: (serverdescription, {toolname: (session, tool)})}
SERVER_TOOL_DICT: dict[str, tuple[str, dict[str, tuple[ClientSession, Tool]]]] = {}


@asynccontextmanager
async def _register_mcp_client(name: str, description: str, proto_type: str, arg_dict: dict):
    # 创建客户端
    if proto_type == "streamable_http":
        client = streamablehttp_client(arg_dict["url"], arg_dict.get("headers"))
    elif proto_type == "sse":
        client = sse_client(arg_dict["url"], arg_dict.get("headers"))
    elif proto_type == "stdio":
        client = stdio_client(StdioServerParameters(command=arg_dict["command"], args=arg_dict["args"]))
    else:
        raise ValueError(f"Unknown proto type: {proto_type}")
    # 建立连接
    async with client as streams:
        read, write = streams[:2]
        async with ClientSession(read, write) as session:
            await session.initialize()
            # 获取工具列表
            tools_resp = await session.list_tools()
            SERVER_TOOL_DICT[name] = (description, {tool.name: (session, tool) for tool in tools_resp.tools})
            logging.info(f"MCP client {name} started, having {len(tools_resp.tools)} tools: {json.dumps([{"name": tool.name, "description": tool.description} for tool in tools_resp.tools], ensure_ascii=False)}")
            # 等待
            yield
            # 结束
            SERVER_TOOL_DICT.pop(name)
            logging.info(f"MCP client {name} stopped")


@asynccontextmanager
async def lifespan():
    settings = await setting_repository.get_settings()
    mcp_servers = settings.get("mcp_servers", {})
    mcp_clients = [_register_mcp_client(name, server_dict.get("description", ""), server_dict.get("type", ""), server_dict) for name, server_dict in mcp_servers.items()]
    async with AsyncExitStack() as stack:
        for client in mcp_clients:
            try:
                await stack.enter_async_context(client)
            except Exception as e:
                if hasattr(e, "exceptions"):
                    logging.error(f"Error registering mcp client: {e.exceptions}")
                else:
                    logging.error(f"Error registering mcp client: {e}")
        yield


async def execute(args: list[str], work_dir: str) -> tuple[str, bool]:
    # 1. mcp server list
    if len(args) == 3 and args[0] == "mcp" and args[1] == "server" and args[2] == "list":
        result = [{"name": name, "description": description} for name, (description, _) in SERVER_TOOL_DICT.items()]
        return json.dumps(result, ensure_ascii=False), False
    # 2. mcp server <server_name> tool list
    elif len(args) == 5 and args[0] == "mcp" and args[1] == "server" and args[3] == "tool" and args[4] == "list":
        server_name = args[2]
        if not server_name in SERVER_TOOL_DICT:
            return f"Unknown server {server_name}", True
        result = [{"name": tool.name, "description": tool.description} for (session, tool) in SERVER_TOOL_DICT[server_name][1].values()]
        return json.dumps(result, ensure_ascii=False), False
    # 3. mcp server <server_name> tool <tool_name> info
    elif len(args) == 6 and args[0] == "mcp" and args[1] == "server" and args[3] == "tool" and args[5] == "info":
        server_name, tool_name = args[2], args[4]
        if not server_name in SERVER_TOOL_DICT:
            return f"Unknown server {server_name}", True
        if not tool_name in SERVER_TOOL_DICT[server_name][1]:
            return f"Unknown tool {tool_name}", True
        tool = SERVER_TOOL_DICT[server_name][1][tool_name][1]
        result = {"name": tool.name, "description": tool.description, "input_schema": tool.inputSchema}
        return json.dumps(result, ensure_ascii=False), False
    # 4. mcp server <server_name> tool <tool_name> call [tool_json_args]
    elif len(args) == 7 and args[0] == "mcp" and args[1] == "server" and args[3] == "tool" and args[5] == "call":
        server_name, tool_name, json_string = args[2], args[4], args[6]
        if not server_name in SERVER_TOOL_DICT:
            return f"Unknown server {server_name}", True
        if not tool_name in SERVER_TOOL_DICT[server_name][1]:
            return f"Unknown tool {tool_name}", True
        session = SERVER_TOOL_DICT[server_name][1][tool_name][0]
        tool_result = await session.call_tool(tool_name, json.loads(json_string) if json_string else {})
        tool_content, is_error = str(tool_result.content), tool_result.isError
        return tool_content, is_error
    return "未知命令", True
