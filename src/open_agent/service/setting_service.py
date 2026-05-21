import json
import os
import pathlib

import anyio
from fastapi import APIRouter

router = APIRouter()
SETTINGS_FILE = str(pathlib.Path.home() / ".openagent" / "settings.json")


async def init_settings():
    # 查询现有配置
    settings_file = anyio.Path(SETTINGS_FILE)
    content = await settings_file.read_text(encoding="utf-8") if await settings_file.exists() else ""
    settings = json.loads(content) if content else {}
    model_providers = settings.get("model_providers", {})
    # 增加 DeepSeek
    if "deepseek" not in model_providers and os.getenv("DEEPSEEK_API_KEY", ""):
        model_providers["deepseek"] = {
            "name": "DeepSeek",
            "base_url": "https://api.deepseek.com/anthropic",
            "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
            "models": [
                "deepseek-v4-flash",
                "deepseek-v4-pro"
            ]
        }
    # 增加 MiniMax
    if "minimax" not in model_providers and os.getenv("MINIMAX_API_KEY", ""):
        model_providers["minimax"] = {
            "name": "MiniMax",
            "base_url": "https://api.minimax.chat/anthropic",
            "api_key": os.getenv("MINIMAX_API_KEY", ""),
            "models": [
                "MiniMax-M2.7"
            ]
        }
    # 保存配置
    if not "model_provider" in settings and model_providers:
        settings["model_provider"] = next(iter(model_providers))
    if not "model" in settings and "model_provider" in settings:
        settings["model"] = model_providers[settings["model_provider"]]["models"][0]
    settings["model_providers"] = model_providers
    await settings_file.parent.mkdir(parents=True, exist_ok=True)
    await settings_file.write_text(json.dumps(settings, ensure_ascii=False, indent=4), encoding="utf-8")


async def get_settings() -> dict:
    settings_file = anyio.Path(SETTINGS_FILE)
    content = await settings_file.read_text(encoding="utf-8") if await settings_file.exists() else ""
    return json.loads(content) if content else {}


async def save_settings(content: dict):
    settings_file = anyio.Path(SETTINGS_FILE)
    await settings_file.parent.mkdir(parents=True, exist_ok=True)
    file_content = json.dumps(content, ensure_ascii=False, indent=4)
    await settings_file.write_text(file_content, encoding="utf-8")
