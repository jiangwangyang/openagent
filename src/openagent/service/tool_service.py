import sys

from openagent.tool import command_tool
from openagent.tool import file_tool
from openagent.tool import mcp_tool
from openagent.tool import skill_tool

# 工具描述
DESCRIPTION = f"""
Execute a command on {sys.platform} system with {"powershell" if sys.platform.startswith("win") else "bash"}.
The following are built-in system commands:
file read <file_path>                                           # Read file content.
file write <file_path> <content>                                # Write content to a file. Creates the file if it doesn't exist, overwrites if it does.
file edit <file_path> <old_str> <new_str>                       # Edit a file by replace all exact matches of old_str with new_str.
skill list                                                      # 列出所有可用技能
mcp server list                                                 # 列出所有MCP服务
mcp server <server_name> tool list                              # 列出指定MCP服务的所有工具
mcp server <server_name> tool <tool_name> info                  # 查看指定MCP服务指定工具的参数格式信息
mcp server <server_name> tool <tool_name> call <tool_json_args> # 调用指定MCP服务指定工具
"""
COMMAND_TOOL = {
    "name": "powershell" if sys.platform.startswith("win") else "bash",
    "description": DESCRIPTION,
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "PowerShell Command" if sys.platform.startswith("win") else "Bash Command",
            }
        },
        "required": ["command"]
    }
}


# 获取工具描述列表
def get_anthropic_tools() -> list[dict]:
    return [COMMAND_TOOL]


# 执行选择的工具
async def execute_tool(name: str, tool_input: dict, work_dir: str) -> tuple[str, bool]:
    try:
        if name != "powershell" and name != "bash":
            return f"Unknown tool: {name}", True
        if not tool_input.get("command"):
            return "No command", True
        command: str = tool_input["command"]
        if command.startswith("file "):
            return await file_tool.execute(command, work_dir)
        if command.startswith("skill "):
            return await skill_tool.execute(command, work_dir)
        if command.startswith("mcp "):
            return await mcp_tool.execute(command, work_dir)
        return await command_tool.execute(command, work_dir)
    except Exception as e:
        return f"{e}", True
