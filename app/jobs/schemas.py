from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class JobBase(BaseModel):
    status: str


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    status: str
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None


class JobResponse(JobBase):
    id: int
    celery_task_id: str
    pid: Optional[int]
    start_time: datetime
    end_time: Optional[datetime]
    error_message: Optional[str]

    class Config:
        from_attributes = True
