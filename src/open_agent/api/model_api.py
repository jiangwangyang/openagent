from fastapi import APIRouter

from open_agent.repository import setting_repository

router = APIRouter()


@router.get("/provider/list")
async def list_model_provider():
    settings = await setting_repository.get_settings()
    model_providers = settings.get("model_providers", {})
    return [{
        "name": k,
        "base_url": v.get("base_url", ""),
        "api_key": v.get("api_key", ""),
        "models": v.get("models", [])
    } for k, v in model_providers.items()]


@router.post("/provider/{name}")
async def update_model_provider(name: str, body: dict):
    settings = await setting_repository.get_settings()
    if not "model_providers" in settings:
        settings["model_providers"] = {}
    settings["model_providers"][name] = body
    await setting_repository.save_settings(settings)


@router.delete("/provider/{name}")
async def delete_model_provider(name: str):
    settings = await setting_repository.get_settings()
    if "model_providers" in settings and name in settings["model_providers"]:
        del settings["model_providers"][name]
        await setting_repository.save_settings(settings)


@router.get("/select")
async def get_model_select():
    settings = await setting_repository.get_settings()
    return {
        "model_provider": settings.get("model_provider", ""),
        "model": settings.get("model", "")
    }


@router.post("/select")
async def update_model_select(body: dict):
    settings = await setting_repository.get_settings()
    settings["model_provider"] = body["model_provider"]
    settings["model"] = body["model"]
    await setting_repository.save_settings(settings)
