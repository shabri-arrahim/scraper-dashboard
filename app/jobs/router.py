from typing import Annotated, List
from fastapi import Depends, BackgroundTasks, Form
from fastapi.routing import APIRouter
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.jobs.schemas import JobResponse
from app.scripts.models import Script
from app.jobs.models import Job
from app.worker.tasks_scripts import run_script
from app.services import telegram
from app.core.celery_app import celery_app

router = APIRouter()


# ---------------------------- JOBS ----------------------------
@router.post("/start", response_model=JobResponse)
async def start_job(
    script_id: Annotated[str, Form()],
    background_task: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Start a new script job"""
    script = await Script.get_by_id(session=db, script_id=script_id)
    if not script:
        return HTTPException(status_code=404, detail="Script Not found")

    job = await Job.create(session=db, status="pending")
    await db.refresh(job)

    task = run_script.apply_async(
        args=[job.id, script.id],
        exchange="main",
        routing_key="main",
    )

    job.celery_task_id = task.id
    job.script_id = script.id
    job.status = "running"
    # TODO: Add handler delete script_file value if job failed to create
    script.log_file = f"{script.name}.log"
    await db.commit()
    await db.refresh(job)
    await db.refresh(script)

    background_task.add_task(
        telegram.send_message,
        f"🚀 Script <b>{script.name}</b> started",
        chat_id=settings.TELEGRAM_CHAT_ID,
    )

    return job


@router.post("/{job_id}/stop", response_model=JobResponse)
async def stop_script_job(job_id: int, db: AsyncSession = Depends(get_db)):
    """Stop a running script job"""
    job = await Job.get_by_id(session=db, job_id=job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != "running":
        raise HTTPException(status_code=400, detail="Job is not running")

    worker_id = job.celery_task_id
    celery_app.control.revoke(worker_id, terminate=True, signal="SIGUSR1")

    return job


@router.get("/", response_model=List[JobResponse])
async def list_script_jobs(db: AsyncSession = Depends(get_db)):
    """List all script jobs"""
    return await Job.get_all(session=db)


@router.get("/{job_id}", response_model=JobResponse)
async def get_script_job(job_id: int, db: AsyncSession = Depends(get_db)):
    """Get script job details"""
    job = await Job.get_by_id(session=db, job_id=job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/running", response_model=List[JobResponse])
async def list_running_scripts(db: AsyncSession = Depends(get_db)):
    """List all running scripts"""
    return await Job.get_running(session=db)


# --------------------------------------------------------------
