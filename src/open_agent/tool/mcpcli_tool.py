import argparse
import io
import json
import logging
from contextlib import asynccontextmanager, AsyncExitStack
from contextlib import redirect_stdout, redirect_stderr

from mcp import ClientSession, StdioServerParameters, Tool
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client

from open_agent.repository import setting_repository

EXAMPLE = """
# 列出服务
mcpcli server list
# 列出指定服务的工具
mcpcli tool list <server_name>
# 查看指定服务指定工具的参数格式信息
mcpcli tool info <server_name> <tool_name>
# 调用指定服务指定工具
mcpcli tool call <server_name> <tool_name> [tool_json_args]
"""
MCPCLI_TOOL = {
    "name": "mcpcli",
    "description": "Query and call MCP (Model Context Protocol) tool",
    "input_schema": {
        "type": "object",
        "properties": {
            "args": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": f"Argument list. Examples: \n{EXAMPLE}"
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


# 构建并返回 argparse 解析器
def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mcpcli",
        description="MCP (Model Context Protocol) 核心调用逻辑"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- server 命令 ---
    # mcpcli server list
    server_parser = subparsers.add_parser("server")
    server_subparsers = server_parser.add_subparsers(dest="server_command", required=True)
    server_list_parser = server_subparsers.add_parser("list")

    # --- tool 命令 ---
    tool_parser = subparsers.add_parser("tool")
    tool_subparsers = tool_parser.add_subparsers(dest="tool_command", required=True)

    # mcpcli tool list <server_name>
    tool_list_parser = tool_subparsers.add_parser("list")
    tool_list_parser.add_argument("server_name")

    # mcpcli tool info <server_name> <tool_name>
    tool_info_parser = tool_subparsers.add_parser("info")
    tool_info_parser.add_argument("server_name")
    tool_info_parser.add_argument("tool_name")

    # mcpcli tool call <server_name> <tool_name> [tool_json_args]
    tool_call_parser = tool_subparsers.add_parser("call")
    tool_call_parser.add_argument("server_name")
    tool_call_parser.add_argument("tool_name")
    tool_call_parser.add_argument("json_string", nargs="?", default=None)

    return parser


async def execute_mcpcli(tool_input: dict, work_dir: str) -> tuple[str, bool]:
    args: list[str] = tool_input.get("args", [])
    args = ["-h"] if not args else args
    parser = _build_parser()

    # 使用内存字符串缓冲区来拦截标准输出和标准错误
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    try:
        with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
            parsed_args = parser.parse_args(args)
    except SystemExit as e:
        # argparse 调用了 sys.exit()
        # e.code 为 0 通常代表正常退出（如 -h --help），非 0 代表解析错误
        if e.code == 0:
            return stdout_buf.getvalue(), False
        return stderr_buf.getvalue(), True

    if parsed_args.command == "server":
        if parsed_args.server_command == "list":
            result = [{"name": name, "description": description} for name, (description, _) in SERVER_TOOL_DICT.items()]
            return json.dumps(result, ensure_ascii=False), False

    elif parsed_args.command == "tool":
        if parsed_args.tool_command == "list":
            if not parsed_args.server_name in SERVER_TOOL_DICT:
                return f"Unknown server {parsed_args.server_name}", True
            result = [{"name": tool.name, "description": tool.description} for (session, tool) in SERVER_TOOL_DICT[parsed_args.server_name][1].values()]
            return json.dumps(result, ensure_ascii=False), False

        elif parsed_args.tool_command == "info":
            if not parsed_args.server_name in SERVER_TOOL_DICT:
                return f"Unknown server {parsed_args.server_name}", True
            if not parsed_args.tool_name in SERVER_TOOL_DICT[parsed_args.server_name][1]:
                return f"Unknown tool {parsed_args.tool_name}", True
            tool = SERVER_TOOL_DICT[parsed_args.server_name][1][parsed_args.tool_name][1]
            result = {"name": tool.name, "description": tool.description, "input_schema": tool.inputSchema}
            return json.dumps(result, ensure_ascii=False), False

        elif parsed_args.tool_command == "call":
            if not parsed_args.server_name in SERVER_TOOL_DICT:
                return f"Unknown server {parsed_args.server_name}", True
            if not parsed_args.tool_name in SERVER_TOOL_DICT[parsed_args.server_name][1]:
                return f"Unknown tool {parsed_args.tool_name}", True
            session = SERVER_TOOL_DICT[parsed_args.server_name][1][parsed_args.tool_name][0]
            tool_result = await session.call_tool(parsed_args.tool_name, json.loads(parsed_args.json_string) if parsed_args.json_string else {})
            tool_content, is_error = str(tool_result.content), tool_result.isError
            return tool_content, is_error

    return "", True
