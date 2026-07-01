from fastapi import APIRouter, Path, Body

from openagent.service import schedule_service

router = APIRouter()


@router.get("/list")
async def list_schedule():
    return await schedule_service.list_schedule()


@router.post("")
async def add_schedule(
        name: str = Body(..., embed=True),
        content: str = Body(..., embed=True),
        work_dir: str = Body(..., embed=True),
        year: str = Body("*", embed=True),
        month: str = Body("*", embed=True),
        day: str = Body("*", embed=True),
        week: str = Body("*", embed=True),
        day_of_week: str = Body("*", embed=True),
        hour: str = Body("*", embed=True),
        minute: str = Body("*", embed=True),
        second: str = Body("*", embed=True)
):
    await schedule_service.add_schedule(name, content, work_dir, year, month, day, week, day_of_week, hour, minute, second)


@router.post("/{schedule_id}/pause")
async def add_schedule(schedule_id: str = Path(...)):
    await schedule_service.pause_schedule(schedule_id)


@router.post("/{schedule_id}/unpause")
async def add_schedule(schedule_id: str = Path(...)):
    await schedule_service.unpause_schedule(schedule_id)


@router.delete("/{schedule_id}")
async def delete_schedule(schedule_id: str = Path(...)):
    await schedule_service.remove_schedule(schedule_id)
