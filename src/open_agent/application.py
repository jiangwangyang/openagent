import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from open_agent.api.agent_api import router as agent_router
from open_agent.api.conversation_api import router as conversation_router
from open_agent.api.mcp_api import router as mcp_router
from open_agent.api.model_api import router as model_router
from open_agent.api.schedule_api import router as schedule_router
from open_agent.api.skill_api import router as skill_router
from open_agent.api.static_api import router as static_router
from open_agent.repository import database
from open_agent.repository import setting_repository
from open_agent.service import schedule_service
from open_agent.tool import mcpcli_tool, skill_tool

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 初始化设置
    await setting_repository.init_settings()
    # 初始化技能
    await skill_tool.init_skills()
    # 数据库/调度器/mcp 生命周期管理
    async with database.lifespan():
        async with schedule_service.lifespan():
            async with mcpcli_tool.lifespan():
                yield


app: FastAPI = FastAPI(lifespan=lifespan)
app.include_router(static_router, prefix="")
app.include_router(agent_router, prefix="/agent")
app.include_router(conversation_router, prefix="/conversation")
app.include_router(schedule_router, prefix="/schedule")
app.include_router(skill_router, prefix="/skill")
app.include_router(mcp_router, prefix="/mcp")
app.include_router(model_router, prefix="/model")
