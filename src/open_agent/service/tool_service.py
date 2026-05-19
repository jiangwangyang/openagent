from open_agent.tool import shell_tool


def get_anthropic_tools() -> list[dict]:
    return shell_tool.get_anthropic_tools()


async def execute_tool(name: str, tool_input: dict, work_dir: str) -> tuple[str, bool]:
    if name == "bash":
        return await shell_tool.execute_bash(tool_input, work_dir)
    if name == "powershell":
        return await shell_tool.execute_powershell(tool_input, work_dir)
    return f"Unknown tool: {name}", True
