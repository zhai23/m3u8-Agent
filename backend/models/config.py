from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel


class AppConfig(BaseModel):
    config: Dict[str, Any]
