from __future__ import annotations

import asyncio
import json
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from backend.core.task_manager import 任务管理器
from .deps import 获取任务管理器


router = APIRouter(prefix="/api/stream", tags=["stream"])


def _格式化SSE(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.get("/tasks")
async def 任务事件流(
    request: Request,
    任务管理: 任务管理器 = Depends(获取任务管理器),
):
    订阅队列 = await 任务管理.事件总线.订阅()

    async def 生成器() -> AsyncGenerator[str, None]:
        try:
            yield "retry: 3000\n\n"
            try:
                while True:
                    if await request.is_disconnected():
                        break
                    try:
                        事件对象 = await asyncio.wait_for(订阅队列.get(), timeout=5.0)
                        yield _格式化SSE(事件对象.event, 事件对象.data)
                    except asyncio.TimeoutError:
                        yield "event: ping\ndata: {}\n\n"
            except asyncio.CancelledError:
                return
        finally:
            await 任务管理.事件总线.取消订阅(订阅队列)

    return StreamingResponse(生成器(), media_type="text/event-stream")
