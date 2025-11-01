"""Task management API endpoints."""

from typing import List

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.deps import get_db
from ...core.worker import worker
from ...services.projects import ProjectService

router = APIRouter()


@router.get(
    "/tasks/{task_id}",
    tags=["tasks"],
)
async def get_task_status(
    task_id: str,

) -> dict:
    """Get task status.

    Args:
        task_id: Task ID


    Returns:
        Task status information

    Raises:
        HTTPException: If task not found
    """
    # Get task result from worker
    task = AsyncResult(task_id, app=worker.app)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Return task status
    # Handle different task states
    response = {
        "task_id": task.id,
        "status": task.status,
    }

    if task.failed():
        # Extract error message from exception
        error_msg = str(task.result)
        # If it's an exception object, get the message
        if hasattr(task.result, 'args') and task.result.args:
            error_msg = str(task.result.args[0])
        response["error"] = error_msg
        response["result"] = None
    elif task.ready():
        # Task completed successfully
        response["result"] = task.result
        response["error"] = None
    else:
        # Task is pending or running
        response["result"] = None
        response["error"] = None

    return response


@router.get(
    "/projects/{project_id}/tasks",
    tags=["tasks"],
)
async def list_project_tasks(
    *,
    project_id: int,
    db: AsyncSession = Depends(get_db),

) -> List[dict]:
    """List active tasks for a project.

    Args:
        project_id: Project ID
        db: Database session


    Returns:
        List of task information

    Raises:
        HTTPException: If project not found
    """
    # Verify project exists
    service = ProjectService(db)
    project = await service.get(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Get active tasks from Worker Celery
    # Note: This is a simplified implementation
    # In a production system, you would typically:
    # 1. Store task IDs in the database with project association
    # 2. Query the database for task IDs
    # 3. Look up task status from Celery
    i = worker.app.control.inspect()
    active_tasks = []

    # Get active tasks
    if i.active():
        for tasks in i.active().values():
            for task in tasks:
                if task.get("kwargs", {}).get("project_id") == project_id:
                    task_result = AsyncResult(task["id"], app=worker.app)
                    active_tasks.append({
                        "task_id": task["id"],
                        "name": task["name"],
                        "status": task_result.status,
                        "started_at": task["time_start"],
                    })

    return active_tasks


@router.patch(
    "/tasks/{task_id}/cancel",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["tasks"],
)
async def cancel_task(
    task_id: str,

) -> None:
    """Cancel a running task.

    Args:
        task_id: Task ID


    Raises:
        HTTPException: If task not found or cannot be canceled
    """
    # Get task from worker
    task = AsyncResult(task_id, app=worker.app)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Check if task can be canceled
    if task.ready():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task already completed",
        )

    # Revoke task
    task.revoke(terminate=True)
