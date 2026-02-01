from .tasks import router as tasks_router
from .config import router as config_router
from .stream import router as stream_router
from .status import router as status_router

__all__ = ["tasks_router", "config_router", "stream_router", "status_router"]
