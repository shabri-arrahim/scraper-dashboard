import os

import httpx


class TelegramService:
    def __init__(self, bot_token: str = None) -> None:
        self.bot_token = bot_token
        self.base_url = "https://api.telegram.org/bot"

        # Set default token
        if bot_token is None and os.environ.get("TELEGRAM_BOT_TOKEN"):
            self.bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")

    async def send_message(self, message: str, chat_id: str):
        try:
            async with httpx.AsyncClient() as client:
                payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
                resp = await client.post(
                    f"{self.base_url}{self.bot_token}/sendMessage", json=payload
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            print(f"Failed to send Telegram notification: {e}")
