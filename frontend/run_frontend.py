from __future__ import annotations

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import os


def main():
    前端目录 = Path(__file__).resolve().parent
    os.chdir(前端目录)

    端口 = int(os.environ.get("M3U8_FRONTEND_PORT", "8100"))
    地址 = os.environ.get("M3U8_FRONTEND_HOST", "0.0.0.0")

    处理器 = SimpleHTTPRequestHandler
    httpd = ThreadingHTTPServer((地址, 端口), 处理器)
    print(f"前端已启动: http://127.0.0.1:{端口}/")
    httpd.serve_forever()


if __name__ == "__main__":
    main()

