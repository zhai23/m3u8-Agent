from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse

from backend.core.task_manager import 任务管理器
from backend.models.task import Task, TaskCreateRequest
from .deps import 获取任务管理器


router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=list[Task])
async def 获取所有任务(任务管理: 任务管理器 = Depends(获取任务管理器)):
    return await 任务管理.列出任务()


@router.post("", response_model=Task)
async def 创建新任务(
    请求: TaskCreateRequest,
    任务管理: 任务管理器 = Depends(获取任务管理器),
):
    try:
        return await 任务管理.创建任务(链接=请求.url, 保存名称=请求.name)
    except ValueError as 异常:
        raise HTTPException(status_code=400, detail=str(异常))


@router.get("/{task_id}", response_model=Task)
async def 获取任务详情(task_id: str, 任务管理: 任务管理器 = Depends(获取任务管理器)):
    try:
        return await 任务管理.获取任务(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="任务不存在")


@router.delete("/{task_id}")
async def 删除任务(task_id: str, 任务管理: 任务管理器 = Depends(获取任务管理器)):
    try:
        await 任务管理.删除任务(task_id)
        return {"success": True}
    except KeyError:
        raise HTTPException(status_code=404, detail="任务不存在")


@router.post("/{task_id}/start", response_model=Task)
async def 开始任务(task_id: str, 任务管理: 任务管理器 = Depends(获取任务管理器)):
    try:
        return await 任务管理.开始任务(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="任务不存在")


@router.post("/{task_id}/pause", response_model=Task)
async def 暂停任务(task_id: str, 任务管理: 任务管理器 = Depends(获取任务管理器)):
    try:
        return await 任务管理.暂停任务(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="任务不存在")


@router.get("/{task_id}/logs")
async def 获取任务日志(
    task_id: str,
    tail: int = Query(400, ge=0, le=2000),
    任务管理: 任务管理器 = Depends(获取任务管理器),
):
    try:
        await 任务管理.获取任务(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="任务不存在")
    return await 任务管理.获取任务日志(task_id, tail=tail)


@router.get("/{task_id}/logs/raw", response_class=PlainTextResponse)
async def 获取任务日志原文(
    task_id: str,
    任务管理: 任务管理器 = Depends(获取任务管理器),
):
    try:
        await 任务管理.获取任务(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="任务不存在")
    文本, 需截断 = await 任务管理.获取任务日志原文(task_id)
    return PlainTextResponse(文本, headers={"X-Log-Truncated": "1" if 需截断 else "0"})
