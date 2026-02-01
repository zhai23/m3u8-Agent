from __future__ import annotations

from fastapi import Request

from backend.core.task_manager import 任务管理器


def 获取任务管理器(request: Request) -> 任务管理器:
    return request.app.state.task_manager

