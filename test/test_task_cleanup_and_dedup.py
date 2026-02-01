import asyncio
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.core.config import get_config
from backend.core.task_manager import 任务管理器


class TestTaskCleanupAndDedup(unittest.TestCase):
    def test_delete_pending_task_removes_tmp_folder(self):
        配置 = get_config()
        临时根目录 = Path(配置.tmp_dir)
        临时根目录.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory() as 临时目录:
            async def 运行():
                管理器 = 任务管理器()
                管理器._任务文件路径 = Path(临时目录) / "tasks.json"
                管理器._任务文件路径.parent.mkdir(parents=True, exist_ok=True)
                await 管理器.初始化()

                任务 = await 管理器.创建任务(链接="https://example.com/a.m3u8", 保存名称="__tmp_cleanup_test__")

                目录 = 临时根目录 / 任务.name
                目录.mkdir(parents=True, exist_ok=True)
                (目录 / "a.txt").write_text("x", encoding="utf-8")

                self.assertTrue(目录.exists())
                await 管理器.删除任务(任务.id)
                self.assertFalse(目录.exists())

            asyncio.run(运行())

    def test_dedup_name(self):
        with tempfile.TemporaryDirectory() as 临时目录:
            async def 运行():
                管理器 = 任务管理器()
                管理器._任务文件路径 = Path(临时目录) / "tasks.json"
                管理器._任务文件路径.parent.mkdir(parents=True, exist_ok=True)
                await 管理器.初始化()

                await 管理器.创建任务(链接="https://example.com/a.m3u8", 保存名称="同名任务")
                with self.assertRaises(ValueError):
                    await 管理器.创建任务(链接="https://example.com/b.m3u8", 保存名称="同名任务")

            asyncio.run(运行())


if __name__ == "__main__":
    unittest.main()

