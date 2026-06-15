from open_agent.tool import shell_tool, mcp_tool, file_tool, skill_tool


def get_anthropic_tools() -> list[dict]:
    return file_tool.get_anthropic_tools() + shell_tool.get_anthropic_tools() + skill_tool.get_anthropic_tools() + mcp_tool.get_anthropic_tools()


async def execute_tool(name: str, tool_input: dict, work_dir: str) -> tuple[str, bool]:
    try:
        if name == "write_file":
            return await file_tool.write_file(tool_input, work_dir)
        if name == "edit_file":
            return await file_tool.edit_file(tool_input, work_dir)
        if name == "bash":
            return await shell_tool.execute_bash(tool_input, work_dir)
        if name == "powershell":
            return await shell_tool.execute_powershell(tool_input, work_dir)
        if name == "list_skill":
            return await skill_tool.list_skill(tool_input, work_dir)
        if name == "mcpcli":
            return await mcp_tool.execute_mcpcli(tool_input, work_dir)
    except Exception as e:
        return f"{e}", True
    return f"Unknown tool: {name}", True
