from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.middleware.auth import require_auth
from app.common.middleware.security import setup_middleware
from app.core.database import get_db
from app.core.config import settings
from app.scripts import router as scripts_router
from app.contents import router as contents_router
from app.jobs import router as jobs_router
from app.scripts.models import Script

app = FastAPI(title="Script Management Dashboard")

app.include_router(scripts_router.router, prefix="/scripts", tags=["scripts"])
app.include_router(contents_router.router, prefix="/contents", tags=["contents"])
app.include_router(jobs_router.router, prefix="/jobs", tags=["jobs"])

templates = Jinja2Templates(directory="templates")

# Set up security middleware
setup_middleware(app)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


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

    if not token or token != settings.API_TOKEN:
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
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    """Main dashboard page"""
    # scripts = await Script.get_all(session=db)

    # if not scripts:
    #     return templates.TemplateResponse(
    #         "components/script_list.html", {"request": request, "scripts": []}
    #     )

    # scripts = [
    #     {
    #         "id": sc.id,
    #         "name": sc.name,
    #         "status": sc.job.status if sc.job else "stopped",
    #         "has_logs": bool(sc.log_file and sc.job),
    #         "job_id": sc.job.id if sc.job else None,
    #     }
    #     for sc in scripts
    # ]

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "scripts": [],
            "telegram_configured": bool(
                settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID
            ),
        },
    )


if __name__ == "__main__":
    import uvicorn

    try:
        environment = settings.ENVIRONMENT
        if environment == "local":
            uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
        else:
            # Production settings
            uvicorn.run(
                "main:app",
                host="0.0.0.0",  # Always bind to 0.0.0.0 in container
                port=80,
                workers=4,
                reload=False,
                access_log=True,
                log_level="info",
            )
    except Exception as e:
        print(f"Failed to start application: {e}")
        raise
