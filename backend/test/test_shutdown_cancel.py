import asyncio
import tempfile
import unittest
from pathlib import Path
import sys
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.core.task_manager import 任务管理器
from backend.models.task import Task


class _假下载器:
    def __init__(self):
        self.已取消 = False

    async def 取消(self):
        self.已取消 = True


class TestShutdownCancel(unittest.TestCase):
    def test_shutdown_should_cancel_all_running_tasks_and_write_state(self):
        with tempfile.TemporaryDirectory() as 临时目录:
            async def 运行():
                管理器 = 任务管理器()
                管理器._任务文件路径 = Path(临时目录) / "tasks.json"
                管理器._任务文件路径.parent.mkdir(parents=True, exist_ok=True)
                管理器._获取任务日志路径 = lambda 任务ID: Path(临时目录) / "logs" / f"{任务ID}.log"
                await 管理器.初始化()

                任务 = Task(
                    id="t_shutdown",
                    url="https://example.com/a.m3u8",
                    name="a",
                    status="running",
                    progress=10.0,
                    speed=None,
                    eta=None,
                    created_at=datetime.now(timezone.utc),
                    started_at=datetime.now(timezone.utc),
                    completed_at=None,
                    error=None,
                )

                假下载器 = _假下载器()
                管理器._任务表[任务.id] = 任务
                管理器._运行中下载器[任务.id] = 假下载器
                管理器._运行中任务[任务.id] = asyncio.create_task(asyncio.sleep(10))

                await 管理器.关闭()

                self.assertTrue(假下载器.已取消)
                结果 = await 管理器.获取任务(任务.id)
                self.assertEqual(结果.status, "paused")
                self.assertEqual(结果.error, "服务关闭，任务已暂停")

                日志 = await 管理器.获取任务日志(任务.id, tail=200)
                全文 = "\n".join(日志.get("lines") or [])
                self.assertIn("服务关闭", 全文)

            asyncio.run(运行())


if __name__ == "__main__":
    unittest.main()
