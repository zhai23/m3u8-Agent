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
        关闭事件 = getattr(request.app.state, "shutdown_event", None)
        try:
            yield "retry: 3000\n\n"
            try:
                while True:
                    if 关闭事件 and 关闭事件.is_set():
                        break
                    if await request.is_disconnected():
                        break
                    try:
                        取事件任务 = asyncio.create_task(订阅队列.get())
                        等待任务 = {取事件任务}
                        关闭任务 = None
                        if 关闭事件:
                            关闭任务 = asyncio.create_task(关闭事件.wait())
                            等待任务.add(关闭任务)

                        完成, 未完成 = await asyncio.wait(等待任务, timeout=5.0, return_when=asyncio.FIRST_COMPLETED)
                        for t in 未完成:
                            t.cancel()

                        if not 完成:
                            yield "event: ping\ndata: {}\n\n"
                            continue
                        if 关闭任务 and 关闭任务 in 完成:
                            break
                        if 取事件任务 in 完成:
                            事件对象 = 取事件任务.result()
                            yield _格式化SSE(事件对象.event, 事件对象.data)
                    except asyncio.TimeoutError:
                        yield "event: ping\ndata: {}\n\n"
            except asyncio.CancelledError:
                return
        finally:
            await 任务管理.事件总线.取消订阅(订阅队列)

    return StreamingResponse(生成器(), media_type="text/event-stream")
