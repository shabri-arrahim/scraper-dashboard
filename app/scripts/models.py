from typing import List

from sqlalchemy import Column, Integer, String, select
from sqlalchemy.orm import relationship, selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base


class Script(Base):
    __tablename__ = "scripts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    log_file = Column(String, nullable=True)
    job = relationship("Job", back_populates="script", uselist=False)

    @classmethod
    async def get_by_id(cls, session: AsyncSession, script_id: int) -> "Script":
        """Get job by ID"""
        stmt = select(cls).where(cls.id == script_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def get_by_id_with_job(
        cls, session: AsyncSession, script_id: int
    ) -> "Script":
        """Get job by ID"""
        stmt = select(cls).where(cls.id == script_id).options(selectinload(cls.job))
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def get_all(cls, session: AsyncSession) -> List["Script"]:
        stmt = select(cls).order_by(cls.name)
        result = await session.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def get_all_with_jobs(cls, session: AsyncSession) -> List["Script"]:
        stmt = select(cls).options(selectinload(cls.job))
        result = await session.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def create(cls, session: AsyncSession, name: str) -> "Script":
        new_script = cls(name=name)
        session.add(new_script)
        await session.commit()
        return new_script
