import os
import uuid
import shutil
import aiofiles
import datetime
import aiofiles.os as async_os

from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from fastapi import (
    APIRouter,
    Depends,
    File,
    UploadFile,
)
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.exceptions import HTTPException
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates

from app.core.database import get_db
from app.core.config import settings
from app.scripts.schemas import ScriptResponse
from app.scripts.models import Script
from app.jobs.models import Job
from app.common.log_handler import LogFileReader
from app.utils.async_tool import sync_to_async

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# ---------------------------- SCRIPTS ----------------------------
# TODO: move all of the bussiness logic to service.py
@router.get("", response_model=List[ScriptResponse])
async def list_scripts(request: Request, db: AsyncSession = Depends(get_db)):
    """List all scripts"""
    scripts = await Script.get_all_with_jobs(session=db)

    if not scripts:
        return templates.TemplateResponse(
            "components/script_list.html", {"request": request, "scripts": []}
        )

    scripts = [
        {
            "id": sc.id,
            "name": sc.name,
            "status": sc.job.status if sc.job else "stopped",
            "has_logs": bool(sc.log_file is not None),
            "job_id": sc.job.id if sc.job else None,
        }
        for sc in scripts
    ]

    return templates.TemplateResponse(
        "components/script_list.html", {"request": request, "scripts": scripts}
    )


@router.post("/upload")
async def upload_script(
    file: UploadFile = File(...), db: AsyncSession = Depends(get_db)
):
    """Handle script upload"""
    try:
        # Validate file extension
        if not file.filename.endswith(".py"):
            return HTTPException(
                status_code=400,
                detail="Only Python (.py) files are allowed",
            )

        new_filename = f"{uuid.uuid4().hex[:5]}_{file.filename}"

        # Save file to scripts directory
        file_path = settings.SCRIPTS_DIR / new_filename
        async with aiofiles.open(file_path, "wb") as buffer:
            while chunk := await file.read(8192):
                await buffer.write(chunk)

        script = await Script.create(session=db, name=os.path.splitext(new_filename)[0])

        return {"success": True, "filename": script.name}
    except Exception as e:
        return HTTPException(
            status_code=500, detail=f"Failed to upload script: {str(e)}"
        )


@router.delete("/{script_id}")
async def delete_script(script_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a script"""
    try:
        # NOTE: Currentely the script name probably used more than one
        # Soo every scripts jobs and logs records will be deleted if has a same name,
        # athought it from different process
        script = await Script.get_by_id(session=db, script_id=script_id)
        if not script:
            HTTPException(
                status_code=404,
                detail=f"Can't delete script with ID {script_id}, script are not found",
            )

        script_path = settings.SCRIPTS_DIR / f"{script.name}.py"

        stmt = select(Job).where(Job.script_id == script_id)
        result = await db.execute(stmt)
        job = result.scalar_one_or_none()

        if job:
            if job.status == "running":
                return HTTPException(
                    status_code=400,
                    detail="Cannot delete script while it's running",
                )

            stmt = delete(Job).where(Job.id == job.id)
            await db.execute(stmt)
            await db.commit()

        log_handler = LogFileReader(script.name)
        await sync_to_async(log_handler.delete_log_file)()

        if await async_os.path.exists(script_path):
            await async_os.unlink(script_path)
        else:
            return HTTPException(status_code=404, detail="Script not found")

        stmt = delete(Script).where(Script.id == script.id)
        await db.execute(stmt)
        await db.commit()

        return {"success": True}
    except Exception as e:
        return HTTPException(
            status_code=500, detail=f"Failed to delete script: {str(e)}"
        )


@router.get("/{script_id}/logs")
async def get_script_log(script_id: int, db: AsyncSession = Depends(get_db)):
    try:
        script = await Script.get_by_id_with_job(session=db, script_id=script_id)
        log_handler = LogFileReader(script_name=script.name)

        if not log_handler.log_file.exists():
            return HTTPException(status_code=404, detail="can't find log")

        log_tail = await sync_to_async(log_handler.tail_log_file)()
        script_status = script.job.status if script.job else "stoped"
        return {"logs": log_tail, "status": script_status}
    except Exception as e:
        return HTTPException(
            status_code=500, detail=f"Failed to get script log: {str(e)}"
        )


# -----------------------------------------------------------------


# ---------------------------- ASSESTS ----------------------------
@router.get("/assets", response_class=HTMLResponse)
async def get_assets(request: Request):
    """Get script assets list"""
    assets_path = settings.SCRIPTS_ASSETS_DIR
    assets = []

    if await async_os.path.exists(assets_path):
        for entry in await async_os.scandir(assets_path):
            if await async_os.path.isdir(entry.path):
                stat = await async_os.stat(entry.path)
                assets.append(
                    {
                        "name": entry.name,
                        "type": "folder",
                        "last_modified": datetime.datetime.fromtimestamp(
                            stat.st_mtime
                        ).strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )

        for entry in await async_os.scandir(assets_path):
            if await async_os.path.isfile(entry):
                stat = await async_os.stat(entry.path)
                size = stat.st_size
                # Format size
                if size < 1024:
                    size_formatted = f"{size} B"
                elif size < 1024 * 1024:
                    size_formatted = f"{size/1024:.1f} KB"
                else:
                    size_formatted = f"{size/(1024*1024):.1f} MB"

                assets.append(
                    {
                        "name": entry.name,
                        "type": "file",
                        "size": size,
                        "size_formatted": size_formatted,
                        "last_modified": datetime.datetime.fromtimestamp(
                            stat.st_mtime
                        ).strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )

    return templates.TemplateResponse(
        "components/assets_list.html", {"request": request, "assets": assets}
    )


@router.post("/assets/upload")
async def upload_asset(file: UploadFile = File(...)):
    """Handle asset upload"""
    try:
        file_path = settings.SCRIPTS_ASSETS_DIR / file.filename
        async with aiofiles.open(file_path, "wb") as buffer:
            while chunk := await file.read(8192):
                await buffer.write(chunk)
        return {"success": True, "filename": file.filename}
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"error": f"Failed to upload asset: {str(e)}"}
        )


@router.delete("/assets/{asset_name}")
async def delete_asset(asset_name: str):
    """Delete an asset"""
    try:
        asset_path = settings.SCRIPTS_ASSETS_DIR / asset_name
        if await async_os.path.isfile(asset_path):
            await async_os.unlink(asset_path)
        elif await async_os.path.isdir(asset_path):
            await sync_to_async(shutil.rmtree)(asset_path)
        return {"success": True}
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"error": f"Failed to delete asset: {str(e)}"}
        )


# -----------------------------------------------------------------
