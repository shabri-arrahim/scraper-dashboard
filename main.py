import os
import subprocess
import asyncio
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import shutil
import httpx
from fastapi import (
    FastAPI,
    Request,
    HTTPException,
    BackgroundTasks,
    UploadFile,
    File,
    Depends,
    Cookie,
)
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from middleware.auth import require_auth
from middleware.security import setup_middleware
from collections import deque

from config import config

app = FastAPI(title="Script Management Dashboard")
templates = Jinja2Templates(directory="templates")

# Set up security middleware
setup_middleware(app)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global storage for running processes and logs
running_processes: Dict[str, subprocess.Popen] = {}
script_logs: Dict[str, deque] = {}
script_status: Dict[str, str] = {}


class LogCapture:
    def __init__(self, script_name: str):
        self.script_name = script_name
        self.logs = deque(maxlen=config.MAX_LOG_LINES)
        script_logs[script_name] = self.logs

    def write(self, data: str):
        if data.strip():
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.logs.append(f"[{timestamp}] {data.strip()}")


async def send_telegram_notification(message: str):
    """Send notification to Telegram"""
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        return

    try:
        async with httpx.AsyncClient() as client:
            url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": config.TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "HTML",
            }
            await client.post(url, json=payload)
    except Exception as e:
        print(f"Failed to send Telegram notification: {e}")


def monitor_process(script_name: str, process: subprocess.Popen):
    """Monitor process completion and send notifications"""
    process.wait()

    if script_name in running_processes:
        del running_processes[script_name]

    if process.returncode == 0:
        script_status[script_name] = "completed"
        message = f"✅ Script <b>{script_name}</b> completed successfully"
    else:
        script_status[script_name] = "failed"
        message = (
            f"❌ Script <b>{script_name}</b> failed with exit code {process.returncode}"
        )

    # Create a new event loop for the async operation in this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        # Run the notification in the new event loop
        loop.run_until_complete(send_telegram_notification(message))
    finally:
        loop.close()

    # Reset status after 5 seconds
    threading.Timer(5.0, lambda: script_status.pop(script_name, None)).start()


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = None):
    """Login page"""
    return templates.TemplateResponse(
        "login.html", {"request": request, "error": error}
    )


@app.post("/login")
async def login(request: Request):
    """Handle login"""
    form = await request.form()
    token = form.get("token")

    if not token or token != config.API_TOKEN:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid token"},
            status_code=401,
        )

    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(
        key="auth_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=86400,  # 24 hours
    )
    return response


@app.get("/", response_class=HTMLResponse)
@require_auth
async def dashboard(request: Request):
    """Main dashboard page"""
    scripts_path = Path(config.SCRIPTS_DIR)
    scripts = []

    if scripts_path.exists():
        for script_file in scripts_path.glob("*.py"):
            status = get_script_status(script_file.name)
            scripts.append(
                {
                    "name": script_file.name,
                    "status": status,
                    "has_logs": script_file.name in script_logs,
                }
            )

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "scripts": scripts,
            "telegram_configured": bool(
                config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID
            ),
        },
    )


@app.get("/scripts", response_class=HTMLResponse)
async def get_scripts(request: Request):
    """Get updated script list"""
    scripts_path = Path(config.SCRIPTS_DIR)
    scripts = []

    if scripts_path.exists():
        for script_file in scripts_path.glob("*.py"):
            status = get_script_status(script_file.name)
            scripts.append(
                {
                    "name": script_file.name,
                    "status": status,
                    "has_logs": script_file.name in script_logs,
                }
            )

    return templates.TemplateResponse(
        "components/script_list.html", {"request": request, "scripts": scripts}
    )


@app.post("/scripts/upload")
async def upload_script(file: UploadFile = File(...)):
    """Handle script upload"""
    try:
        # Validate file extension
        if not file.filename.endswith(".py"):
            return JSONResponse(
                status_code=400,
                content={"error": "Only Python (.py) files are allowed"},
            )

        # Save file to scripts directory
        file_path = Path(config.SCRIPTS_DIR) / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return {"success": True, "filename": file.filename}
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"error": f"Failed to upload script: {str(e)}"}
        )


