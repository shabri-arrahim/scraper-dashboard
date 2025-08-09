import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Security Settings
    API_TOKEN = os.getenv("API_TOKEN", "")
    ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
    RATE_LIMIT = int(os.getenv("RATE_LIMIT", "100"))  # Requests per minute

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
        # Ensure the scripts directory exists
        scripts_dir = os.path.join(os.path.expanduser("~"), self.SCRIPTS_DIR)
        if not os.path.exists(scripts_dir):
            os.makedirs(scripts_dir)

        # check if the download directory exists in user's home directory
        downloads_path = os.path.join(os.path.dirname(__file__), "downloads")
        if not os.path.exists(downloads_path):
            # create the directory if it does not exist
            os.makedirs(downloads_path)

        scripts_assets_path = os.path.join(
            os.path.dirname(__file__), "scripts", "dependencies"
        )
        if not os.path.exists(scripts_assets_path):
            # create the scripts assets directory if it does not exist
            os.makedirs(scripts_assets_path, exist_ok=True)

        # Create static directory for assets
        static_path = os.path.join(os.path.dirname(__file__), "static")
        if not os.path.exists(static_path):
            os.makedirs(static_path, exist_ok=True)

        self.SCRIPTS_DIR = scripts_dir
        self.DOWNLOAD_DIR = downloads_path
        self.SCRIPTS_ASSETS_DIR = scripts_assets_path


config = Config()
