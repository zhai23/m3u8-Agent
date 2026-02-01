"""
M3U8 下载器核心模块
封装 N_m3u8DL-RE 的调用逻辑
"""

import asyncio
import os
import re
import subprocess
import signal
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from datetime import datetime

from .config import get_config, Config


class M3U8下载器:
    """M3U8 下载器类"""
    
    def __init__(self, 配置: Optional[Config] = None):
        """
        初始化下载器
        
        Args:
            配置: 配置对象（可选，默认使用全局配置）
        """
        self.配置 = 配置 or get_config()
        
        # 从配置读取路径
        self.m3u8d路径 = Path(self.配置.m3u8d_path)
        self.默认保存目录 = Path(self.配置.save_dir)
        self.默认临时目录 = Path(self.配置.tmp_dir)
        
        # 确保目录存在
        self.默认保存目录.mkdir(parents=True, exist_ok=True)
        self.默认临时目录.mkdir(parents=True, exist_ok=True)
        
        # 检查 N_m3u8DL-RE 是否存在
        if not self.m3u8d路径.exists():
            raise FileNotFoundError(f"找不到 N_m3u8DL-RE: {self.m3u8d路径}")
        
        # 当前运行的进程（用于清理）
        self._当前进程: Optional[asyncio.subprocess.Process] = None
    
    async def 下载(
        self,
        链接: str,
        保存名称: str,
        保存目录: Optional[str] = None,
        临时目录: Optional[str] = None,
        线程数: Optional[int] = None,
        自定义请求头: Optional[list] = None,
        进度回调: Optional[Callable[[Dict[str, Any]], None]] = None,
        日志回调: Optional[Callable[[str], None]] = None,
        **其他参数
    ) -> bool:
        """
        下载 M3U8 视频
        
        Args:
            链接: M3U8 链接
            保存名称: 保存文件名（不含扩展名）
            保存目录: 保存目录（可选，最终文件存放位置）
            临时目录: 临时目录（可选，下载过程中的临时文件）
            线程数: 线程数（可选）
            自定义请求头: 自定义 HTTP 请求头（可选）
            进度回调: 进度回调函数
            日志回调: 日志回调函数
            **其他参数: 其他可覆盖的配置参数
            
        Returns:
            bool: 下载是否成功
        """
        最终保存目录 = Path(保存目录) if 保存目录 else self.默认保存目录
        最终临时目录 = Path(临时目录) if 临时目录 else self.默认临时目录
        
        # 确保目录存在
        最终保存目录.mkdir(parents=True, exist_ok=True)
        最终临时目录.mkdir(parents=True, exist_ok=True)
        
        # 构建命令
        命令 = self._构建下载命令(
            链接=链接,
            保存名称=保存名称,
            保存目录=最终保存目录,
            临时目录=最终临时目录,
            线程数=线程数,
            自定义请求头=自定义请求头,
            **其他参数
        )
        
        if 日志回调:
            日志回调(f"开始下载: {保存名称}")
            日志回调(f"命令: {' '.join(命令)}")
        
        try:
            # 执行下载
            成功 = await self._执行下载(命令, 进度回调, 日志回调)
            
            if 成功:
                if 日志回调:
                    日志回调(f"下载完成: {保存名称}")
                return True
            else:
                if 日志回调:
                    日志回调(f"下载失败: {保存名称}")
                return False
                
        except Exception as 异常:
            if 日志回调:
                日志回调(f"下载出错: {str(异常)}")
            return False
        finally:
            try:
                最终临时目录.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
    
    def _构建下载命令(
        self,
        链接: str,
        保存名称: str,
        保存目录: Path,
        临时目录: Path,
        线程数: Optional[int] = None,
        自定义请求头: Optional[list] = None,
        **其他参数
    ) -> list:
        """
        构建 N_m3u8DL-RE 命令
        
        Args:
            链接: M3U8 链接
            保存名称: 保存文件名
            保存目录: 保存目录
            临时目录: 临时目录
            线程数: 线程数（可选）
            自定义请求头: 自定义请求头（可选）
            **其他参数: 其他可覆盖的配置参数
        """
        命令 = [str(self.m3u8d路径), 链接]
        
        # 基础路径参数
        命令.extend(["--tmp-dir", str(临时目录)])
        命令.extend(["--save-dir", str(保存目录)])
        命令.extend(["--save-name", 保存名称])
        
        # 线程数
        最终线程数 = 线程数 if 线程数 is not None else self.配置.thread_count
        命令.extend(["--thread-count", str(最终线程数)])
        
        # 重试次数
        重试次数 = 其他参数.get("download_retry_count", self.配置.download_retry_count)
        命令.extend(["--download-retry-count", str(重试次数)])
        
        # HTTP 超时
        超时时间 = 其他参数.get("http_request_timeout", self.配置.http_request_timeout)
        命令.extend(["--http-request-timeout", str(超时时间)])
        
        # 布尔选项
        if 其他参数.get("check_segments_count", self.配置.check_segments_count):
            命令.append("--check-segments-count")
        
        if 其他参数.get("del_after_done", self.配置.del_after_done):
            命令.append("--del-after-done")
        
        if 其他参数.get("binary_merge", self.配置.binary_merge):
            命令.append("--binary-merge")
        
        if 其他参数.get("skip_merge", self.配置.skip_merge):
            命令.append("--skip-merge")
        
        if 其他参数.get("skip_download", self.配置.skip_download):
            命令.append("--skip-download")
        
        if 其他参数.get("no_log", self.配置.no_log):
            命令.append("--no-log")
        
        if not 其他参数.get("write_meta_json", self.配置.write_meta_json):
            # 注意：默认是 true，所以这里是反向逻辑
            pass
        
        if 其他参数.get("auto_select", self.配置.auto_select):
            命令.append("--auto-select")
        
        if 其他参数.get("append_url_params", self.配置.append_url_params):
            命令.append("--append-url-params")
        
        if 其他参数.get("no_date_info", self.配置.no_date_info):
            命令.append("--no-date-info")
        
        if 其他参数.get("force_ansi_console", self.配置.force_ansi_console):
            命令.append("--force-ansi-console")
        
        if 其他参数.get("sub_only", self.配置.sub_only):
            命令.append("--sub-only")
        
        if 其他参数.get("auto_subtitle_fix", self.配置.auto_subtitle_fix):
            命令.append("--auto-subtitle-fix")
        
        if 其他参数.get("mp4_real_time_decryption", self.配置.mp4_real_time_decryption):
            命令.append("--mp4-real-time-decryption")
        
        # 日志级别
        日志级别 = 其他参数.get("log_level", self.配置.log_level)
        if 日志级别:
            命令.extend(["--log-level", 日志级别])
        
        # 字幕格式
        字幕格式 = 其他参数.get("sub_format", self.配置.sub_format)
        if 字幕格式:
            命令.extend(["--sub-format", 字幕格式])
        
        # 解密引擎
        解密引擎 = 其他参数.get("decryption_engine", self.配置.decryption_engine)
        if 解密引擎:
            命令.extend(["--decryption-engine", 解密引擎])
        
        # 限速
        限速 = 其他参数.get("max_speed", self.配置.max_speed)
        if 限速:
            命令.extend(["-R", 限速])
        
        # 代理
        if not 其他参数.get("use_system_proxy", self.配置.use_system_proxy):
            # 如果不使用系统代理，需要明确禁用
            pass  # N_m3u8DL-RE 默认使用系统代理
        
        自定义代理 = 其他参数.get("custom_proxy", self.配置.custom_proxy)
        if 自定义代理:
            命令.extend(["--custom-proxy", 自定义代理])
        
        # 自定义请求头
        请求头列表 = 自定义请求头 if 自定义请求头 is not None else self.配置.custom_headers
        for 请求头 in 请求头列表:
            命令.extend(["-H", 请求头])
        
        # FFmpeg 路径
        ffmpeg路径 = 其他参数.get("ffmpeg_binary_path", self.配置.ffmpeg_binary_path)
        if ffmpeg路径:
            命令.extend(["--ffmpeg-binary-path", ffmpeg路径])
        
        # 解密工具路径
        解密工具路径 = 其他参数.get("decryption_binary_path", self.配置.decryption_binary_path)
        if 解密工具路径:
            命令.extend(["--decryption-binary-path", 解密工具路径])
        
        return 命令
    
    async def _执行下载(
        self,
        命令: list,
        进度回调: Optional[Callable[[Dict[str, Any]], None]],
        日志回调: Optional[Callable[[str], None]]
    ) -> bool:
        """执行下载命令并解析输出"""
        进程 = None
        try:
            # 创建子进程
            进程 = await asyncio.create_subprocess_exec(
                *命令,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # 保存当前进程引用
            self._当前进程 = 进程
            
            # 读取输出
            while True:
                行 = await 进程.stdout.readline()
                if not 行:
                    break
                
                # 尝试多种编码解码（优先 GBK，因为 Windows 中文环境）
                行文本 = None
                for 编码 in ['gbk', 'utf-8', 'cp936']:
                    try:
                        行文本 = 行.decode(编码).strip()
                        break
                    except (UnicodeDecodeError, LookupError):
                        continue
                
                if 行文本 is None:
                    行文本 = 行.decode('utf-8', errors='ignore').strip()
                
                if 日志回调:
                    日志回调(行文本)
                
                # 解析进度信息
                if 进度回调:
                    进度信息 = self._解析进度(行文本)
                    if 进度信息:
                        进度回调(进度信息)
            
            # 等待进程结束
            返回码 = await 进程.wait()
            
            return 返回码 == 0
            
        except asyncio.CancelledError:
            # 任务被取消，终止子进程
            if 日志回调:
                日志回调("下载被中断，正在停止...")
            if 进程 and 进程.returncode is None:
                await self._终止进程(进程)
            raise
            
        except Exception as 异常:
            if 日志回调:
                日志回调(f"执行命令出错: {str(异常)}")
            if 进程 and 进程.returncode is None:
                await self._终止进程(进程)
            return False
        
        finally:
            # 清理进程引用
            self._当前进程 = None
    
    async def _终止进程(self, 进程: asyncio.subprocess.Process):
        """终止子进程"""
        try:
            if os.name == 'nt':
                # Windows: 使用 taskkill 强制终止进程树
                subprocess.run(
                    ['taskkill', '/F', '/T', '/PID', str(进程.pid)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                # 等待进程结束并关闭管道
                try:
                    await asyncio.wait_for(进程.wait(), timeout=2.0)
                except asyncio.TimeoutError:
                    pass
                # 显式关闭管道以避免资源警告
                if 进程.stdout:
                    进程.stdout.close()
                if 进程.stderr:
                    进程.stderr.close()
            else:
                # Unix: 发送 SIGTERM
                进程.terminate()
                try:
                    await asyncio.wait_for(进程.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    # 如果 5 秒后还没结束，强制杀死
                    进程.kill()
                    await 进程.wait()
        except Exception:
            pass  # 忽略终止过程中的错误
    
    async def 取消(self):
        """取消当前下载"""
        if self._当前进程 and self._当前进程.returncode is None:
            await self._终止进程(self._当前进程)
    
    def _解析进度(self, 输出行: str) -> Optional[Dict[str, Any]]:
        """
        解析 N_m3u8DL-RE 输出的进度信息
        
        示例输出格式:
        [12:34:56] 45.5% | 2.5 MB/s | ETA: 00:02:30
        Vid 1280x720 | 0 Kbps ------------------------------ 523/739 70.77% 153.99MB/228.51MB 15.76MBps 00:00:03
        """
        # 匹配百分比
        百分比匹配 = re.search(r'(\d+\.?\d*)%', 输出行)
        
        # 匹配速度（注意：日志里还有 0 Kbps 这种码率信息，这里只识别大写 B 的下载速度）
        # 兼容：15.76MBps / 2.5 MB/s / 1.70MBps
        速度列表 = re.findall(r'(\d+(?:\.\d+)?)\s*([KMG]?B)\s*(?:/s|ps)\b', 输出行)
        速度 = None
        if 速度列表:
            数值, 单位 = 速度列表[-1]
            速度 = f"{数值} {单位}/s"
        
        # 匹配 ETA（兼容：ETA: 00:02:30 / 行尾 00:00:03 或 00:01:49 /）
        eta匹配 = re.search(r'ETA[:\s]+(\d{2}:\d{2}:\d{2})', 输出行)
        if not eta匹配:
            eta匹配 = re.search(r'(\d{2}:\d{2}:\d{2})(?=\s*(?:/|$))', 输出行)
        
        if 百分比匹配:
            进度信息 = {
                "percent": float(百分比匹配.group(1)),
                "speed": 速度,
                "eta": eta匹配.group(1) if eta匹配 else None,
                "timestamp": datetime.now().isoformat()
            }
            return 进度信息
        
        return None
    
    def 获取下载路径(self, 保存名称: str, 保存目录: Optional[str] = None) -> Path:
        """获取下载文件的完整路径"""
        最终保存目录 = Path(保存目录) if 保存目录 else self.默认保存目录
        # N_m3u8DL-RE 通常会自动添加扩展名（如 .mp4）
        return 最终保存目录 / f"{保存名称}.mp4"


# 同步版本的简单封装（用于测试）
class 简单下载器:
    """简化的同步下载器（用于快速测试）"""
    
    def __init__(self, 配置: Optional[Config] = None):
        """
        初始化简单下载器
        
        Args:
            配置: 配置对象（可选）
        """
        self.下载器 = M3U8下载器(配置=配置)
        self._下载任务: Optional[asyncio.Task] = None
    
    def 下载(
        self,
        链接: str,
        保存名称: str,
        保存目录: Optional[str] = None,
        临时目录: Optional[str] = None,
        线程数: Optional[int] = None,
        自定义请求头: Optional[list] = None,
        **其他参数
    ) -> bool:
        """
        同步下载方法
        
        Args:
            链接: M3U8 链接
            保存名称: 保存文件名
            保存目录: 保存目录（最终文件存放位置）
            临时目录: 临时目录（下载过程中的临时文件）
            线程数: 线程数
            自定义请求头: 自定义请求头
            **其他参数: 其他可覆盖的配置参数
            
        Returns:
            bool: 是否成功
        """
        def 进度回调(进度: Dict[str, Any]):
            百分比 = 进度.get("percent", 0)
            速度 = 进度.get("speed", "N/A")
            剩余时间 = 进度.get("eta", "N/A")
            print(f"进度: {百分比:.1f}% | 速度: {速度} | 剩余时间: {剩余时间}")
        
        def 日志回调(消息: str):
            print(f"[日志] {消息}")
        
        # 设置信号处理
        async def _运行下载():
            """异步运行下载任务"""
            try:
                return await self.下载器.下载(
                    链接=链接,
                    保存名称=保存名称,
                    保存目录=保存目录,
                    临时目录=临时目录,
                    线程数=线程数,
                    自定义请求头=自定义请求头,
                    进度回调=进度回调,
                    日志回调=日志回调,
                    **其他参数
                )
            except KeyboardInterrupt:
                日志回调("检测到中断信号，正在停止下载...")
                await self.下载器.取消()
                return False
        
        # 运行异步下载
        try:
            if os.name == 'nt':
                # Windows: 使用默认事件循环
                return asyncio.run(_运行下载())
            else:
                # Unix: 设置信号处理
                事件循环 = asyncio.new_event_loop()
                asyncio.set_event_loop(事件循环)
                
                def _信号处理器(信号, 帧):
                    日志回调("检测到中断信号，正在停止下载...")
                    if self._下载任务:
                        self._下载任务.cancel()
                
                signal.signal(signal.SIGINT, _信号处理器)
                signal.signal(signal.SIGTERM, _信号处理器)
                
                try:
                    self._下载任务 = 事件循环.create_task(_运行下载())
                    return 事件循环.run_until_complete(self._下载任务)
                finally:
                    事件循环.close()
        except KeyboardInterrupt:
            日志回调("下载已中断")
            return False
