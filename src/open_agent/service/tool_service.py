import sys

from open_agent.tool import command_tool
from open_agent.tool import file_tool
from open_agent.tool import mcp_tool
from open_agent.tool import skill_tool

DESCRIPTION = f"""
Execute commands on the {sys.platform} system.
The following are built-in system commands, and note that the commands should be entered as an array:
file read <file_path>                                           # Read file content.
file write <file_path> <content>                                # Write content to a file. Creates the file if it doesn't exist, overwrites if it does.
file edit <file_path> <old_str> <new_str>                       # Edit a file by replacing specific blocks of text. Must match existing content exactly.
skill list                                                      # 列出所有可用技能
mcp server list                                                 # 列出所有MCP服务
mcp server <server_name> tool list                              # 列出指定MCP服务的所有工具
mcp server <server_name> tool <tool_name> info                  # 查看指定MCP服务指定工具的参数格式信息
mcp server <server_name> tool <tool_name> call [tool_json_args] # 调用指定MCP服务指定工具
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


def get_anthropic_tools() -> list[dict]:
    return [COMMAND_TOOL]


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
