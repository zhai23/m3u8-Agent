from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
import shutil
import stat

import aiofiles

from backend.core.downloader import M3U8下载器
from backend.core.config import get_config
from backend.models.task import Task
from .event_bus import 事件总线


class 任务管理器:
    def __init__(self, 最大并发数: int = 3):
        self._任务文件路径 = Path(__file__).parent.parent / "data" / "tasks.json"
        self._任务文件路径.parent.mkdir(parents=True, exist_ok=True)

        self._锁 = asyncio.Lock()
        self._并发信号量 = asyncio.Semaphore(最大并发数)
        self._事件总线 = 事件总线()

        self._任务表: Dict[str, Task] = {}
        self._运行中任务: Dict[str, asyncio.Task] = {}
        self._运行中下载器: Dict[str, M3U8下载器] = {}
        self._停止原因: Dict[str, str] = {}
        self._上次落盘时间: Dict[str, float] = {}

    @property
    def 事件总线(self) -> 事件总线:
        return self._事件总线

    async def 初始化(self):
        await self._加载任务文件()

    async def 列出任务(self) -> List[Task]:
        async with self._锁:
            return list(self._任务表.values())

    async def 获取任务(self, 任务ID: str) -> Task:
        async with self._锁:
            任务 = self._任务表.get(任务ID)
            if not 任务:
                raise KeyError("任务不存在")
            return 任务

    async def 创建任务(self, 链接: str, 保存名称: str) -> Task:
        保存名称 = (保存名称 or "").strip()
        self._检查保存名称(保存名称)
        现在 = datetime.now(timezone.utc)
        任务 = Task(
            id=str(uuid.uuid4()),
            url=链接,
            name=保存名称,
            status="pending",
            progress=0.0,
            speed=None,
            eta=None,
            created_at=现在,
            started_at=None,
            completed_at=None,
            error=None,
        )
        async with self._锁:
            for 已有任务 in self._任务表.values():
                if 已有任务.name == 保存名称:
                    raise ValueError("保存名称已存在，请换一个名称")
            self._任务表[任务.id] = 任务
            await self._保存任务文件(需持锁=True)
        await self._事件总线.发布("task.created", {"task": 任务.model_dump(mode="json")})
        return 任务

    async def 删除任务(self, 任务ID: str):
        async with self._锁:
            任务 = self._任务表.get(任务ID)
            if not 任务:
                raise KeyError("任务不存在")
            保存名称 = 任务.name
            需要清理临时文件 = 任务.status != "completed"

        await self._停止任务用于删除(任务ID)
        if 需要清理临时文件:
            await self._清理临时目录(保存名称)
        async with self._锁:
            if 任务ID in self._任务表:
                del self._任务表[任务ID]
                await self._保存任务文件(需持锁=True)

    async def 开始任务(self, 任务ID: str) -> Task:
        async with self._锁:
            任务 = self._任务表.get(任务ID)
            if not 任务:
                raise KeyError("任务不存在")
            if 任务.status in ("running", "completed"):
                return 任务
            任务.status = "running"
            任务.error = None
            if not 任务.started_at:
                任务.started_at = datetime.now(timezone.utc)
            await self._保存任务文件(需持锁=True)

            if 任务ID not in self._运行中任务 or self._运行中任务[任务ID].done():
                self._停止原因.pop(任务ID, None)
                协程任务 = asyncio.create_task(self._运行下载任务(任务ID), name=f"download:{任务ID}")
                self._运行中任务[任务ID] = 协程任务

        return await self.获取任务(任务ID)

    async def 暂停任务(self, 任务ID: str) -> Task:
        async with self._锁:
            任务 = self._任务表.get(任务ID)
            if not 任务:
                raise KeyError("任务不存在")
            if 任务.status != "running":
                return 任务
            self._停止原因[任务ID] = "paused"
            下载器 = self._运行中下载器.get(任务ID)
            运行任务 = self._运行中任务.get(任务ID)

        if 下载器:
            await 下载器.取消()
        if 运行任务 and not 运行任务.done():
            运行任务.cancel()

        async with self._锁:
            任务 = self._任务表.get(任务ID)
            if 任务:
                任务.status = "paused"
                await self._保存任务文件(需持锁=True)
        return await self.获取任务(任务ID)

    async def _运行下载任务(self, 任务ID: str):
        async with self._并发信号量:
            下载器 = M3U8下载器()
            async with self._锁:
                self._运行中下载器[任务ID] = 下载器

            loop = asyncio.get_running_loop()

            def 进度回调(进度: Dict[str, Any]):
                loop.create_task(self._更新任务进度(任务ID, 进度))

            try:
                async with self._锁:
                    任务 = self._任务表.get(任务ID)
                    if not 任务 or 任务.status != "running":
                        return
                    链接 = 任务.url
                    保存名称 = 任务.name

                成功 = await 下载器.下载(
                    链接=链接,
                    保存名称=保存名称,
                    进度回调=进度回调,
                )

                async with self._锁:
                    任务 = self._任务表.get(任务ID)
                    if not 任务:
                        return

                    停止原因 = self._停止原因.get(任务ID)
                    if 停止原因 == "paused":
                        任务.status = "paused"
                        await self._保存任务文件(需持锁=True)
                        return
                    if 停止原因 == "deleting":
                        return

                    if 成功:
                        任务.status = "completed"
                        任务.progress = 100.0
                        任务.completed_at = datetime.now(timezone.utc)
                        任务.error = None
                        await self._保存任务文件(需持锁=True)
                        await self._事件总线.发布("task.completed", {"task": 任务.model_dump(mode="json")})
                    else:
                        任务.status = "failed"
                        if not 任务.error:
                            任务.error = "下载失败"
                        await self._保存任务文件(需持锁=True)
                        await self._事件总线.发布("task.failed", {"task": 任务.model_dump(mode="json")})

            except asyncio.CancelledError:
                async with self._锁:
                    任务 = self._任务表.get(任务ID)
                    if 任务 and 任务.status == "running":
                        停止原因 = self._停止原因.get(任务ID)
                        if 停止原因 == "paused":
                            任务.status = "paused"
                            await self._保存任务文件(需持锁=True)
                            return
                        if 停止原因 == "deleting":
                            return
                        else:
                            任务.status = "failed"
                            任务.error = "任务被中断"
                        await self._保存任务文件(需持锁=True)
                return
            finally:
                async with self._锁:
                    self._运行中下载器.pop(任务ID, None)
                    self._停止原因.pop(任务ID, None)

    async def _更新任务进度(self, 任务ID: str, 进度: Dict[str, Any]):
        现在戳 = asyncio.get_running_loop().time()
        async with self._锁:
            任务 = self._任务表.get(任务ID)
            if not 任务 or 任务.status != "running":
                return
            if "percent" in 进度 and 进度["percent"] is not None:
                try:
                    任务.progress = float(进度["percent"])
                except (ValueError, TypeError):
                    pass
            if "speed" in 进度 and 进度["speed"] is not None:
                任务.speed = str(进度["speed"])
            if "eta" in 进度 and 进度["eta"] is not None:
                任务.eta = str(进度["eta"])

            上次 = self._上次落盘时间.get(任务ID, 0.0)
            需要落盘 = (现在戳 - 上次) >= 1.0 or 任务.progress >= 100.0
            if 需要落盘:
                self._上次落盘时间[任务ID] = 现在戳
                await self._保存任务文件(需持锁=True)

            事件数据 = {
                "task_id": 任务ID,
                "percent": 任务.progress,
                "speed": 任务.speed,
                "eta": 任务.eta,
            }

        await self._事件总线.发布("task.progress", 事件数据)

    async def _加载任务文件(self):
        if not self._任务文件路径.exists():
            async with aiofiles.open(self._任务文件路径, "w", encoding="utf-8") as f:
                await f.write("[]")
            return

        async with aiofiles.open(self._任务文件路径, "r", encoding="utf-8") as f:
            文本 = await f.read()
        try:
            数据 = json.loads(文本) if 文本.strip() else []
        except json.JSONDecodeError:
            数据 = []

        async with self._锁:
            self._任务表 = {项["id"]: Task.model_validate(项) for 项 in 数据 if isinstance(项, dict) and "id" in 项}

    async def _保存任务文件(self, 需持锁: bool = False):
        if not 需持锁:
            async with self._锁:
                return await self._保存任务文件(需持锁=True)

        数据 = [任务.model_dump(mode="json") for 任务 in self._任务表.values()]
        文本 = json.dumps(数据, ensure_ascii=False, indent=2)
        async with aiofiles.open(self._任务文件路径, "w", encoding="utf-8") as f:
            await f.write(文本)

    async def _停止任务用于删除(self, 任务ID: str):
        async with self._锁:
            任务 = self._任务表.get(任务ID)
            if not 任务:
                raise KeyError("任务不存在")
            if 任务.status not in ("running", "pending", "paused"):
                return
            self._停止原因[任务ID] = "deleting"
            下载器 = self._运行中下载器.get(任务ID)
            运行任务 = self._运行中任务.get(任务ID)

        if 下载器:
            await 下载器.取消()
        if 运行任务 and not 运行任务.done():
            运行任务.cancel()

    def _检查保存名称(self, 保存名称: str):
        if not 保存名称:
            raise ValueError("保存名称不能为空")
        if "/" in 保存名称 or "\\" in 保存名称:
            raise ValueError("保存名称不能包含路径分隔符")
        if any(字符 in 保存名称 for 字符 in '<>:"|?*'):
            raise ValueError("保存名称包含非法字符")
        if 保存名称 in (".", ".."):
            raise ValueError("保存名称不合法")
        if Path(保存名称).name != 保存名称:
            raise ValueError("保存名称不合法")

    async def _清理临时目录(self, 保存名称: str):
        try:
            self._检查保存名称(保存名称)
        except Exception:
            return

        配置 = get_config()
        临时根目录 = Path(配置.tmp_dir)
        待删除目录 = 临时根目录 / 保存名称
        if not 待删除目录.exists():
            return

        def _处理删除错误(函数, 路径, 异常信息):
            try:
                os.chmod(路径, stat.S_IWRITE)
            except Exception:
                pass
            函数(路径)

        import os

        for _ in range(10):
            try:
                await asyncio.to_thread(shutil.rmtree, 待删除目录, onerror=_处理删除错误)
                return
            except FileNotFoundError:
                return
            except PermissionError:
                await asyncio.sleep(0.2)
            except OSError:
                await asyncio.sleep(0.2)
