from fastapi import APIRouter

from openagent.tool import skill_tool

router = APIRouter()


@router.get("/list")
async def list_skill():
    return skill_tool.SKILLS
