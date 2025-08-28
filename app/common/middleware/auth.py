import secrets
import hashlib

from functools import wraps
from fastapi import Request
from fastapi.responses import RedirectResponse

from app.core.config import settings


def verify_token(token: str) -> bool:
    """Verify if the token is valid"""
    if not token or not settings.API_TOKEN:
        return False
    # Compare tokens in a secure way using secrets
    return secrets.compare_digest(
        hashlib.sha256(token.encode()).hexdigest(),
        hashlib.sha256(settings.API_TOKEN.encode()).hexdigest(),
    )


def require_auth(func):
    """Decorator to require authentication for routes"""

    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        # Skip auth for login page and static files
        if request.url.path in ["/login", "/static"] or request.url.path.startswith(
            "/static/"
        ):
            return await func(request, *args, **kwargs)

        # Check for token in cookie
        token = request.cookies.get("auth_token")

        if not verify_token(token):
            return RedirectResponse(url="/login", status_code=302)

        return await func(request, *args, **kwargs)

    return wrapper
