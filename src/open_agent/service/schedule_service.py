import logging
import pathlib

from apscheduler import AsyncScheduler
from apscheduler.datastores.sqlalchemy import SQLAlchemyDataStore
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import create_async_engine

from open_agent.service import agent_service

DATABASE_FILE = str(pathlib.Path.home() / ".openagent" / "scheduler.db")
DATABASE_URL = f"sqlite+aiosqlite:///{DATABASE_FILE}"
pathlib.Path(DATABASE_FILE).parent.mkdir(parents=True, exist_ok=True)
async_engine = create_async_engine(DATABASE_URL)
data_store = SQLAlchemyDataStore(async_engine)
async_scheduler = AsyncScheduler(data_store)


async def _execute_task(name: str, query: str, work_dir: str):
    logging.info(f"Schedule started: {name}")
    async for _ in agent_service.agent(0, query, work_dir):
        pass


async def list_schedule() -> list[dict]:
    return [{
        "id": schedule.id,
        "name": schedule.args[0] if schedule.args else "",
        "content": schedule.args[1] if len(schedule.args) > 1 else "",
        "work_dir": schedule.args[2] if len(schedule.args) > 2 else "",
        "trigger": str(schedule.trigger),
        "next_fire_time": schedule.next_fire_time.strftime("%Y-%m-%d %H:%M:%S") if schedule.next_fire_time else None
    } for schedule in await async_scheduler.get_schedules()]


async def add_schedule(name: str, content: str, work_dir: str, year: str, month: str, day: str, week: str, day_of_week: str, hour: str, minute: str, second: str):
    trigger = CronTrigger(
        year=year or "*",
        month=month or "*",
        day=day or "*",
        week=week or "*",
        day_of_week=day_of_week or "*",
        hour=hour or "*",
        minute=minute or "*",
        second=second or "*"
    )
    await async_scheduler.add_schedule(_execute_task, trigger=trigger, args=[name, content, work_dir])


async def pause_schedule(task_id: str):
    schedule = await async_scheduler.get_schedule(task_id)
    if schedule:
        await async_scheduler.pause_schedule(task_id)


async def unpause_schedule(task_id: str):
    schedule = await async_scheduler.get_schedule(task_id)
    if schedule:
        await async_scheduler.unpause_schedule(task_id)


async def remove_schedule(task_id: str):
    schedule = await async_scheduler.get_schedule(task_id)
    if schedule:
        await async_scheduler.remove_schedule(task_id)
