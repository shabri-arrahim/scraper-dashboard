import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
    SCRIPTS_DIR = os.getenv("SCRIPTS_DIR", "scripts")
    MAX_LOG_LINES = int(os.getenv("MAX_LOG_LINES", "1000"))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    def __init__(self):
        # check if the download directory exists in user's home directory
        downloads_path = os.path.join(os.path.expanduser("~"), "downloads")
        if not os.path.exists(downloads_path):
            # create the directory if it does not exist
            os.makedirs(downloads_path)

        scripts_assets_path = os.path.join(os.path.expanduser("~"), "static", "scripts")
        if not os.path.exists(scripts_assets_path):
            # create the scripts assets directory if it does not exist
            os.makedirs(scripts_assets_path)

        self.DOWNLOAD_DIR = downloads_path
        self.SCRIPTS_ASSETS_DIR = scripts_assets_path


config = Config()
