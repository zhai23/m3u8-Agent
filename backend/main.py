from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
import sys

项目根目录 = Path(__file__).resolve().parent.parent
if str(项目根目录) not in sys.path:
    sys.path.insert(0, str(项目根目录))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import tasks_router, config_router, stream_router, status_router
from backend.core.task_manager import 任务管理器


@asynccontextmanager
async def 生命周期(app: FastAPI):
    任务管理 = 任务管理器()
    await 任务管理.初始化()
    app.state.task_manager = 任务管理
    app.state.shutdown_event = asyncio.Event()
    yield
    try:
        try:
            app.state.shutdown_event.set()
        except Exception:
            pass
        await asyncio.shield(任务管理.关闭())
    except Exception:
        pass


app = FastAPI(title="M3U8 Agent", lifespan=生命周期)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(status_router)
app.include_router(config_router)
app.include_router(tasks_router)
app.include_router(stream_router)


if __name__ == "__main__":
    import os
    import uvicorn

    host = os.environ.get("M3U8_AGENT_HOST", "0.0.0.0")
    port = int(os.environ.get("M3U8_AGENT_PORT", "8000"))
    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=False,
        timeout_graceful_shutdown=5,
    )
