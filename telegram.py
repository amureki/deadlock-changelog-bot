import os

import httpx

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")


def send_message_to_telegram(text):
    data = {"chat_id": TELEGRAM_CHANNEL_ID, "parse_mode": "HTML", "text": text}
    response = httpx.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", data=data
    )
    response.raise_for_status()
