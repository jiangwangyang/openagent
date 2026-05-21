from fastapi import APIRouter

from open_agent.tool import skill_tool

router = APIRouter()


@router.get("/list")
async def list_skill():
    return skill_tool.SKILLS
