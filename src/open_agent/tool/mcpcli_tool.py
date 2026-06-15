import json
import logging
from contextlib import asynccontextmanager, AsyncExitStack

from mcp import ClientSession, StdioServerParameters, Tool
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client

from open_agent.repository import setting_repository

HELP_CONTENT = """
mcpcli server list                                                 # 列出所有MCP服务
mcpcli server <server_name> tool list                              # 列出指定MCP服务的所有工具
mcpcli server <server_name> tool <tool_name> info                  # 查看指定MCP服务指定工具的参数格式信息
mcpcli server <server_name> tool <tool_name> call [tool_json_args] # 调用指定MCP服务指定工具
"""
MCPCLI_TOOL = {
    "name": "mcpcli",
    "description": HELP_CONTENT,
    "input_schema": {
        "type": "object",
        "properties": {
            "args": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": f"Argument list."
            }
        },
        "required": []
    }
}
# {servername: (serverdescription, {toolname: (session, tool)})}
SERVER_TOOL_DICT: dict[str, tuple[str, dict[str, tuple[ClientSession, Tool]]]] = {}


def get_anthropic_tools() -> list[dict]:
    return [MCPCLI_TOOL] if SERVER_TOOL_DICT else []


@asynccontextmanager
async def _register_mcp_client(name: str, description: str, proto_type: str, **kwargs):
    async with AsyncExitStack() as stack:
        # 创建客户端
        if proto_type == "streamable_http":
            transport = await stack.enter_async_context(streamablehttp_client(kwargs["url"], kwargs.get("headers")))
        elif proto_type == "sse":
            transport = await stack.enter_async_context(sse_client(kwargs["url"], kwargs.get("headers")))
        elif proto_type == "stdio":
            transport = await stack.enter_async_context(stdio_client(StdioServerParameters(command=kwargs["command"], args=kwargs["args"])))
        else:
            raise ValueError(f"Unknown proto type: {proto_type}")
        read, write = transport[:2]
        session = await stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        # 获取工具列表
        tools_resp = await session.list_tools()
        SERVER_TOOL_DICT[name] = (description, {tool.name: (session, tool) for tool in tools_resp.tools})
        logging.info(f"MCP client {name} started, having {len(tools_resp.tools)} tools: {json.dumps(tools_resp.tools, ensure_ascii=False, default=lambda o: o.__dict__)}")
        # 等待
        yield
        # 结束
        SERVER_TOOL_DICT.pop(name)
        logging.info(f"MCP client {name} stopped")


@asynccontextmanager
async def lifespan():
    settings = await setting_repository.get_settings()
    mcp_servers = settings.get("mcp_servers", {})
    async with AsyncExitStack() as stack:
        for name, server in mcp_servers.items():
            try:
                if server.get("type") == "streamable_http":
                    await stack.enter_async_context(_register_mcp_client(name, server.get("description", ""), "streamable_http", url=server.get("url"), headers=server.get("headers")))
                elif server.get("type") == "sse":
                    await stack.enter_async_context(_register_mcp_client(name, server.get("description", ""), "sse", url=server.get("url"), headers=server.get("headers")))
                elif server.get("type") == "stdio":
                    await stack.enter_async_context(_register_mcp_client(name, server.get("description", ""), "stdio", command=server.get("command"), args=server.get("args")))
                else:
                    logging.warning(f"Unknown MCP server type: {server.get("type")}")
            except Exception as e:
                if hasattr(e, "exceptions"):
                    logging.error(f"Error registering {name}: {e.exceptions}")
                else:
                    logging.error(f"Error registering {name}: {e}")
        yield


async def execute_mcpcli(tool_input: dict, work_dir: str) -> tuple[str, bool]:
    args: list[str] = tool_input.get("args", [])
    args = ["mcpcli"] if not args else args
    if args[0] == "mcpcli":
        args = args[1:]

    # 0. help
    if "-h" in args or "--help" in args:
        return HELP_CONTENT, False

    # 1. mcpcli server list
    if len(args) == 2 and args[0] == "server" and args[1] == "list":
        result = [{"name": name, "description": description} for name, (description, _) in SERVER_TOOL_DICT.items()]
        return json.dumps(result, ensure_ascii=False), False
    # 2. mcpcli server <server_name> tool list
    elif len(args) == 4 and args[0] == "server" and args[2] == "tool" and args[3] == "list":
        server_name = args[1]
        if not server_name in SERVER_TOOL_DICT:
            return f"Unknown server {server_name}", True
        result = [{"name": tool.name, "description": tool.description} for (session, tool) in SERVER_TOOL_DICT[server_name][1].values()]
        return json.dumps(result, ensure_ascii=False), False
    # 3. mcpcli server <server_name> tool <tool_name> info
    elif len(args) == 5 and args[0] == "server" and args[2] == "tool" and args[4] == "info":
        server_name = args[1]
        tool_name = args[3]
        if not server_name in SERVER_TOOL_DICT:
            return f"Unknown server {server_name}", True
        if not tool_name in SERVER_TOOL_DICT[server_name][1]:
            return f"Unknown tool {tool_name}", True
        tool = SERVER_TOOL_DICT[server_name][1][tool_name][1]
        result = {"name": tool.name, "description": tool.description, "input_schema": tool.inputSchema}
        return json.dumps(result, ensure_ascii=False), False
    # 4. mcpcli server <server_name> tool <tool_name> call [tool_json_args]
    elif len(args) == 6 and args[0] == "server" and args[2] == "tool" and args[4] == "call":
        server_name = args[1]
        tool_name = args[3]
        json_string = args[5]
        if not server_name in SERVER_TOOL_DICT:
            return f"Unknown server {server_name}", True
        if not tool_name in SERVER_TOOL_DICT[server_name][1]:
            return f"Unknown tool {tool_name}", True
        session = SERVER_TOOL_DICT[server_name][1][tool_name][0]
        tool_result = await session.call_tool(tool_name, json.loads(json_string) if json_string else {})
        tool_content, is_error = str(tool_result.content), tool_result.isError
        return tool_content, is_error
    return "未知命令，输入'mcpcli -h'或'mcpcli --help'查看用法", True
