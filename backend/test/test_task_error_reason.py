import asyncio
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import backend.core.task_manager as task_manager_mod
from backend.core.task_manager import 任务管理器


class _失败下载器:
    async def 下载(self, 链接, 保存名称, 进度回调=None, 日志回调=None, **kwargs):
        if 日志回调:
            日志回调("命令: N_m3u8DL-RE -H secret-token=xxx")
            日志回调("ERROR: 404 Not Found")
        await asyncio.sleep(0.01)
        return False

    async def 取消(self):
        return


class TestTaskErrorReason(unittest.TestCase):
    def test_failed_task_should_expose_log_and_keep_error_simple(self):
        原下载器类 = task_manager_mod.M3U8下载器
        task_manager_mod.M3U8下载器 = _失败下载器
        try:
            with tempfile.TemporaryDirectory() as 临时目录:
                async def 运行():
                    管理器 = 任务管理器()
                    管理器._任务文件路径 = Path(临时目录) / "tasks.json"
                    管理器._任务文件路径.parent.mkdir(parents=True, exist_ok=True)
                    管理器._获取任务日志路径 = lambda 任务ID: Path(临时目录) / "logs" / f"{任务ID}.log"
                    await 管理器.初始化()
                    任务 = await 管理器.创建任务("https://example.com/404.m3u8", "e1")
                    await 管理器.开始任务(任务.id)
                    await asyncio.sleep(0.05)
                    结果 = await 管理器.获取任务(任务.id)
                    self.assertEqual(结果.status, "failed")
                    self.assertEqual(结果.error, "下载失败")

                    日志 = await 管理器.获取任务日志(任务.id, tail=200)
                    全文 = "\n".join(日志.get("lines") or [])
                    self.assertIn("ERROR: 404 Not Found", 全文)
                    self.assertNotIn("命令:", 全文)

                asyncio.run(运行())
        finally:
            task_manager_mod.M3U8下载器 = 原下载器类


if __name__ == "__main__":
    unittest.main()
