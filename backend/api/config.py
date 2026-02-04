from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.core.config import reload_config, read_config_toml, write_config_toml, deep_merge_dict
from backend.models.config import AppConfig


router = APIRouter(prefix="/api", tags=["config"])


@router.get("/config", response_model=AppConfig)
async def 获取配置():
    return AppConfig(config=read_config_toml())


@router.put("/config", response_model=AppConfig)
async def 更新配置(请求: AppConfig):
    try:
        旧配置 = read_config_toml()
        新配置 = deep_merge_dict(旧配置, 请求.config)
        write_config_toml(新配置)
        reload_config()
        return AppConfig(config=read_config_toml())
    except Exception as 异常:
        raise HTTPException(status_code=500, detail=f"更新配置失败: {异常}")
