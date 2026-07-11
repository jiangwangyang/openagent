import sys

from openagent.tool import command_tool
from openagent.tool import file_tool
from openagent.tool import mcp_tool
from openagent.tool import skill_tool

# 工具描述
DESCRIPTION = f"""
Execute commands on {sys.platform} system.{' PowerShell commands are recommended, such as ["powershell", "Get-Date"]' if sys.platform.startswith("win") else ""}
The following are built-in system commands:
["file", "read", <file_path>]                                                   # Read file content.
["file", "write", <file_path>, <content>]                                       # Write content to a file. Creates the file if it doesn't exist, overwrites if it does.
["file", "edit", <file_path>, <old_str>, <new_str>]                             # Edit a file by replace all exact matches of old_str with new_str.
["skill", "list"]                                                               # 列出所有可用技能
["mcp", "server", "list"]                                                       # 列出所有MCP服务
["mcp", "server", <server_name>, "tool", "list"]                                # 列出指定MCP服务的所有工具
["mcp", "server", <server_name>, "tool", <tool_name>, "info"]                   # 查看指定MCP服务指定工具的参数格式信息
["mcp", "server", <server_name>, "tool", <tool_name>, "call", <tool_json_args>] # 调用指定MCP服务指定工具
"""
COMMAND_TOOL = {
    "name": "command",
    "description": DESCRIPTION,
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
        "required": ["args"]
    }
}


# 获取工具描述列表
def get_anthropic_tools() -> list[dict]:
    return [COMMAND_TOOL]


# 执行选择的工具
async def execute_tool(name: str, tool_input: dict, work_dir: str) -> tuple[str, bool]:
    try:
        if name != "command":
            return f"Unknown tool: {name}", True
        if not tool_input.get("args"):
            return "No args", True
        args: list[str] = tool_input["args"]
        if args[0] == "file":
            return await file_tool.execute(args, work_dir)
        if args[0] == "skill":
            return await skill_tool.execute(args, work_dir)
        if args[0] == "mcp":
            return await mcp_tool.execute(args, work_dir)
        return await command_tool.execute(args, work_dir)
    except Exception as e:
        return f"{e}", True
