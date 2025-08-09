import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    ENVIRONMENT = os.getenv("ENVIRONMENT", "local").lower()
    # Security Settings
    API_TOKEN = os.getenv("API_TOKEN", "")
    ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
    RATE_LIMIT = int(os.getenv("RATE_LIMIT", "100"))  # Requests per minute

    # Ensure HOME_DIR is set to the user's home directory
    HOME_DIR = os.path.expanduser("~")
    SOURCES_DIR = os.path.join(HOME_DIR, ".scraper_dash")
    DOWNLOAD_DIR = os.path.join(SOURCES_DIR, "downloads")
    SCRIPTS_DIR = os.path.join(SOURCES_DIR, "scripts")
    SCRIPTS_ASSETS_DIR = os.path.join(SOURCES_DIR, "static", "scripts")

    # Security Headers
    SECURITY_HEADERS = {
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": (
            "default-src 'self' cdn.tailwindcss.com unpkg.com cdnjs.cloudflare.com;"
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' cdn.tailwindcss.com unpkg.com;"
            "style-src 'self' 'unsafe-inline' cdnjs.cloudflare.com;"
            "font-src 'self' cdnjs.cloudflare.com;"
            "img-src 'self' data:;"
        ),
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }

    # Application Settings
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
    SCRIPTS_DIR = os.getenv("SCRIPTS_DIR", "scripts")
    MAX_LOG_LINES = int(os.getenv("MAX_LOG_LINES", "1000"))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    def __init__(self):
        for path in [
            self.SOURCES_DIR,
            self.SCRIPTS_DIR,
            self.DOWNLOAD_DIR,
            self.SCRIPTS_ASSETS_DIR,
        ]:
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)


config = Config()
