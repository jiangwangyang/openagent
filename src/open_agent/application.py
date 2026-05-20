import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.responses import RedirectResponse
from starlette.staticfiles import StaticFiles

from open_agent.api.agent_api import router as agent_router
from open_agent.api.conversation_api import router as conversation_router
from open_agent.api.path_api import router as path_router
from open_agent.api.schedule_api import router as schedule_router
from open_agent.repository import database
from open_agent.service import schedule_service
from open_agent.tool import mcpcli_tool, skill_tool

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 初始化技能
    await skill_tool.init_skills()
    # 数据库/调度器/mcp 生命周期管理
    async with database.lifespan():
        async with schedule_service.lifespan():
            async with mcpcli_tool.lifespan():
                yield


app: FastAPI = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"))
app.include_router(agent_router, prefix="/agent")
app.include_router(conversation_router, prefix="/conversation")
app.include_router(path_router, prefix="")
app.include_router(schedule_router, prefix="/schedule")


@app.get("/")
async def index():
    return RedirectResponse(url="/static/index.html")
