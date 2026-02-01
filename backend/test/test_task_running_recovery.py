import asyncio
import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import backend.core.task_manager as task_manager_mod
from backend.core.task_manager import 任务管理器


class _假下载器:
    async def 初始化(self):
        return

    async def 下载(self, 链接, 保存名称, 进度回调=None, **kwargs):
        if 进度回调:
            进度回调({"percent": 1.0, "speed": "1 MB/s", "eta": "00:00:01"})
        await asyncio.sleep(0.01)
        if 进度回调:
            进度回调({"percent": 100.0, "speed": "1 MB/s", "eta": "00:00:00"})
        return True

    async def 取消(self):
        return


class TestTaskRunningRecovery(unittest.TestCase):
    def test_running_tasks_marked_paused_on_startup(self):
        with tempfile.TemporaryDirectory() as 临时目录:
            tasks_path = Path(临时目录) / "tasks.json"
            tasks_path.write_text(
                json.dumps(
                    [
                        {
                            "id": "t1",
                            "url": "https://example.com/a.m3u8",
                            "name": "a",
                            "status": "running",
                            "progress": 0.0,
                            "speed": None,
                            "eta": None,
                            "created_at": "2026-02-01T00:00:00Z",
                            "started_at": None,
                            "completed_at": None,
                            "error": None,
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            async def 运行():
                管理器 = 任务管理器()
                管理器._任务文件路径 = tasks_path
                await 管理器.初始化()
                任务 = await 管理器.获取任务("t1")
                self.assertEqual(任务.status, "paused")

            asyncio.run(运行())

    def test_start_can_restart_running_without_worker(self):
        原下载器类 = task_manager_mod.M3U8下载器
        task_manager_mod.M3U8下载器 = _假下载器
        try:
            with tempfile.TemporaryDirectory() as 临时目录:
                async def 运行():
                    管理器 = 任务管理器()
                    管理器._任务文件路径 = Path(临时目录) / "tasks.json"
                    管理器._任务文件路径.parent.mkdir(parents=True, exist_ok=True)
                    await 管理器.初始化()
                    任务 = await 管理器.创建任务("https://example.com/a.m3u8", "a1")
                    await 管理器.开始任务(任务.id)
                    await asyncio.sleep(0.05)
                    任务2 = await 管理器.获取任务(任务.id)
                    self.assertIn(任务2.status, ("running", "completed"))

                asyncio.run(运行())
        finally:
            task_manager_mod.M3U8下载器 = 原下载器类


if __name__ == "__main__":
    unittest.main()
