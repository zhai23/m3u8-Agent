from __future__ import annotations

from fastapi import APIRouter, Depends

from backend import __version__
from backend.core.task_manager import 任务管理器
from .deps import 获取任务管理器


router = APIRouter(prefix="/api", tags=["status"])


@router.get("/status")
async def 获取系统状态(任务管理: 任务管理器 = Depends(获取任务管理器)):
    任务列表 = await 任务管理.列出任务()
    运行中 = sum(1 for 任务 in 任务列表 if 任务.status == "running")
    return {"ok": True, "version": __version__, "tasks": len(任务列表), "running": 运行中}
