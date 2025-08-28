import datetime
import aiofiles
import aiofiles.os as async_os


from pathlib import Path
from fastapi.routing import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import HTTPException
from fastapi import UploadFile, File

from app.core.config import settings
from app.utils.async_tool import sync_to_async
from app.utils.filesystem import iter_glob

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def list_contents(request: Request):
    """Get downloadable content list"""
    downloadable_contents_path = settings.DOWNLOAD_DIR
    downloadable_contents = []

    if await async_os.path.exists(downloadable_contents_path):
        for ext in ("*.csv", "*.xlsx", "*.json"):
            async for content_file in iter_glob(downloadable_contents_path, ext):
                stat = await async_os.stat(content_file.path)
                downloadable_contents.append(
                    {
                        "name": content_file.name,
                        "path": content_file.path,
                        "size": stat.st_size,
                        "last_modified": datetime.datetime.fromtimestamp(
                            stat.st_mtime
                        ).strftime("%Y-%m-%d %H:%M:%S"),
                        "download_url": f"/download/{content_file.name}",
                    }
                )

    return templates.TemplateResponse(
        "components/content_list.html",
        {"request": request, "downloadable_contents": downloadable_contents},
    )


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Handle content file upload"""
    try:
        # Validate file extension
        allowed_extensions = {".csv", ".xlsx", ".json"}
        file_ext = Path(file.filename).suffix.lower()

        if file_ext not in allowed_extensions:
            return JSONResponse(
                status_code=400,
                content={
                    "error": f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
                },
            )

        # Save file to download directory
        file_path = settings.DOWNLOAD_DIR / file.filename
        async with aiofiles.open(file_path, "wb") as buffer:
            while chunk := await file.read(8192):
                await buffer.write(chunk)

        return {"success": True, "filename": file.filename}
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"error": f"Failed to upload file: {str(e)}"}
        )


@router.get("/download/{filename}")
async def download_file(filename: str):
    """Download a file from the download directory"""
    file_path = settings.DOWNLOAD_DIR / filename
    if not await async_os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path, filename=filename, media_type="application/octet-stream"
    )


@router.delete("/{filename}")
async def delete_content(filename: str):
    """Delete a content file"""
    try:
        file_path = settings.DOWNLOAD_DIR / filename
        if await async_os.path.exists(file_path):
            await async_os.unlink(file_path)
            return {"success": True}
        else:
            raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")
