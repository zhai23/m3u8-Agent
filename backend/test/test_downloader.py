"""
M3U8 下载器测试脚本
可以直接在脚本中写入名称和链接进行下载测试
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.core.downloader import 简单下载器
from backend.core.config import get_config


def main():
    """主测试函数"""
    
    # ========== 在这里配置你的下载任务 ==========
    
    # 任务名称（保存的文件名，不需要扩展名）
    任务名称 = "测试视频"
    
    # M3U8 链接
    m3u8链接 = "https://v4.zuidazym3u8.com/yyv4/202411/01/CBT6uA2wNr23/video/index.m3u8"
    
    # 以下参数可选，留空则使用 config.toml 中的配置
    保存目录 = None  # 留空使用配置文件中的 save_dir
    临时目录 = None  # 留空使用配置文件中的 tmp_dir
    线程数 = None    # 留空使用配置文件中的 thread_count
    
    # 自定义请求头（可选）
    # 示例: ["Cookie: mycookie", "User-Agent: Mozilla/5.0"]
    自定义请求头 = None
    
    # ==========================================
    
    # 加载配置
    配置 = get_config()
    
    print("=" * 60)
    print("M3U8 下载器测试")
    print("=" * 60)
    print(f"任务名称: {任务名称}")
    print(f"M3U8 链接: {m3u8链接}")
    print(f"保存目录: {保存目录 or 配置.save_dir} (配置文件)")
    print(f"临时目录: {临时目录 or 配置.tmp_dir} (配置文件)")
    print(f"线程数: {线程数 or 配置.thread_count} (配置文件)")
    print("=" * 60)
    print()
    
    # 创建下载器
    try:
        下载器 = 简单下载器()
    except FileNotFoundError as 异常:
        print(f"错误: {异常}")
        print("请确保 N_m3u8DL-RE.exe 位于配置文件指定的路径")
        return
    
    # 开始下载
    print("开始下载...")
    print()
    
    成功 = 下载器.下载(
        链接=m3u8链接,
        保存名称=任务名称,
        保存目录=保存目录,
        临时目录=临时目录,
        线程数=线程数,
        自定义请求头=自定义请求头
    )
    
    print()
    print("=" * 60)
    if 成功:
        print("✓ 下载成功!")
        最终目录 = 保存目录 or 配置.save_dir
        print(f"文件保存在: {最终目录}/{任务名称}.mp4")
    else:
        print("✗ 下载失败!")
    print("=" * 60)


def 快速测试(名称: str, 链接: str, **其他参数):
    """
    快速测试函数 - 可以直接调用
    
    使用示例:
        from test_downloader import 快速测试
        快速测试("我的视频", "https://example.com/video.m3u8")
        
        # 带自定义参数
        快速测试("我的视频", "https://example.com/video.m3u8",
                线程数=8,
                自定义请求头=["User-Agent: iOS"])
    """
    下载器 = 简单下载器()
    return 下载器.下载(链接=链接, 保存名称=名称, **其他参数)


if __name__ == "__main__":
    # 检查是否有命令行参数
    if len(sys.argv) >= 3:
        # 从命令行获取参数
        任务名称 = sys.argv[1]
        m3u8链接 = sys.argv[2]
        
        print(f"从命令行参数启动下载:")
        print(f"  名称: {任务名称}")
        print(f"  链接: {m3u8链接}")
        print()
        
        下载器 = 简单下载器()
        成功 = 下载器.下载(链接=m3u8链接, 保存名称=任务名称)
        
        if 成功:
            print("\n✓ 下载成功!")
        else:
            print("\n✗ 下载失败!")
    else:
        # 使用脚本内配置的参数
        main()
