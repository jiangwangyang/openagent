import anyio

WRITE_FILE_TOOL = {
    "name": "write_file",
    "description": "Write content to a file. Creates the file if it doesn't exist, overwrites if it does.",
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Absolute or relative path to the file to write"
            },
            "content": {
                "type": "string",
                "description": "Content to write to the file"
            }
        },
        "required": ["file_path", "content"]
    }
}
EDIT_FILE_TOOL = {
    "name": "edit_file",
    "description": "Edit a file by replacing specific blocks of text. Must match existing content exactly.",
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Absolute or relative path to the file to edit"
            },
            "old_str": {
                "type": "string",
                "description": "Exact text to replace"
            },
            "new_str": {
                "type": "string",
                "description": "New text to insert"
            }
        },
        "required": ["file_path", "old_str", "new_str"]
    }
}


def get_anthropic_tools() -> list[dict]:
    return [WRITE_FILE_TOOL, EDIT_FILE_TOOL]


async def write_file(tool_input: dict, work_dir: str) -> tuple[str, bool]:
    file_path, content = tool_input["file_path"], tool_input["content"]
    path = await (anyio.Path(work_dir) / file_path).resolve()
    await path.parent.mkdir(parents=True, exist_ok=True)
    await path.write_text(content, encoding="utf-8")
    return "", False


async def edit_file(tool_input: dict, work_dir: str) -> tuple[str, bool]:
    file_path, old_str, new_str = tool_input["file_path"], tool_input["old_str"], tool_input["new_str"]

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