@app.delete("/scripts/{script_name}")
async def delete_script(script_name: str):
    """Delete a script"""
    try:
        # Check if script is running
        if script_name in running_processes:
            return JSONResponse(
                status_code=400,
                content={"error": "Cannot delete script while it's running"},
            )

        script_path = Path(config.SCRIPTS_DIR) / script_name
        if script_path.exists():
            script_path.unlink()

            # Clean up any logs
            if script_name in script_logs:
                del script_logs[script_name]
            if script_name in script_status:
                del script_status[script_name]

            return {"success": True}
        else:
            return JSONResponse(status_code=404, content={"error": "Script not found"})
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"error": f"Failed to delete script: {str(e)}"}
        )


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Handle file upload"""
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
        file_path = Path(config.DOWNLOAD_DIR) / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return {"success": True, "filename": file.filename}
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"error": f"Failed to upload file: {str(e)}"}
        )


@app.get("/assets", response_class=HTMLResponse)
async def get_assets(request: Request):
    """Get script assets list"""
    assets_path = Path(config.SCRIPTS_ASSETS_DIR)
    assets = []

    if assets_path.exists():
        # Add directories first
        for item in assets_path.iterdir():
            if item.is_dir():
                assets.append(
                    {
                        "name": item.name,
                        "type": "folder",
                        "last_modified": datetime.fromtimestamp(
                            item.stat().st_mtime
                        ).strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )

        # Then add files
        for item in assets_path.iterdir():
            if item.is_file():
                size = item.stat().st_size
                # Format size
                if size < 1024:
                    size_formatted = f"{size} B"
                elif size < 1024 * 1024:
                    size_formatted = f"{size/1024:.1f} KB"
                else:
                    size_formatted = f"{size/(1024*1024):.1f} MB"

                assets.append(
                    {
                        "name": item.name,
                        "type": "file",
                        "size": size,
                        "size_formatted": size_formatted,
                        "last_modified": datetime.fromtimestamp(
                            item.stat().st_mtime
                        ).strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )

    return templates.TemplateResponse(
        "components/assets_list.html", {"request": request, "assets": assets}
    )


@app.post("/assets/upload")
async def upload_asset(file: UploadFile = File(...)):
    """Handle asset upload"""
    try:
        file_path = Path(config.SCRIPTS_ASSETS_DIR) / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"success": True, "filename": file.filename}
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"error": f"Failed to upload asset: {str(e)}"}
        )


@app.delete("/assets/{asset_name}")
async def delete_asset(asset_name: str):
    """Delete an asset"""
    try:
        asset_path = Path(config.SCRIPTS_ASSETS_DIR) / asset_name
        if asset_path.is_file():
            asset_path.unlink()
        elif asset_path.is_dir():
            shutil.rmtree(asset_path)
        return {"success": True}
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"error": f"Failed to delete asset: {str(e)}"}
        )


@app.get("/downloads", response_class=HTMLResponse)
async def get_contents_to_download(request: Request):
    """Get downloadable content list"""
    downloadable_contents_path = Path(config.DOWNLOAD_DIR)
    downloadable_contents = []

    if downloadable_contents_path.exists():
        for ext in ("*.csv", "*.xlsx", "*.json"):
            for content_file in downloadable_contents_path.glob(ext):
                downloadable_contents.append(
                    {
                        "name": content_file.name,
                        "path": content_file,
                        "size": content_file.stat().st_size,
                        "last_modified": datetime.fromtimestamp(
                            content_file.stat().st_mtime
                        ).strftime("%Y-%m-%d %H:%M:%S"),
                        "download_url": f"/download/{content_file.name}",
                    }
                )

    return templates.TemplateResponse(
        "components/download_list.html",
        {"request": request, "downloadable_contents": downloadable_contents},
    )


def get_script_status(script_name: str) -> str:
    """Get current status of a script"""
    if script_name in script_status:
        return script_status[script_name]
    if script_name in running_processes:
        return "running"
    return "stopped"


@app.post("/scripts/{script_name}/start")
async def start_script(script_name: str, background_tasks: BackgroundTasks):
    """Start a Python script"""
    if script_name in running_processes:
        raise HTTPException(status_code=400, detail="Script is already running")

    script_path = Path(config.SCRIPTS_DIR) / script_name
    if not script_path.exists():
        raise HTTPException(status_code=404, detail="Script not found")

    try:
        # Initialize log capture
        log_capture = LogCapture(script_name)

        # Start the process
        process = subprocess.Popen(
            ["python", str(script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
        )

        running_processes[script_name] = process

        # Start log capture in background
        def capture_output():
            for line in process.stdout:
                log_capture.write(line)

        threading.Thread(target=capture_output, daemon=True).start()

        # Monitor process completion
        threading.Thread(
            target=monitor_process, args=(script_name, process), daemon=True
        ).start()

        # Send start notification
        background_tasks.add_task(
            send_telegram_notification, f"🚀 Script <b>{script_name}</b> started"
        )

        return {"status": "started", "pid": process.pid}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start script: {str(e)}")


@app.post("/scripts/{script_name}/stop")
async def stop_script(script_name: str, background_tasks: BackgroundTasks):
    """Stop a running script"""
    if script_name not in running_processes:
        raise HTTPException(status_code=400, detail="Script is not running")

    try:
        process = running_processes[script_name]

        # Terminate process gracefully
        process.terminate()

        # Wait for termination, then force kill if needed
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

        del running_processes[script_name]
        script_status[script_name] = "stopped"

        # Send stop notification
        background_tasks.add_task(
            send_telegram_notification, f"⏹️ Script <b>{script_name}</b> stopped"
        )

        return {"status": "stopped"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop script: {str(e)}")


@app.get("/scripts/{script_name}/logs")
async def get_logs(script_name: str):
    """Get logs for a script"""
    if script_name not in script_logs:
        return {"logs": [], "status": get_script_status(script_name)}

    logs = list(script_logs[script_name])
    return {"logs": logs, "status": get_script_status(script_name)}


@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download a file from the download directory"""
    file_path = Path(config.DOWNLOAD_DIR) / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path, filename=filename, media_type="application/octet-stream"
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=config.DEBUG)
