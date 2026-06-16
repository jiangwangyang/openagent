import logging
import pathlib
import sys
import threading
from contextlib import asynccontextmanager
from importlib.resources import files

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from open_agent.api.agent_api import router as agent_router
from open_agent.api.app_api import router as app_router
from open_agent.api.conversation_api import router as conversation_router
from open_agent.api.mcp_api import router as mcp_router
from open_agent.api.model_api import router as model_router
from open_agent.api.schedule_api import router as schedule_router
from open_agent.api.skill_api import router as skill_router
from open_agent.repository import database
from open_agent.repository import setting_repository
from open_agent.service import schedule_service
from open_agent.tool import mcp_tool, skill_tool

STATIC_PATH = files("open_agent") / "static"
LOGGING_FILE = str(pathlib.Path.home() / ".openagent" / "app.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOGGING_FILE, mode="a", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
startup_event = threading.Event()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 初始化设置
    await setting_repository.init_settings()
    # 初始化技能
    await skill_tool.init_skills()
    # 数据库/调度器/mcp 生命周期管理
    async with database.lifespan():
        async with schedule_service.lifespan():
            async with mcp_tool.lifespan():
                # 启动完成
                startup_event.set()
                logging.info("Application started")
                yield


app: FastAPI = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(STATIC_PATH)), name="static")
app.include_router(app_router, prefix="")
app.include_router(agent_router, prefix="/agent")
app.include_router(conversation_router, prefix="/conversation")
app.include_router(schedule_router, prefix="/schedule")
app.include_router(skill_router, prefix="/skill")
app.include_router(mcp_router, prefix="/mcp")
app.include_router(model_router, prefix="/model")
