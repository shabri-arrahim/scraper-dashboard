from typing import List
from sqlalchemy import Column, Integer, String, DateTime, Text, select, ForeignKey
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.config import settings


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String)  # running, completed, failed, stopped
    script_id = Column(Integer, ForeignKey("scripts.id"), unique=True)
    celery_task_id = Column(String, unique=True, index=True)
    pid = Column(Integer, nullable=True)
    start_time = Column(DateTime, default=settings.TIME_NOW())
    end_time = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    script = relationship("Script", back_populates="job", uselist=False)

    @classmethod
    async def get_by_id(cls, session: AsyncSession, job_id: int) -> "Job":
        """Get job by ID"""
        stmt = select(cls).where(cls.id == job_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def get_all(cls, session: AsyncSession) -> List["Job"]:
        """Get all job"""
        stmt = select(cls).order_by(cls.start_time.desc())
        result = await session.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def get_running(cls, session: AsyncSession) -> "Job":
        """Get all running jobs"""
        stmt = select(cls).where(cls.status == "running")
        result = await session.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def create(cls, session: AsyncSession, status: str) -> "Job":
        """Create a new job"""
        new_job = cls(status=status)
        session.add(new_job)
        await session.commit()
        return new_job

    @classmethod
    async def update_status(
        cls, session: AsyncSession, job_id: int, status: str, error_message: str = None
    ):
        """Update job status"""
        job = await cls.get_by_id(session, job_id)
        if not job:
            raise ValueError(f"Job with ID {job_id} not found")
        job.status = status
        job.end_time = (
            settings.TIME_NOW()
            if status in ["completed", "failed", "stopped"]
            else None
        )
        job.error_message = error_message
        await session.commit()
        return job

    @classmethod
    async def update_process_id(
        cls, session: AsyncSession, job_id: int, process_id: int
    ):
        """Update job process ID"""
        job = await cls.get_by_id(session, job_id)
        if not job:
            raise ValueError(f"Job with ID {job_id} not found")
        job.pid = process_id
        await session.commit()
        await session.refresh(job)
        return job
