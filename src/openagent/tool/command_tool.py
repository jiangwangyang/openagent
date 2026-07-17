import asyncio
import subprocess
import sys


async def execute(command: str, work_dir: str) -> tuple[str, bool]:
    encoding = "gbk" if sys.platform.startswith("win") else "utf-8"
    program = "powershell" if sys.platform.startswith("win") else "bash"
    encoded_command = command.encode(encoding, errors="replace")
    process = await asyncio.create_subprocess_exec(program, "-c", encoded_command, cwd=work_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = await process.communicate()
    tool_content = f"{stdout.decode(encoding, errors="replace")}{stderr.decode(encoding, errors="replace")}"
    is_error = process.returncode != 0
    return tool_content, is_error
