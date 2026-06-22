import os
import logging
import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
LINE_NOTIFY_TOKEN = os.getenv("LINE_NOTIFY_TOKEN")

async def send_discord_alert(message: str, title: str = "Huay KVJ Alert", color: int = 15158332):
    """
    ส่งข้อความแจ้งเตือนผ่าน Discord Webhook
    """
    if not DISCORD_WEBHOOK_URL:
        logger.debug("Discord webhook URL is not configured. Skipping alert.")
        return False

    payload = {
        "embeds": [
            {
                "title": title,
                "description": message,
                "color": color, # default Red-ish
                "timestamp": None # Discord will default to now
            }
        ]
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
            if resp.status_code in (200, 204):
                logger.info("Discord alert sent successfully.")
                return True
            else:
                logger.error(f"Failed to send Discord alert: HTTP {resp.status_code} - {resp.text}")
    except Exception as e:
        logger.error(f"Error sending Discord alert: {e}")
    return False

async def send_line_alert(message: str):
    """
    ส่งข้อความแจ้งเตือนผ่าน LINE Notify
    """
    if not LINE_NOTIFY_TOKEN:
        logger.debug("LINE Notify token is not configured. Skipping alert.")
        return False

    url = "https://notify-api.line.me/api/notify"
    headers = {
        "Authorization": f"Bearer {LINE_NOTIFY_TOKEN}"
    }
    payload = {
        "message": message
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, data=payload, timeout=10)
            if resp.status_code == 200:
                logger.info("LINE alert sent successfully.")
                return True
            else:
                logger.error(f"Failed to send LINE alert: HTTP {resp.status_code} - {resp.text}")
    except Exception as e:
        logger.error(f"Error sending LINE alert: {e}")
    return False

async def send_alert(message: str, title: str = "Notification"):
    """
    ส่งแจ้งเตือนผ่านช่องทางที่มีการระบุตัวแปรใน .env (รันพร้อมกันทุกช่องทางที่กรอกข้อมูล)
    """
    discord_task = send_discord_alert(message, title)
    line_task = send_line_alert(f"\n[{title}]\n{message}")
    
    # รันคู่กันแบบไม่บล็อกกัน
    import asyncio
    await asyncio.gather(discord_task, line_task, return_exceptions=True)
