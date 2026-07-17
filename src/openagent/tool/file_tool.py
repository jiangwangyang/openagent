import shlex

import anyio


async def execute(command: str, work_dir: str) -> tuple[str, bool]:
    args: list[str] = shlex.split(command)
    # 1. file read <file_path>
    if len(args) == 3 and args[0] == "file" and args[1] == "read":
        file_path = args[2]
        path = await (anyio.Path(work_dir) / file_path).resolve()
        if not await path.exists():
            return f"File not found: {file_path}", True
        if not await path.is_file():
            return f"Path is not file: {file_path}", True
        content = await path.read_text(encoding="utf-8")
        return content, False
    # 2. file write <file_path> <content>
    elif len(args) == 4 and args[0] == "file" and args[1] == "write":
        file_path, content = args[2], args[3]
        path = await (anyio.Path(work_dir) / file_path).resolve()
        await path.parent.mkdir(parents=True, exist_ok=True)
        await path.write_text(content, encoding="utf-8")
        return "", False
    # 3. file edit <file_path> <old_str> <new_str>
    elif len(args) == 5 and args[0] == "file" and args[1] == "edit":
        file_path, old_str, new_str = args[2], args[3], args[4]
        # 读文件
        path = await (anyio.Path(work_dir) / file_path).resolve()
        if not await path.exists():
            return f"File not found: {file_path}", True
        if not await path.is_file():
            return f"Path is not file: {file_path}", True
        content = await path.read_text(encoding="utf-8")
        # 应用替换逻辑
        if old_str not in content:
            return f"Target string not found in file:\n{old_str}", True
        content = content.replace(old_str, new_str)
        # 写文件
        await path.write_text(content, encoding="utf-8")
        return "", False
    return "未知命令", True
