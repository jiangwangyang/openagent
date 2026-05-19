import asyncio
import subprocess
import sys

BASH_TOOL = {
    "name": "bash",
    "description": "Execute a shell command on the linux system using /bin/bash",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The shell command to execute"
            }
        },
        "required": ["command"]
    }
}
POWERSHELL_TOOL = {
    "name": "powershell",
    "description": "Execute a PowerShell command on the Windows system using powershell. Specify the character encoding when reading and writing files.",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The powershell command to execute"
            }
        },
        "required": ["command"]
    }
}


def get_anthropic_tools() -> list[dict]:
    return [POWERSHELL_TOOL if sys.platform.startswith("win") else BASH_TOOL]


async def execute_bash(tool_input: dict, work_dir) -> tuple[str, bool]:
    command = tool_input.get("command", "")
    if not command:
        return "No command provided", True
    try:
        process = await asyncio.create_subprocess_exec("/bin/bash", cwd=work_dir, stdin=asyncio.subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.stdin.write(command.encode(encoding="utf-8"))
        await process.stdin.drain()
        process.stdin.close()
        await process.stdin.wait_closed()
        stdout, stderr = await process.communicate()
        tool_content = f"{stdout.decode("utf-8", errors="replace")}{stderr.decode("utf-8", errors="replace")}"
        is_error = process.returncode != 0
        return tool_content, is_error
    except Exception as e:
        return f"Error executing command: {e}", True


async def execute_powershell(tool_input: dict, work_dir) -> tuple[str, bool]:
    command = tool_input.get("command", "")
    if not command:
        return "No command provided", True
    try:
        process = await asyncio.create_subprocess_exec("powershell", cwd=work_dir, stdin=asyncio.subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.stdin.write(command.encode(encoding="gbk"))
        await process.stdin.drain()
        process.stdin.close()
        await process.stdin.wait_closed()
        stdout, stderr = await process.communicate()
        tool_content = f"{stdout.decode("gbk", errors="replace")}{stderr.decode("gbk", errors="replace")}"
        is_error = process.returncode != 0
        return tool_content, is_error
    except Exception as e:
        return f"Error executing command: {e}", True
