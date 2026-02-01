from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any, Dict

import toml
from fastapi import APIRouter, HTTPException

from backend.core.config import reload_config
from backend.models.config import AppConfig


router = APIRouter(prefix="/api", tags=["config"])


def _配置文件路径() -> Path:
    return Path(__file__).parent.parent / "config.toml"


def _读取配置() -> Dict[str, Any]:
    路径 = _配置文件路径()
    if not 路径.exists():
        return {}
    with open(路径, "rb") as f:
        return tomllib.load(f)


def _写入配置(配置: Dict[str, Any]):
    路径 = _配置文件路径()
    文本 = toml.dumps(配置)
    路径.write_text(文本, encoding="utf-8")


def _合并字典(旧: Dict[str, Any], 新: Dict[str, Any]) -> Dict[str, Any]:
    结果: Dict[str, Any] = dict(旧)
    for 键, 值 in 新.items():
        if isinstance(值, dict) and isinstance(结果.get(键), dict):
            结果[键] = _合并字典(结果[键], 值)
        else:
            结果[键] = 值
    return 结果


@router.get("/config", response_model=AppConfig)
async def 获取配置():
    return AppConfig(config=_读取配置())


@router.put("/config", response_model=AppConfig)
async def 更新配置(请求: AppConfig):
    try:
        旧配置 = _读取配置()
        新配置 = _合并字典(旧配置, 请求.config)
        _写入配置(新配置)
        reload_config()
        return AppConfig(config=_读取配置())
    except Exception as 异常:
        raise HTTPException(status_code=500, detail=f"更新配置失败: {异常}")
