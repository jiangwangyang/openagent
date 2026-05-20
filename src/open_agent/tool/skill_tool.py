import json
import pathlib

import anyio

LIST_SKILL_TOOL = {
    "name": "list_skill",
    "description": "List Skill",
    "input_schema": {
        "type": "object",
        "properties": {},
        "required": []
    }
}
SKILLS_DIR_LIST = [str(pathlib.Path.home() / ".openagent" / "skills"), str(pathlib.Path.home() / ".agents" / "skills")]
SKILLS = []


async def init_skills():
    loaded = set()
    # 遍历技能目录
    for skills_dir in map(anyio.Path, SKILLS_DIR_LIST):
        if not await skills_dir.exists():
            continue
        # 遍历技能
        async for skill_dir in skills_dir.iterdir():
            if skill_dir.name in loaded:
                continue
            skill_file = skill_dir / "SKILL.md"
            if not await skill_file.is_file():
                continue
            # 尝试读取 SKILL.md 提取 name 和 description
            text = await skill_file.read_text(encoding="utf-8")
            lines = [line.strip() for line in text.split("\n")]
            if len(lines) > 0 and lines[0] == "---" and "---" in lines[1:]:
                second_index = lines.index("---", 1)
            else:
                continue
            name, description = "", ""
            for line in lines[1:second_index]:
                if line.startswith("name:"):
                    name = line[5:].strip()
                elif line.startswith("description:"):
                    description = line[12:].strip()
            if name == skill_dir.name:
                content = text.split("---\n", 2)[2].strip()
                SKILLS.append({"name": name, "description": description, "path": str(await skill_file.resolve()), "content": content})
                loaded.add(name)


def get_anthropic_tools() -> list[dict]:
    return [LIST_SKILL_TOOL] if SKILLS else []


async def list_skill(tool_input: dict, work_dir: str) -> tuple[str, bool]:
    tool_content = json.dumps([{"name": s["name"], "description": s["description"], "path": s["path"]} for s in SKILLS], ensure_ascii=False)
    return tool_content, False
