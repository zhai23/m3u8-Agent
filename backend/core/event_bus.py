from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, Set


@dataclass(frozen=True)
class 事件:
    event: str
    data: Dict[str, Any]


class 事件总线:
    def __init__(self):
        self._订阅者: Set[asyncio.Queue[事件]] = set()
        self._锁 = asyncio.Lock()

    async def 订阅(self) -> asyncio.Queue[事件]:
        队列: asyncio.Queue[事件] = asyncio.Queue(maxsize=1000)
        async with self._锁:
            self._订阅者.add(队列)
        return 队列

    async def 取消订阅(self, 队列: asyncio.Queue[事件]):
        async with self._锁:
            self._订阅者.discard(队列)

    async def 发布(self, event: str, data: Dict[str, Any]):
        事件对象 = 事件(event=event, data=data)
        async with self._锁:
            订阅者列表 = list(self._订阅者)
        for 队列 in 订阅者列表:
            try:
                队列.put_nowait(事件对象)
            except asyncio.QueueFull:
                try:
                    _ = 队列.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                try:
                    队列.put_nowait(事件对象)
                except asyncio.QueueFull:
                    pass
